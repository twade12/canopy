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

BANNER = r"""
   ██████╗ █████╗ ███╗   ██╗ ██████╗ ██████╗ ██╗   ██╗
  ██╔════╝██╔══██╗████╗  ██║██╔═══██╗██╔══██╗╚██╗ ██╔╝
  ██║     ███████║██╔██╗ ██║██║   ██║██████╔╝ ╚████╔╝
  ██║     ██╔══██║██║╚██╗██║██║   ██║██╔═══╝   ╚██╔╝
  ╚██████╗██║  ██║██║ ╚████║╚██████╔╝██║        ██║
   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝        ██║
   Universal CAN Module Test & Diagnostic Station
"""


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """Show the banner and help when invoked with no subcommand."""
    if ctx.invoked_subcommand is None:
        typer.echo(BANNER)
        typer.echo(ctx.get_help())
        raise typer.Exit()


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


# --- sim: the "car in a box" --------------------------------------------------
sim_app = typer.Typer(help="Run a software-defined virtual vehicle (restbus + UDS).")
app.add_typer(sim_app, name="sim")


@sim_app.command("run")
def sim_run(
    vehicle: Path = typer.Argument(..., exists=True, help="Vehicle YAML (see vehicles/)."),
    channel: str = typer.Option("vcan0", help="CAN channel to broadcast on."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    duration: float = typer.Option(0.0, help="Seconds to run; 0 = until Ctrl-C."),
) -> None:
    """Bring up every virtual ECU's restbus (and UDS responders) on a channel."""
    import time

    from canopy.sim.loader import load_vehicle

    config = _make_config(channel, interface, fd=False)
    with CanInterface(config) as iface:
        car = load_vehicle(vehicle, iface)
        ecus = ", ".join(e.name for e in car.ecus)
        typer.echo(f"vehicle '{car.name}' up on {channel}: ECUs [{ecus}]")
        car.start()
        try:
            if duration > 0:
                time.sleep(duration)
            else:
                typer.echo("broadcasting… Ctrl-C to stop")
                while True:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            car.stop()
    typer.echo(f"stopped; {car.frames_sent} frame(s) sent")


# --- uds: the station as tester -----------------------------------------------
uds_app = typer.Typer(help="UDS diagnostics (station acts as the tester).")
app.add_typer(uds_app, name="uds")


def _uds_client(channel: str, interface: str, req: str, rsp: str):
    from canopy.hal.uds import UdsClient

    config = _make_config(channel, interface, fd=False)
    return UdsClient(channel=config, request_id=_parse_id(req), response_id=_parse_id(rsp))


@uds_app.command("vin")
def uds_vin(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    req: str = typer.Option("0x7E0", help="Tester request id."),
    rsp: str = typer.Option("0x7E8", help="ECU response id."),
) -> None:
    """Read the VIN (DID 0xF190)."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(1)
        typer.echo(uds.read_vin())


@uds_app.command("read-dtc")
def uds_read_dtc(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    req: str = typer.Option("0x7E0", help="Tester request id."),
    rsp: str = typer.Option("0x7E8", help="ECU response id."),
    mask: str = typer.Option("0xFF", help="DTC status mask."),
) -> None:
    """Read stored DTCs by status mask (service 0x19)."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(1)
        dtcs = uds.read_dtcs(_parse_id(mask))
    for d in dtcs:
        typer.echo(f"{d.code_hex}  status=0x{d.status:02X}")
    typer.echo(f"{len(dtcs)} DTC(s)")


@uds_app.command("clear-dtc")
def uds_clear_dtc(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    interface: str = typer.Option("socketcan", help="python-can backend."),
    req: str = typer.Option("0x7E0", help="Tester request id."),
    rsp: str = typer.Option("0x7E8", help="ECU response id."),
) -> None:
    """Clear stored DTCs (service 0x14)."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(1)
        uds.clear_dtcs()
    typer.echo("DTCs cleared")


# --- vision: local AI wiring-diagram tool -------------------------------------
vision_app = typer.Typer(help="Local AI wiring-diagram + chat web UI (Ollama).")
app.add_typer(vision_app, name="vision")


@vision_app.command("serve")
def vision_serve(
    host: str = typer.Option("127.0.0.1", help="Bind address."),
    port: int = typer.Option(8088, help="Port."),
    model: str | None = typer.Option(None, help="Ollama model (default: gemma4:26b)."),
    ollama_url: str | None = typer.Option(None, help="Ollama base URL."),
) -> None:
    """Launch the wiring-diagram vision/chat server (needs the 'vision' extra + Ollama)."""
    try:
        import uvicorn

        from canopy.vision.app import create_app
        from canopy.vision.config import VisionConfig
    except ModuleNotFoundError as exc:
        raise typer.BadParameter(
            f"vision extra not installed ({exc.name}). Run: pip install -e '.[vision]'"
        ) from exc

    config = VisionConfig.from_env(model=model, ollama_url=ollama_url)
    config.ensure_dirs()
    typer.echo(
        f"CANOPY Vision → http://{host}:{port}  (model: {config.model}, data: {config.data_dir})"
    )
    uvicorn.run(create_app(config), host=host, port=port)


if __name__ == "__main__":
    app()
