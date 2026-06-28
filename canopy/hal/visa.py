"""pyvisa / SCPI driver — drive a real bench DMM or USB oscilloscope from Canopy.

Verified-compatible instruments (SCPI over USB / USBTMC, controllable via pyvisa):
  DMMs   : Rigol DM3058E, Rigol DM3068, Siglent SDM3045X, Siglent SDM3055, Keysight 34461A
  Scopes : Rigol DS1054Z / DS1104Z (DS1000Z family), Siglent SDS1104X-E (SDS1000X-E family)

Install (pure-python backend, no NI-VISA needed):
    pip install ".[visa]"          # pyvisa + pyvisa-py + pyusb + pyserial
On Linux add a udev rule so the USBTMC device is accessible without root (see
docs/INSTRUMENT-PYVISA.md). Then in Canopy: Instruments → Source → pick the USB instrument.

The class implements the same surface as MockInstrument (dmm / scope_frame / set_siggen /
get_siggen / status) so the existing panels drive it unchanged.
"""

from __future__ import annotations

from canopy.hal.instruments import Instrument

# SCPI measurement command per DMM mode (standard SCPI — portable across Rigol/Siglent/Keysight).
_DMM_CMD = {
    "vdc": "MEAS:VOLT:DC?", "vac": "MEAS:VOLT:AC?", "adc": "MEAS:CURR:DC?",
    "aac": "MEAS:CURR:AC?", "resistance": "MEAS:RES?", "frequency": "MEAS:FREQ?",
}
_DMM_UNIT = {"vdc": "V", "vac": "V", "adc": "mA", "aac": "mA",
             "resistance": "Ω", "continuity": "Ω", "frequency": "Hz"}


def list_resources() -> dict:
    """List VISA resource strings (e.g. 'USB0::0x1AB1::...::INSTR'). Empty if pyvisa is absent."""
    try:
        import pyvisa
        try:
            rm = pyvisa.ResourceManager()
        except Exception:
            rm = pyvisa.ResourceManager("@py")  # pure-python backend
        res = list(rm.list_resources())
        return {"available": True, "resources": res}
    except Exception as e:
        return {"available": False, "resources": [], "error": str(e)}


class VisaInstrument(Instrument):
    name = "VISA instrument"

    def __init__(self, resource: str) -> None:
        import pyvisa
        try:
            self.rm = pyvisa.ResourceManager()
        except Exception:
            self.rm = pyvisa.ResourceManager("@py")
        self.dev = self.rm.open_resource(resource)
        self.dev.timeout = 5000
        self.resource = resource
        try:
            self.idn = self.dev.query("*IDN?").strip()
        except Exception:
            self.idn = resource
        parts = self.idn.split(",")
        self.vendor = (parts[0] if parts else "").upper()
        self.model = (parts[1].strip() if len(parts) > 1 else "").upper()
        self.kind = self._detect_kind()
        self.name = self.idn

    def _detect_kind(self) -> str:
        m = self.model
        if any(x in m for x in ("DS1", "DS2", "MSO", "SDS", "DPO", "TBS", "DHO")):
            return "scope"
        if any(x in m for x in ("DM3", "SDM", "3446", "3440", "34401", "DMM")):
            return "dmm"
        return "dmm"

    def status(self) -> dict:
        return {"connected": True, "name": self.idn, "kind": self.kind,
                "caps": [self.kind], "resource": self.resource, "mock": False}

    # --- DMM ---
    def dmm(self, mode: str) -> dict:
        if mode == "continuity":
            r = self._query_float("MEAS:RES?")
            if r is None:
                return {"mode": mode, "value": 0.0, "unit": "Ω", "error": "no reading"}
            return {"mode": mode, "value": round(r, 2), "unit": "Ω", "continuity": r < 50}
        cmd = _DMM_CMD.get(mode, "MEAS:VOLT:DC?")
        r = self._query_float(cmd)
        if r is None:
            return {"mode": mode, "value": 0.0, "unit": _DMM_UNIT.get(mode, ""),
                    "error": "no reading"}
        if mode in ("adc", "aac"):
            r *= 1000.0  # SCPI returns amps; the panel shows mA
        ol = abs(r) > 9e37  # SCPI overload sentinel
        return {"mode": mode, "value": round(r, 4), "unit": _DMM_UNIT.get(mode, ""), "overload": ol}

    def _query_float(self, cmd: str):
        try:
            return float(self.dev.query(cmd).strip())
        except Exception:
            return None

    # --- Scope (Rigol DS1000Z & Siglent SDS1000X-E families) ---
    def scope_frame(self, timebase_s: float, samples: int = 480, frame: int = 0,
                    trig_level: float = 0.0, trig_edge: str = "rising",
                    coupling: str = "dc", channel: int = 1) -> dict:
        d = self.dev
        try:
            # apply the panel's trigger to the instrument
            d.write(f":TRIG:EDGE:SOUR CHAN{channel}")
            d.write(f":TRIG:EDGE:SLOP {'POS' if trig_edge == 'rising' else 'NEG'}")
            d.write(f":TRIG:EDGE:LEV {trig_level}")
            d.write(f":CHAN{channel}:COUP {'AC' if coupling == 'ac' else 'DC'}")
            d.write(f":WAV:SOUR CHAN{channel}")
            d.write(":WAV:MODE NORM")
            d.write(":WAV:FORM BYTE")
            pre = d.query(":WAV:PRE?").split(",")
            xinc, yinc = float(pre[4]), float(pre[7])
            yorig, yref = float(pre[8]), float(pre[9])
            raw = d.query_binary_values(":WAV:DATA?", datatype="B", container=bytes)
            ch1 = [round((b - yorig - yref) * yinc, 4) for b in raw]
            return {"frame": frame, "dt": xinc, "span": xinc * max(1, len(ch1)),
                    "ch1": ch1, "trig": True, "trig_level": trig_level}
        except Exception as e:
            return {"frame": frame, "dt": 1e-6, "span": 1e-3, "ch1": [],
                    "trig": False, "error": str(e)}

    # the signal generator panel is not applicable to a DMM/scope; keep a stable shape
    def set_siggen(self, **kw) -> dict:
        return self.get_siggen()

    def get_siggen(self) -> dict:
        return {"waveform": "sine", "freq_hz": 0, "amp_vpp": 0, "offset_v": 0,
                "duty": 0.5, "enabled": False, "unsupported": True}

    def close(self) -> None:
        try:
            self.dev.close()
        except Exception:
            pass
