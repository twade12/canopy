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

    def open(self) -> UdsClient:
        self._iface = CanInterface(self.channel)
        stack = make_can_stack(self._iface.bus, self.request_id, self.response_id)
        conn = PythonIsoTpConnection(stack)
        config = dict(default_client_config)
        config["data_identifiers"] = {VIN_DID: udsoncan.AsciiCodec(17), **self.data_identifiers}
        self._client = Client(conn, config=config)
        self._client.open()
        return self

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
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

    def __enter__(self) -> UdsClient:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
