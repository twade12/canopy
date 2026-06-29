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


def _hexbytes(s: str) -> bytes:
    s = (s or "").replace("0x", "").replace(" ", "")
    return bytes.fromhex(s) if s else b""


@uds_app.command("io-control")
def uds_io_control(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    did: str = typer.Argument(..., help="IO DID, e.g. 0x4A01."),
    control: str = typer.Option("short_term_adjust",
                                help="return_control|reset_to_default|freeze|short_term_adjust."),
    data: str = typer.Option("", help="Control-state payload bytes (hex)."),
    session: int = typer.Option(3, help="Diagnostic session to enter first."),
    interface: str = typer.Option("socketcan"),
    req: str = typer.Option("0x7E0"),
    rsp: str = typer.Option("0x7E8"),
) -> None:
    """InputOutputControl (0x2F) — force an actuator (e.g. A/C clutch ON)."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(session)
        typer.echo(str(uds.io_control(_parse_id(did), control, _hexbytes(data))))


@uds_app.command("routine")
def uds_routine(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    routine_id: str = typer.Argument(..., help="Routine id, e.g. 0x0203."),
    control: str = typer.Option("start", help="start|stop|results."),
    data: str = typer.Option("", help="Routine option record (hex)."),
    session: int = typer.Option(3, help="Diagnostic session to enter first."),
    interface: str = typer.Option("socketcan"),
    req: str = typer.Option("0x7E0"),
    rsp: str = typer.Option("0x7E8"),
) -> None:
    """RoutineControl (0x31) — run a built-in actuator/self-test routine."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(session)
        typer.echo(str(uds.routine_control(_parse_id(routine_id), control, _hexbytes(data))))


@uds_app.command("read-did")
def uds_read_did(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    did: str = typer.Argument(..., help="DID, e.g. 0xF190."),
    interface: str = typer.Option("socketcan"),
    req: str = typer.Option("0x7E0"),
    rsp: str = typer.Option("0x7E8"),
) -> None:
    """ReadDataByIdentifier (0x22), raw — for arbitrary OEM DIDs."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(1)
        r = uds.read_did(_parse_id(did))
    typer.echo(str(r) if not r.positive else f"DID 0x{_parse_id(did):04X} = {r.data.hex(' ')}")


@uds_app.command("write-did")
def uds_write_did(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    did: str = typer.Argument(..., help="DID, e.g. 0x2A10."),
    data: str = typer.Argument(..., help="Bytes to write (hex)."),
    session: int = typer.Option(3, help="Diagnostic session to enter first."),
    interface: str = typer.Option("socketcan"),
    req: str = typer.Option("0x7E0"),
    rsp: str = typer.Option("0x7E8"),
) -> None:
    """WriteDataByIdentifier (0x2E) — set a configuration/value identifier."""
    with _uds_client(channel, interface, req, rsp) as uds:
        uds.change_session(session)
        typer.echo(str(uds.write_did(_parse_id(did), _hexbytes(data))))


@app.command("send-signal")
def send_signal(
    channel: str = typer.Argument(..., help="CAN channel, e.g. vcan0."),
    dbc: str = typer.Argument(..., help="Path to the platform DBC file."),
    message: str = typer.Argument(..., help="DBC message name to encode."),
    assignments: list[str] = typer.Argument(None, help="Signal=Value pairs, e.g. AC_Clutch=1."),
    interface: str = typer.Option("socketcan"),
    fd: bool = typer.Option(False, "--fd", help="Force a CAN FD frame."),
) -> None:
    """Encode named DBC signals onto a message and transmit it (application-layer control)."""
    import cantools

    from canopy.hal import commands as cmd
    from canopy.hal.can_iface import CanInterface

    db = cantools.database.load_file(dbc)
    signals: dict = {}
    for pair in assignments or []:
        key, _, val = pair.partition("=")
        val = val.strip()
        try:
            signals[key.strip()] = float(val) if "." in val else int(val)
        except ValueError:
            signals[key.strip()] = val
    arb, data, ext, is_fd = cmd.encode_signal_frame(db, message, signals)
    with CanInterface(_make_config(channel, interface, fd=fd or is_fd)) as iface:
        iface.send(arb, data, is_extended_id=ext, is_fd=fd or is_fd)
    typer.echo(f"sent 0x{arb:X} [{data.hex(' ')}]")


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


@vision_app.command("migrate")
def vision_migrate(
    sqlite: Path | None = typer.Option(None, help="Source SQLite DB (default: configured one)."),
    to: str | None = typer.Option(None, help="Target postgresql://… (else CANOPY_DATABASE_URL)."),
) -> None:
    """Migrate the local SQLite knowledge base into Postgres + pgvector."""
    import os

    from canopy.vision.config import VisionConfig
    from canopy.vision.migrate import migrate_sqlite_to_pg

    cfg = VisionConfig.from_env()
    src = sqlite or cfg.db_path
    dst = to or os.environ.get("CANOPY_DATABASE_URL")
    if not dst:
        raise typer.BadParameter("set --to or CANOPY_DATABASE_URL to the target Postgres URL")
    if not Path(src).exists():
        raise typer.BadParameter(f"source SQLite not found: {src}")
    typer.echo(f"Migrating {src} → {dst}")
    counts = migrate_sqlite_to_pg(src, dst, log=typer.echo)
    typer.echo("done: " + ", ".join(f"{v} {k}" for k, v in counts.items()))


if __name__ == "__main__":
    app()
