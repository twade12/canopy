"""Auto-draft a Module Profile from what Canopy already extracted (pinout + PCB + identity).

Deterministic and grounded — it only classifies pins that exist in the diagram and maps them to
CAB cards. The technician then confirms/edits before anything is energized (CAB §11 / CLAUDE §10).
"""

from __future__ import annotations

import re

from canopy.profiles.schema import ROLE_CARD, HarnessPin, Identity, ModuleProfile, Safety

# Pin-role classification from the signal/function text. Order matters (first match wins).
_ROLE_PATTERNS: list[tuple[str, str]] = [
    ("can_fd_h", r"can[\s_-]?fd[\s_-]?h|canfd\+"),
    ("can_fd_l", r"can[\s_-]?fd[\s_-]?l|canfd-"),
    ("can_h", r"\bcan[\s_-]?(h|hi|high)\b|can[\s_-]?\+|hs?\s*can\s*\+|\bcanh\b"),
    ("can_l", r"\bcan[\s_-]?(l|lo|low)\b|can[\s_-]?-|hs?\s*can\s*-|\bcanl\b"),
    ("lin", r"\blin\b"),
    ("kline", r"\bk[\s_-]?line\b|iso\s*9141"),
    ("ground", r"\b(gnd|ground|grnd|sigrtn|pwrgnd|return|rtn)\b"),
    ("ignition", r"\b(kl15|ign|ignition|run/?start|run|crank\s*sig)\b"),
    ("accessory", r"\bacc\b|accessory"),
    ("power", r"\b(b\+|kl30|vbat|vbatt|batt|battery|\+12|power|pwr|vpwr|vbpwr)\b"),
    ("wake", r"\bwake\b|wak\b"),
    ("enable", r"\benable\b|\ben\b"),
    ("sensor_ref", r"5\s*v\s*ref|vref|reference|sensor\s*(supply|ref)|5v"),
    ("sensor_return", r"sensor\s*(gnd|ground|return)|low\s*ref"),
    ("sensor_signal", r"sensor|sig|signal|temp|press|position|tps|map|maf|o2|knock"),
    ("output", r"relay|solenoid|injector|motor|lamp|coil|valve|pump|fan|output|drive|control|"
               r"actuator|clutch\s*coil"),
    ("switch", r"switch|\bsw\b|brake|clutch|prndl|door|pedal|button|contact|input"),
]


def classify_role(signal: str, function: str = "") -> str:
    text = f"{signal} {function}".lower()
    for role, pat in _ROLE_PATTERNS:
        if re.search(pat, text):
            return role
    return "unknown"


# Module-class inference from tags / label (drives safety + which cards are relevant).
_CLASS_PATTERNS: list[tuple[str, str]] = [
    ("PCM", r"\bpcm\b|powertrain"), ("ECM", r"\becm\b|\becu\b|engine control"),
    ("TCM", r"\btcm\b|\btcu\b|transmission"), ("FICM", r"\bficm\b|fuel inject"),
    ("ICM", r"\bicm\b|ignition control"),
    ("ABS_ESC", r"\babs\b|\bebcm\b|\besc\b|\besp\b|brake|stability"),
    ("RCM_ACM", r"\brcm\b|\bacm\b|air\s*bag|airbag|srs|restraint|squib|pretension"),
    ("BCM", r"\bbcm\b|body control"), ("TIPM", r"\btipm\b|integrated power"),
    ("HVAC", r"\bhvac\b|climate|heating|a/?c\b"), ("IPC", r"\bipc\b|cluster|instrument"),
    ("CCM", r"\bccm\b|comfort|central control"), ("GEM", r"\bgem\b"),
    ("HCM", r"\bhcm\b|\balcm\b|headlight|lighting"),
    ("PSCM", r"\bpscm\b|\bsas\b|steering"),
    ("TCCM", r"\btccm\b|transfer case"), ("ASCM", r"\bascm\b|air suspension"),
    ("DDM_PDM", r"\bddm\b|\bpdm\b|door module"), ("MSM", r"\bmsm\b|memory seat"),
]


def infer_module_class(label: str, tags: list[str]) -> str:
    text = f"{label} {' '.join(tags)}".lower()
    for cls, pat in _CLASS_PATTERNS:
        if re.search(pat, text):
            return cls
    return "unknown"


# Which extra cards a module class implies beyond power+network.
_CLASS_CARDS = {
    "PCM": ["CAB-PATTERN-12CH", "CAB-SENS-8V-8R", "CAB-DIG-32SW", "CAB-LOAD-16"],
    "ECM": ["CAB-PATTERN-12CH", "CAB-SENS-8V-8R", "CAB-LOAD-16"],
    "TCM": ["CAB-PATTERN-12CH", "CAB-SENS-8V-8R", "CAB-LOAD-16"],
    "FICM": ["CAB-LOAD-16"], "ICM": ["CAB-PATTERN-12CH", "CAB-LOAD-16"],
    "ABS_ESC": ["CAB-PATTERN-12CH", "CAB-LOAD-16"],
    "RCM_ACM": ["CAB-SAFE-SQUIB-8", "CAB-DIG-32SW"],
    "BCM": ["CAB-DIG-32SW", "CAB-LOAD-16", "CAB-SENS-8V-8R"],
    "TIPM": ["CAB-DIG-32SW", "CAB-LOAD-16"],
    "HVAC": ["CAB-SENS-8V-8R", "CAB-DIG-32SW", "CAB-MOTOR-HB-8"],
    "IPC": ["CAB-IPC-DISPLAY", "CAB-PATTERN-12CH"],
    "CCM": ["CAB-DIG-32SW", "CAB-MOTOR-HB-8"],
    "PSCM": ["CAB-PATTERN-12CH", "CAB-MOTOR-HB-8"],
    "HCM": ["CAB-LIGHT-HCM-ALCM", "CAB-MOTOR-HB-8", "CAB-LOAD-16"],
}


def build_profile(store, vehicle_id: int) -> ModuleProfile:
    v = store.get_vehicle(vehicle_id)
    tags = store.list_tags(vehicle_id)
    pins = store.list_pinouts(vehicle_id)
    mclass = infer_module_class(v.get("label", ""), tags)

    connector = ""
    harness: list[HarnessPin] = []
    chan_count: dict[str, int] = {}
    for i, p in enumerate(pins, start=1):
        role = classify_role(p.get("signal", ""), p.get("function", ""))
        card = ROLE_CARD.get(role, "")
        chan = ""
        if card:
            chan_count[card] = chan_count.get(card, 0) + 1
            chan = f"{card.split('-')[1]}{chan_count[card]}"
        connector = connector or p.get("connector", "")
        harness.append(HarnessPin(
            module_pin=str(p.get("pin", "")), connector=str(p.get("connector", "")),
            signal=str(p.get("signal", "")), function=str(p.get("function", "")),
            role=role, header_pin=f"H{i}", card=card, channel=chan,
        ))

    cards = ["CAB-PWR-IGN", "CAB-NET-4CAN-4LIN"]
    cards += [c for c in _CLASS_CARDS.get(mclass, []) if c not in cards]
    # also include any card implied by an actually-classified pin
    for hp in harness:
        if hp.card and hp.card not in cards:
            cards.append(hp.card)

    is_srs = mclass == "RCM_ACM"
    safety = Safety(
        live_pyrotechnics_allowed=False, confirm_before_energize=True,
        notes=(["DUMMY squib loads ONLY — never connect live pyrotechnics."] if is_srs else [])
        + ["Verify power/ground/CAN pins against the diagram before energizing."],
    )

    profile = ModuleProfile(
        identity=Identity(
            make=v.get("make", ""), model=v.get("model", ""), year=v.get("year", ""),
            vin=v.get("vin", ""), label=v.get("label", ""), module_class=mclass,
        ),
        active_cards=cards, connector=connector, harness_map=harness, safety=safety,
    )
    # sensible signal/expected placeholders the tech fills in
    profile.expected = {"can_activity": True}
    return profile
