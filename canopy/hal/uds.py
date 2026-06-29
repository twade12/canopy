"""UDS (ISO 14229) client — the station acting as the diagnostic tester.

Wraps :mod:`udsoncan` over an ISO-TP/python-can stack and exposes the handful of services
the runner needs (CLAUDE.md §7.2). The connection owns the stack lifecycle, so the client
is a context manager: open it, talk, close it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType

import udsoncan
from udsoncan.client import Client
from udsoncan.configs import default_client_config
from udsoncan.connections import PythonIsoTpConnection

from canopy.config import CanConfig
from canopy.hal import commands as _cmd
from canopy.hal.can_iface import CanInterface
from canopy.hal.isotp import DEFAULT_TESTER_REQUEST_ID, DEFAULT_TESTER_RESPONSE_ID, make_can_stack

VIN_DID = 0xF190


@dataclass
class DiagnosticTroubleCode:
    """A decoded DTC."""

    code: int
    status: int

    @property
    def code_hex(self) -> str:
        return f"0x{self.code:06X}"


@dataclass
class UdsClient:
    """Tester-side UDS client bound to one CAN channel and ECU address.

    Args:
        channel: CAN connection settings.
        request_id / response_id: 11-bit diagnostic addressing (tester→ECU / ECU→tester).
        data_identifiers: Optional DID→codec map (VIN is pre-registered).
    """

    channel: CanConfig = field(default_factory=CanConfig.from_env)
    request_id: int = DEFAULT_TESTER_REQUEST_ID
    response_id: int = DEFAULT_TESTER_RESPONSE_ID
    data_identifiers: dict[int, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._iface: CanInterface | None = None
        self._client: Client | None = None
        self._conn = None

    def open(self) -> UdsClient:
        self._iface = CanInterface(self.channel)
        stack = make_can_stack(self._iface.bus, self.request_id, self.response_id)
        conn = PythonIsoTpConnection(stack)
        self._conn = conn
        config = dict(default_client_config)
        config["data_identifiers"] = {VIN_DID: udsoncan.AsciiCodec(17), **self.data_identifiers}
        self._client = Client(conn, config=config)
        self._client.open()
        return self

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        self._conn = None
        if self._iface is not None:
            self._iface.shutdown()
            self._iface = None

    @property
    def client(self) -> Client:
        if self._client is None:
            raise RuntimeError("UdsClient is not open(); use it as a context manager")
        return self._client

    # --- services --------------------------------------------------------------
    def change_session(self, session: int = 1) -> None:
        self.client.change_session(session)

    def tester_present(self) -> None:
        self.client.tester_present()

    def read_data_by_identifier(self, did: int):
        return self.client.read_data_by_identifier(did).service_data.values[did]

    def read_vin(self) -> str:
        return self.read_data_by_identifier(VIN_DID)

    def read_dtcs(self, status_mask: int = 0xFF) -> list[DiagnosticTroubleCode]:
        response = self.client.get_dtc_by_status_mask(status_mask)
        out: list[DiagnosticTroubleCode] = []
        for dtc in response.service_data.dtcs:
            status = dtc.status
            if hasattr(status, "get_byte_as_int"):
                status = status.get_byte_as_int()
            out.append(DiagnosticTroubleCode(code=dtc.id, status=int(status)))
        return out

    def clear_dtcs(self, group: int = 0xFFFFFF) -> None:
        self.client.clear_dtc(group)

    # --- raw + actuation services (control the module, not just read it) -------
    def request(self, payload: bytes, timeout: float = 2.0) -> bytes:
        """Send raw UDS service bytes over ISO-TP and return the raw response.

        This is the generic path for replaying captured/reverse-engineered commands and
        OEM-specific DIDs that don't fit udsoncan's codec model. Returns b"" on timeout.
        """
        if self._conn is None:
            raise RuntimeError("UdsClient is not open(); use it as a context manager")
        self._conn.empty_rxqueue()
        self._conn.send(payload)
        try:
            resp = self._conn.wait_frame(timeout=timeout, exception=False)
        except TypeError:  # older udsoncan: no exception kwarg
            resp = self._conn.wait_frame(timeout=timeout)
        except Exception:  # treat a raised timeout as "no response"
            resp = None
        return bytes(resp) if resp else b""

    def io_control(self, did: int, control: str | int = "short_term_adjust",
                   data: bytes = b"", timeout: float = 2.0) -> _cmd.UdsResult:
        """InputOutputControlByIdentifier (0x2F) — force an actuator (e.g. A/C clutch ON)."""
        req = _cmd.build_io_control(did, control, data)
        return _cmd.parse_uds_response(req, self.request(req, timeout))

    def routine_control(self, routine_id: int, control: str | int = "start",
                        data: bytes = b"", timeout: float = 2.0) -> _cmd.UdsResult:
        """RoutineControl (0x31) — run a built-in actuator test / self-test."""
        req = _cmd.build_routine(routine_id, control, data)
        return _cmd.parse_uds_response(req, self.request(req, timeout))

    def write_did(self, did: int, data: bytes = b"", timeout: float = 2.0) -> _cmd.UdsResult:
        """WriteDataByIdentifier (0x2E) — set a configuration/value identifier."""
        req = _cmd.build_write_did(did, data)
        return _cmd.parse_uds_response(req, self.request(req, timeout))

    def read_did(self, did: int, timeout: float = 2.0) -> _cmd.UdsResult:
        """ReadDataByIdentifier (0x22), returned raw (no codec) for arbitrary OEM DIDs."""
        req = _cmd.build_read_did(did)
        return _cmd.parse_uds_response(req, self.request(req, timeout))

    def security_access(self, level: int = 1, key_fn=None,
                        timeout: float = 2.0) -> _cmd.UdsResult:
        """SecurityAccess (0x27): request a seed, compute the key, send it.

        ``key_fn(seed: bytes) -> bytes`` is the OEM-specific seed→key algorithm (a plugin
        seam). Without it the seed is echoed back, which a real ECU rejects (invalidKey) —
        useful only to confirm the seed exchange itself.
        """
        seed_req = _cmd.build_security_request_seed(level)
        seed_res = _cmd.parse_uds_response(seed_req, self.request(seed_req, timeout))
        if not seed_res.positive:
            return seed_res
        seed = seed_res.data[1:]  # drop the echoed access level
        key = key_fn(seed) if key_fn else seed
        key_req = _cmd.build_security_send_key(level, key)
        return _cmd.parse_uds_response(key_req, self.request(key_req, timeout))

    def __enter__(self) -> UdsClient:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
