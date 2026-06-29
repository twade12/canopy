"""A minimal UDS (ISO 14229) server — a virtual ECU's diagnostic personality.

udsoncan is a *client* library; the simulator needs the *server* side so a module under
test (or a tech's external scan tool) can query a simulated peer and get correct answers.
This implements just enough of the common services over ISO-TP to be convincing:

    0x10 DiagnosticSessionControl   0x22 ReadDataByIdentifier
    0x3E TesterPresent              0x19 ReadDTCInformation (reportDTCByStatusMask)
    0x14 ClearDiagnosticInformation

Unknown services get a proper negative response (NRC 0x11). Multi-frame responses (e.g. a
17-byte VIN) exercise real ISO-TP segmentation + flow control. See BATTLE-PLAN Track B2.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

import isotp

from canopy.config import CanConfig
from canopy.hal.can_iface import CanInterface

# Negative Response Codes
NRC_SERVICE_NOT_SUPPORTED = 0x11
NRC_SUBFUNCTION_NOT_SUPPORTED = 0x12
NRC_REQUEST_OUT_OF_RANGE = 0x31

VIN_DID = 0xF190


@dataclass
class UdsServerConfig:
    """What a virtual ECU knows how to answer.

    Attributes:
        vin: Vehicle Identification Number served at DID 0xF190 (17 chars).
        did_map: Extra ReadDataByIdentifier responses, ``{did: raw_bytes}``.
        dtcs: Stored DTCs as ``(dtc_id_3_bytes, status_byte)`` tuples.
        dtc_availability_mask: Reported DTCStatusAvailabilityMask.
    """

    vin: str | None = None
    did_map: dict[int, bytes] = field(default_factory=dict)
    dtcs: list[tuple[int, int]] = field(default_factory=list)
    dtc_availability_mask: int = 0xFF

    def resolve_did(self, did: int) -> bytes | None:
        if did == VIN_DID and self.vin is not None:
            return self.vin.encode("ascii")
        return self.did_map.get(did)


class UdsServer:
    """Serves UDS requests for one ECU on its own CAN interface."""

    def __init__(
        self,
        channel: CanConfig,
        *,
        request_id: int,
        response_id: int,
        config: UdsServerConfig,
    ):
        self._channel = channel
        self.request_id = request_id
        self.response_id = response_id
        self.config = config
        self._iface: CanInterface | None = None
        self._stack: isotp.CanStack | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        self._iface = CanInterface(self._channel)
        address = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=self.response_id,
            rxid=self.request_id,
        )
        self._stack = isotp.CanStack(bus=self._iface.bus, address=address)
        self._stack.start()
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        assert self._stack is not None
        while not self._stop.is_set():
            try:
                request = self._stack.recv(block=True, timeout=0.2)
            except Exception:
                continue
            if not request:
                continue
            response = self._handle(bytes(request))
            if response:
                self._stack.send(response)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._stack is not None:
            self._stack.stop()
            self._stack = None
        if self._iface is not None:
            self._iface.shutdown()
            self._iface = None

    # --- request handling ------------------------------------------------------
    def _handle(self, req: bytes) -> bytes | None:
        if not req:
            return None
        sid = req[0]
        handler = {
            0x10: self._session_control,
            0x3E: self._tester_present,
            0x22: self._read_data_by_identifier,
            0x19: self._read_dtc_information,
            0x14: self._clear_diagnostic_information,
            0x27: self._security_access,
            0x2E: self._write_data_by_identifier,
            0x2F: self._io_control,
            0x31: self._routine_control,
        }.get(sid)
        if handler is None:
            return bytes([0x7F, sid, NRC_SERVICE_NOT_SUPPORTED])
        return handler(req)

    # --- actuation services (a convincing target for control commands) ---------
    def _security_access(self, req: bytes) -> bytes:
        if len(req) < 2:
            return bytes([0x7F, 0x27, NRC_SUBFUNCTION_NOT_SUPPORTED])
        sub = req[1]
        if sub % 2 == 1:  # requestSeed (odd)
            self._seed = bytes([0x11, 0x22, 0x33, 0x44])
            return bytes([0x67, sub, *self._seed])
        # sendKey (even): the demo algorithm is a byte-wise NOT of the seed
        expected = bytes((b ^ 0xFF) & 0xFF for b in getattr(self, "_seed", b""))
        if bytes(req[2:]) == expected:
            self._unlocked = True
            return bytes([0x67, sub])
        return bytes([0x7F, 0x27, 0x35])  # invalidKey

    def _write_data_by_identifier(self, req: bytes) -> bytes:
        if len(req) < 3:
            return bytes([0x7F, 0x2E, NRC_REQUEST_OUT_OF_RANGE])
        did = (req[1] << 8) | req[2]
        self.config.did_map[did] = bytes(req[3:])  # stored; readable back via 0x22
        return bytes([0x6E, req[1], req[2]])

    def _io_control(self, req: bytes) -> bytes:
        if len(req) < 4:
            return bytes([0x7F, 0x2F, NRC_REQUEST_OUT_OF_RANGE])
        # positive response echoes DID + control parameter + (controlState) data
        return bytes([0x6F, *req[1:]])

    def _routine_control(self, req: bytes) -> bytes:
        if len(req) < 4:
            return bytes([0x7F, 0x31, NRC_REQUEST_OUT_OF_RANGE])
        # echo routineControlType + routineId (+ optional routineStatusRecord)
        return bytes([0x71, *req[1:]])

    @staticmethod
    def _suppress(subfunction: int) -> bool:
        return bool(subfunction & 0x80)

    def _session_control(self, req: bytes) -> bytes | None:
        if len(req) < 2:
            return bytes([0x7F, 0x10, NRC_SUBFUNCTION_NOT_SUPPORTED])
        session = req[1] & 0x7F
        if self._suppress(req[1]):
            return None
        # Echo session + default P2 / P2* timing (0x0032, 0x01F4).
        return bytes([0x50, session, 0x00, 0x32, 0x01, 0xF4])

    def _tester_present(self, req: bytes) -> bytes | None:
        subfn = req[1] if len(req) > 1 else 0x00
        if self._suppress(subfn):
            return None
        return bytes([0x7E, subfn & 0x7F])

    def _read_data_by_identifier(self, req: bytes) -> bytes:
        if len(req) < 3:
            return bytes([0x7F, 0x22, NRC_REQUEST_OUT_OF_RANGE])
        did = (req[1] << 8) | req[2]
        data = self.config.resolve_did(did)
        if data is None:
            return bytes([0x7F, 0x22, NRC_REQUEST_OUT_OF_RANGE])
        return bytes([0x62, req[1], req[2]]) + data

    def _read_dtc_information(self, req: bytes) -> bytes:
        # Only reportDTCByStatusMask (0x02) is implemented.
        if len(req) < 3 or req[1] != 0x02:
            return bytes([0x7F, 0x19, NRC_SUBFUNCTION_NOT_SUPPORTED])
        status_mask = req[2]
        out = bytearray([0x59, 0x02, self.config.dtc_availability_mask])
        for dtc_id, status in self.config.dtcs:
            if status & status_mask:
                out += bytes([(dtc_id >> 16) & 0xFF, (dtc_id >> 8) & 0xFF, dtc_id & 0xFF, status])
        return bytes(out)

    def _clear_diagnostic_information(self, req: bytes) -> bytes:
        if len(req) < 4:
            return bytes([0x7F, 0x14, NRC_REQUEST_OUT_OF_RANGE])
        self.config.dtcs.clear()
        return bytes([0x54])
