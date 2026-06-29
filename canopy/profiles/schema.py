"""Module Profile schema — the contract between Canopy (the brain) and CAB (the bench).

A profile captures everything needed to safely power a module under test, emulate the missing
vehicle, and run triage: identity, the connector pinout with each pin's role, the harness map
(module pin -> CAB standard header -> CAB card+channel), power/diagnostic settings, restbus/load
inputs, and safety gates. Canopy auto-drafts it from an extracted wiring diagram + PCB analysis;
a technician confirms it; CAB (or the vcan dev loop) executes it. Mirrors the CAB reference §8.
"""

from __future__ import annotations

import yaml
from pydantic import BaseModel, Field

# --- CAB card catalog (10-slot reference) ----------------------------------------
CAB_CARDS = {
    "CAB-PWR-IGN": "Power Supervisor / Ignition (Slot 1)",
    "CAB-NET-4CAN-4LIN": "CAN / LIN Network (Slot 2)",
    "CAB-SENS-8V-8R": "Analog + Resistive Sensor (Slot 3)",
    "CAB-PATTERN-12CH": "Crank/Cam/Wheel-Speed Pattern Generator (Slot 4)",
    "CAB-DIG-32SW": "Digital Switch / Relay Driver (Slot 5)",
    "CAB-LOAD-16": "Load Bank / Output Measurement (Slot 6)",
    "CAB-SAFE-SQUIB-8": "Safe Squib Dummy (Slot 7)",
    "CAB-MOTOR-HB-8": "Motor / H-Bridge / PSCM (Slot 8)",
    "CAB-IPC-DISPLAY": "Instrument Cluster / Display (Slot 9)",
    "CAB-LIGHT-HCM-ALCM": "Headlight Expansion (Slot 10)",
}

# Pin roles Canopy classifies from the diagram, and which CAB card services each.
ROLE_CARD = {
    "power": "CAB-PWR-IGN", "ignition": "CAB-PWR-IGN", "accessory": "CAB-PWR-IGN",
    "ground": "CAB-PWR-IGN", "wake": "CAB-PWR-IGN", "enable": "CAB-PWR-IGN",
    "can_h": "CAB-NET-4CAN-4LIN", "can_l": "CAB-NET-4CAN-4LIN",
    "can_fd_h": "CAB-NET-4CAN-4LIN", "can_fd_l": "CAB-NET-4CAN-4LIN",
    "lin": "CAB-NET-4CAN-4LIN", "kline": "CAB-NET-4CAN-4LIN",
    "sensor_ref": "CAB-SENS-8V-8R", "sensor_signal": "CAB-SENS-8V-8R",
    "sensor_return": "CAB-SENS-8V-8R",
    "output": "CAB-LOAD-16", "switch": "CAB-DIG-32SW", "squib": "CAB-SAFE-SQUIB-8",
    "unknown": "",
}


class HarnessPin(BaseModel):
    module_pin: str
    connector: str = ""
    signal: str = ""
    function: str = ""
    role: str = "unknown"     # see ROLE_CARD
    header_pin: str = ""      # CAB standard test-header pin
    card: str = ""            # CAB card servicing this pin
    channel: str = ""         # card channel label


class Identity(BaseModel):
    make: str = ""
    model: str = ""
    year: str = ""
    part_number: str = ""
    vin: str = ""
    label: str = ""
    module_class: str = "unknown"   # PCM | TCM | BCM | ABS_ESC | RCM_ACM | IPC | ...


class PowerSpec(BaseModel):
    vbat_v: float = 13.5
    ignition: bool = True
    accessory: bool = False
    current_limit_a: float = 2.0    # start conservative; tech raises after a clean power-up


class Diagnostics(BaseModel):
    protocols: list[str] = Field(default_factory=lambda: ["CAN", "UDS"])
    request_id: str = ""            # e.g. 0x7E0 (unknown until confirmed)
    response_id: str = ""           # e.g. 0x7E8
    dtc_read: bool = True


class Safety(BaseModel):
    live_pyrotechnics_allowed: bool = False
    confirm_before_energize: bool = True
    notes: list[str] = Field(default_factory=list)


class CommandRequirements(BaseModel):
    """Preconditions an actuation needs before it will be accepted by the module."""

    session: int = 1               # diagnostic session (0x10) the command runs in
    security_level: int = 0        # 0 = none; else the SecurityAccess (0x27) level
    ignition: bool = False         # KL15 must be on


class CommandExpect(BaseModel):
    """How to judge whether the command worked (closed-loop check)."""

    positive: bool = True          # expect a positive UDS response
    signal: str = ""               # or confirm a DBC signal value came back…
    equals: float | None = None
    contains_hex: str = ""         # …or that the response payload contains these bytes


class Command(BaseModel):
    """One named, parameterized action that controls the module over CAN.

    ``kind`` picks the channel:
      * ``raw``         — send ``data_hex`` on ``arbitration_id`` (cyclic if ``cycle_ms``).
      * ``dbc``         — encode ``signals`` onto DBC ``message`` and send.
      * ``uds_io``      — InputOutputControl (0x2F) on ``did`` with ``control`` + ``value_hex``.
      * ``uds_routine`` — RoutineControl (0x31) on ``did`` (routineId) + ``control``/``value_hex``.
      * ``uds_write`` / ``uds_read`` — Write/Read DataByIdentifier (0x2E / 0x22).
    """

    name: str
    kind: str = "raw"
    arbitration_id: str = ""       # raw/dbc TX id (hex, e.g. "0x6C0")
    request_id: str = ""           # uds tester→ECU (hex); falls back to diagnostics.request_id
    response_id: str = ""          # uds ECU→tester (hex)
    is_fd: bool = False
    cycle_ms: int = 0              # >0 = transmit periodically
    data_hex: str = ""             # raw payload bytes
    message: str = ""              # dbc message name
    signals: dict = Field(default_factory=dict)   # dbc signal -> value
    did: str = ""                  # uds DID / routineId (hex)
    control: str = ""              # io control param or routine control type
    value_hex: str = ""            # uds data payload bytes
    requires: CommandRequirements = Field(default_factory=CommandRequirements)
    expect: CommandExpect = Field(default_factory=CommandExpect)
    note: str = ""                 # where it came from (e.g. "captured from bidirectional tool")


class ModuleProfile(BaseModel):
    schema_version: str = "1.0"
    identity: Identity = Field(default_factory=Identity)
    active_cards: list[str] = Field(default_factory=list)
    connector: str = ""
    harness_map: list[HarnessPin] = Field(default_factory=list)
    power: PowerSpec = Field(default_factory=PowerSpec)
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    signals: dict = Field(default_factory=dict)    # restbus / pattern inputs (template/tech-filled)
    loads: dict = Field(default_factory=dict)       # safe loads on module outputs
    expected: dict = Field(default_factory=dict)     # expected observations (pass criteria)
    commands: list[Command] = Field(default_factory=list)  # actuation catalog (labeled buttons)
    pass_fail: list[str] = Field(default_factory=list)
    safety: Safety = Field(default_factory=Safety)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(), sort_keys=False, allow_unicode=True, width=100)

    @classmethod
    def from_yaml(cls, text: str) -> ModuleProfile:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("profile YAML must be a mapping")
        return cls.model_validate(data)
