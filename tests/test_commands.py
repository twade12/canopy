"""The command layer: UDS request builders, response parsing, and DBC signal encode."""

from __future__ import annotations

import cantools

from canopy.hal import commands as cmd

DBC = """
VERSION ""
BO_ 1696 HVAC_Request: 8 ECU
 SG_ AC_Clutch : 0|1@1+ (1,0) [0|1] "" Vector__XXX
 SG_ Blower : 8|4@1+ (1,0) [0|15] "" Vector__XXX
"""


def test_request_builders() -> None:
    assert cmd.build_read_did(0xF190) == bytes([0x22, 0xF1, 0x90])
    assert cmd.build_write_did(0x2A10, b"\x01") == bytes([0x2E, 0x2A, 0x10, 0x01])
    assert cmd.build_io_control(0x4A01, "short_term_adjust", b"\x01") == \
        bytes([0x2F, 0x4A, 0x01, 0x03, 0x01])
    assert cmd.build_routine(0x0203, "start", b"\xAA") == bytes([0x31, 0x01, 0x02, 0x03, 0xAA])
    assert cmd.build_security_request_seed(1) == bytes([0x27, 0x01])
    assert cmd.build_security_send_key(1, b"\xDE\xAD") == bytes([0x27, 0x02, 0xDE, 0xAD])


def test_parse_positive() -> None:
    r = cmd.parse_uds_response(bytes([0x2F, 0x4A, 0x01, 0x03, 0x01]),
                              bytes([0x6F, 0x4A, 0x01, 0x03, 0x01]))
    assert r.positive and r.service == 0x2F
    assert r.data == bytes([0x4A, 0x01, 0x03, 0x01])


def test_parse_negative_names_the_nrc() -> None:
    r = cmd.parse_uds_response(bytes([0x2F, 0x4A, 0x01]), bytes([0x7F, 0x2F, 0x33]))
    assert not r.positive and r.nrc == 0x33 and r.nrc_name == "securityAccessDenied"


def test_parse_timeout() -> None:
    r = cmd.parse_uds_response(bytes([0x22, 0xF1, 0x90]), b"")
    assert not r.positive and "timeout" in r.nrc_name


def test_encode_signal_frame() -> None:
    db = cantools.database.load_string(DBC, database_format="dbc")
    arb, data, ext, is_fd = cmd.encode_signal_frame(
        db, "HVAC_Request", {"AC_Clutch": 1, "Blower": 3})
    assert arb == 0x6A0 and not ext and not is_fd
    assert data[0] == 0x01 and data[1] == 0x03   # AC_Clutch=1 in byte0, Blower=3 in byte1
