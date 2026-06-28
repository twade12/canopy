"""Bench instruments: DMM + oscilloscope + signal generator (see docs/INSTRUMENT-PROTOCOL.md).

`MockInstrument` synthesizes a fully self-consistent bench with NO hardware: the signal
generator's settings drive the simulated scope trace and DMM readings, so the panels are live and
demoable immediately. `SerialInstrument` (lazy pyserial) speaks the same protocol to a real USB
device. `InstrumentHub` holds the active instrument for the app.
"""

from __future__ import annotations

import math
import random
import time

WAVEFORMS = ("sine", "square", "triangle", "sawtooth", "dc")


def _wave(kind: str, phase: float, duty: float = 0.5) -> float:
    """One cycle of a unit waveform in [-1, 1]; phase in turns (0..1 = one cycle)."""
    frac = phase - math.floor(phase)
    if kind == "sine":
        return math.sin(2 * math.pi * frac)
    if kind == "square":
        return 1.0 if frac < duty else -1.0
    if kind == "triangle":
        return 4 * frac - 1 if frac < 0.5 else 3 - 4 * frac
    if kind == "sawtooth":
        return 2 * frac - 1
    return 0.0  # dc


class SignalGen:
    def __init__(self) -> None:
        self.waveform = "sine"
        self.freq_hz = 1000.0
        self.amp_vpp = 2.0
        self.offset_v = 0.0
        self.duty = 0.5
        self.enabled = True

    def value_at(self, t: float) -> float:
        if not self.enabled:
            return 0.0
        if self.waveform == "dc":
            return self.offset_v
        w = _wave(self.waveform, self.freq_hz * t, self.duty)
        return self.offset_v + (self.amp_vpp / 2.0) * w

    def asdict(self) -> dict:
        return {"waveform": self.waveform, "freq_hz": self.freq_hz, "amp_vpp": self.amp_vpp,
                "offset_v": self.offset_v, "duty": self.duty, "enabled": self.enabled}


class Instrument:
    name = "instrument"

    def status(self) -> dict:
        return {"connected": True, "name": self.name, "caps": ["dmm", "scope", "siggen"]}

    def close(self) -> None:
        pass


class MockInstrument(Instrument):
    name = "Mock bench (simulated)"

    def __init__(self) -> None:
        self.sg = SignalGen()
        self.probe_ohms = 1000.0   # what the resistance/continuity probe "sees"
        self.load_ohms = 1000.0    # assumed load for current modes

    # --- signal generator ---
    def set_siggen(self, **kw) -> dict:
        sg = self.sg
        if "waveform" in kw and kw["waveform"] in WAVEFORMS:
            sg.waveform = kw["waveform"]
        for k in ("freq_hz", "amp_vpp", "offset_v", "duty"):
            if kw.get(k) is not None:
                setattr(sg, k, float(kw[k]))
        if kw.get("enabled") is not None:
            sg.enabled = bool(kw["enabled"])
        sg.duty = min(0.95, max(0.05, sg.duty))
        return sg.asdict()

    def get_siggen(self) -> dict:
        return self.sg.asdict()

    # --- DMM ---
    def dmm(self, mode: str) -> dict:
        sg = self.sg
        # numeric stats over one period of the generator output
        n = 256
        period = 1.0 / max(1e-6, sg.freq_hz)
        xs = [sg.value_at(period * i / n) for i in range(n)]
        vdc = sum(xs) / n
        vrms = math.sqrt(sum(x * x for x in xs) / n)
        vac = math.sqrt(max(0.0, vrms * vrms - vdc * vdc))
        def ns(s):
            return random.gauss(0, s)
        if mode == "vdc":
            return {"mode": mode, "value": round(vdc + ns(0.002), 4), "unit": "V"}
        if mode == "vac":
            return {"mode": mode, "value": round(vac + ns(0.002), 4), "unit": "V"}
        if mode == "adc":
            ma = vdc / self.load_ohms * 1000 + ns(0.05)
            return {"mode": mode, "value": round(ma, 3), "unit": "mA"}
        if mode == "aac":
            ma = vac / self.load_ohms * 1000 + ns(0.05)
            return {"mode": mode, "value": round(ma, 3), "unit": "mA"}
        if mode == "resistance":
            val = round(self.probe_ohms + ns(self.probe_ohms * 0.001), 2)
            return {"mode": mode, "value": val, "unit": "Ω", "overload": self.probe_ohms > 5e6}
        if mode == "continuity":
            return {"mode": mode, "value": round(self.probe_ohms, 1), "unit": "Ω",
                    "continuity": self.probe_ohms < 50}
        if mode == "frequency":
            return {"mode": mode, "value": round(sg.freq_hz, 2), "unit": "Hz"}
        return {"mode": mode, "value": 0.0, "unit": ""}

    # --- scope ---
    def _mean_dc(self) -> float:
        period = 1.0 / max(1e-6, self.sg.freq_hz)
        n = 256
        return sum(self.sg.value_at(period * i / n) for i in range(n)) / n

    def _trigger_offset(self, level: float, edge: str) -> tuple[float, bool]:
        """Time offset (within one period) of the first level crossing on the chosen edge."""
        if not self.sg.enabled or self.sg.waveform == "dc":
            return 0.0, False
        period = 1.0 / max(1e-6, self.sg.freq_hz)
        n = 2000
        prev = self.sg.value_at(0.0)
        for i in range(1, n + 1):
            t = period * i / n
            v = self.sg.value_at(t)
            up = v >= level > prev
            down = v <= level < prev
            if (edge == "rising" and up) or (edge == "falling" and down):
                return t, True
            prev = v
        return 0.0, False

    def scope_frame(self, timebase_s: float, samples: int = 480, frame: int = 0,
                    trig_level: float = 0.0, trig_edge: str = "rising",
                    coupling: str = "dc") -> dict:
        """One captured window. The window starts at the trigger crossing so the trace is stable;
        AC coupling removes the DC component; light noise is added for realism."""
        span = max(1e-6, timebase_s) * 10.0  # 10 horizontal divisions
        dt = span / samples
        t_off, trig = self._trigger_offset(trig_level, trig_edge)
        dc = self._mean_dc() if coupling == "ac" else 0.0
        nz = (self.sg.amp_vpp / 2.0 or 1.0) * 0.012
        ch1 = [round(self.sg.value_at(t_off + i * dt) - dc + random.gauss(0, nz), 4)
               for i in range(samples)]
        return {"frame": frame, "dt": dt, "span": span, "ch1": ch1, "trig": trig,
                "trig_level": round(trig_level - dc, 4)}


class SerialInstrument(Instrument):
    name = "USB instrument"

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        import json as _json

        import serial  # lazy
        self._json = _json
        self._ser = serial.Serial(port, baudrate, timeout=1.0)

    def _txn(self, obj: dict) -> dict:
        self._ser.write((self._json.dumps(obj) + "\n").encode())
        line = self._ser.readline().decode("utf-8").strip()
        return self._json.loads(line) if line else {}

    def set_siggen(self, **kw) -> dict:
        return self._txn({"op": "siggen", **kw})

    def get_siggen(self) -> dict:
        return self._txn({"op": "siggen"})

    def dmm(self, mode: str) -> dict:
        return self._txn({"op": "dmm", "mode": mode})

    def scope_frame(self, timebase_s: float, samples: int = 480, frame: int = 0,
                    trig_level: float = 0.0, trig_edge: str = "rising",
                    coupling: str = "dc") -> dict:
        return self._txn({"op": "scope_once", "timebase": timebase_s, "samples": samples,
                          "trig_level": trig_level, "trig_edge": trig_edge, "coupling": coupling})

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass


class InstrumentHub:
    def __init__(self) -> None:
        self.instr: Instrument = MockInstrument()  # mock by default — works with no hardware

    def status(self) -> dict:
        s = self.instr.status()
        s["mock"] = isinstance(self.instr, MockInstrument)
        return s

    def connect(self, source: str | None = None) -> dict:
        """source: '' -> simulated; a VISA resource (contains '::' or USB/TCPIP/GPIB/ASRL) ->
        real DMM/scope via pyvisa; otherwise a serial port -> SerialInstrument."""
        try:
            self.instr.close()
        except Exception:
            pass
        src = (source or "").strip()
        self.last_error = ""
        if not src:
            self.instr = MockInstrument()
        elif "::" in src or src.upper().startswith(("USB", "TCPIP", "GPIB", "ASRL")):
            try:
                from canopy.hal.visa import VisaInstrument
                self.instr = VisaInstrument(src)
            except Exception as e:
                self.instr = MockInstrument()
                self.last_error = f"VISA connect failed: {e}"
        else:
            try:
                self.instr = SerialInstrument(src)
            except Exception as e:
                self.instr = MockInstrument()
                self.last_error = f"serial connect failed: {e}"
        s = self.status()
        if self.last_error:
            s["error"] = self.last_error
        return s

    def __getattr__(self, item):
        # delegate dmm/scope_frame/set_siggen/get_siggen to the active instrument
        return getattr(self.instr, item)


def now_ms() -> int:
    return int(time.time() * 1000)
