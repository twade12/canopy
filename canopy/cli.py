"""CANOPY command-line interface (Phase 0).

Three commands that exercise the whole zero-hardware loop against ``vcan0``:

    canopy send vcan0 123 01020304
    canopy monitor vcan0 --timeout 5 --dbc dbc/platform.dbc
    canopy decode traces/run.blf --dbc dbc/platform.dbc
"""

from __future__ import annotations

from pathlib import Path

import typer

from canopy.config import CanConfig
from canopy.decode import Decoder
from canopy.hal import CanInterface
from canopy.trace import BlfTraceLogger, default_trace_path, read_trace

app = typer.Typer(add_completion=False, help="CANOPY CAN test station CLI (Phase 0).")


def _parse_id(value: str) -> int:
    """Parse a CAN id given as hex (``0x123``/``123``) or decimal (``291``)."""
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    # Bare tokens are treated as hex — CAN ids are conventionally written that way.
    return int(value, 16)


def _make_config(channel: str, interface: str, fd: bool) -> CanConfig:
    return CanConfig.from_env(channel=channel, interface=interface, fd=fd)


@app.command()
def send(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    can_id: str = typer.Argument(..., help="Arbitration id in hex, e.g. 123 or 0x123."),
    data: str = typer.Argument("", help="Payload as hex bytes, e.g. 01020304 (≤8/≤64)."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    extended: bool = typer.Option(False, "--extended", "-e", help="Use a 29-bit id."),
    fd: bool = typer.Option(False, "--fd", help="Send as a CAN FD frame."),
) -> None:
    """Transmit a single frame."""
    payload = bytes.fromhex(data) if data else b""
    config = _make_config(channel, interface, fd)
    with CanInterface(config) as iface:
        msg = iface.send(_parse_id(can_id), payload, is_extended_id=extended)
    typer.echo(f"sent 0x{msg.arbitration_id:X}  {bytes(msg.data).hex(' ')}")


@app.command()
def monitor(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    timeout: float = typer.Option(2.0, help="Idle seconds before stopping."),
    limit: int | None = typer.Option(None, help="Stop after N frames."),
    fd: bool = typer.Option(False, "--fd", help="Receive CAN FD frames."),
    dbc: Path | None = typer.Option(None, exists=True, help="DBC file for live decode."),
    trace: bool = typer.Option(False, "--trace", help="Write a BLF trace of the session."),
) -> None:
    """Print received frames (optionally decoded), optionally logging a BLF trace."""
    config = _make_config(channel, interface, fd)
    decoder = Decoder.from_files(dbc) if dbc else None
    trace_logger = BlfTraceLogger(default_trace_path("monitor")) if trace else None
    count = 0
    try:
        with CanInterface(config) as iface:
            for msg in iface.monitor(timeout=timeout, limit=limit):
                count += 1
                if trace_logger:
                    trace_logger.log(msg)
                if decoder:
                    typer.echo(decoder.format(msg))
                else:
                    typer.echo(f"0x{msg.arbitration_id:X}  {bytes(msg.data).hex(' ')}")
    finally:
        if trace_logger:
            trace_logger.close()
            typer.echo(f"trace written: {trace_logger.path}")
    typer.echo(f"{count} frame(s)")


@app.command()
def decode(
    trace_file: Path = typer.Argument(..., exists=True, help="BLF trace to decode."),
    dbc: Path = typer.Option(..., exists=True, help="DBC file to decode against."),
) -> None:
    """Decode a recorded BLF trace against a DBC, frame by frame."""
    decoder = Decoder.from_files(dbc)
    messages = read_trace(trace_file)
    for msg in messages:
        typer.echo(decoder.format(msg))
    typer.echo(f"{len(messages)} frame(s)")


if __name__ == "__main__":
    app()
