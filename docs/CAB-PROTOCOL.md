# Host ↔ CAB serial command protocol (v1)

This is the contract between the Canopy host (`canopy/hal/cab.py`) and the CAB backplane
management MCU. Lock it now so firmware and software can be built in parallel. It is intentionally
simple, safe-by-default, and human-readable.

## Transport
- **USB-CDC serial** (the backplane MCU presents one virtual COM port). 115200 baud, 8N1; the host
  may probe by sending `hello`.
- **Newline-delimited JSON** (one compact JSON object per line, `\n` terminated). UTF-8.
- **Request/response correlated by `id`** (monotonic integer chosen by the host). The CAB echoes the
  `id` in its reply. Unsolicited **events** (faults, health) carry no `id` and an `event` field.

## Safety model (non-negotiable, mirrors CAB §7.2 / §11)
- Every output powers up and resets to **safe / open / de-energized**.
- Energizing anything (power rails, loads, squib dummies) requires an explicit **`arm`** after the
  channels are configured. `set` only stages a configuration; it does not energize.
- **`estop`** disables all enables through a path independent of normal command flow; the physical
  E-stop and squib key switch are hardware interlocks the host cannot override.
- The squib card additionally requires its hardware key before `arm` has any effect.

## Host → CAB commands
```json
{"id": 12, "op": "set", "card": "CAB-PATTERN-12CH", "channel": "WHEEL_FL",
 "mode": "frequency", "value": {"frequency_hz": 82.4, "amplitude": "12V_OPEN_DRAIN"},
 "fault_injection": "none"}
```
| op | purpose | key fields |
|---|---|---|
| `hello` | handshake / probe | → `{fw, protocol, cards:[...]}` |
| `status` | global state | → rails, temp, estop, armed, slot map |
| `health` | per-card health packets | → list of health objects |
| `set` | stage a channel config (no energize) | `card, channel, mode, value, fault_injection` |
| `read` | read a measurement/readback | `card, channel` → `{value, unit}` |
| `arm` | enable outputs for a card or `ALL` | `card` (default `ALL`) |
| `disarm` | return outputs to safe/open | `card` (default `ALL`) |
| `estop` | immediate hardware-independent disable | — |
| `reset` | all channels to safe/open defaults | — |

`mode`/`value` are card-specific (e.g. pattern: `frequency`/`pattern`; load: `resistive`/`pwm`;
power: `vbat`/`ign`; sensor: `analog_voltage`/`resistance`). `fault_injection` ∈
`none|open|short_gnd|short_bat|dropout|jitter|stuck` per the card's capability.

## CAB → host
Reply to a command (same `id`):
```json
{"id": 12, "ok": true, "readback": {"frequency_hz": 82.4}}
{"id": 12, "ok": false, "error": "card CAB-PATTERN-12CH not present"}
```
Unsolicited event (no `id`):
```json
{"event": "fault", "card": "CAB-LOAD-16", "channel": "LOAD1", "flags": ["overcurrent"], "ts": 184523}
{"event": "health", "card": "CAB-PWR-IGN", "fw": "1.0.0",
 "rails": {"vbat": 13.5, "5v": 5.02, "3v3": 3.30}, "temp_c": 31, "faults": [], "armed": false}
```

## Channel command shape (canonical, from CAB §7.3)
Each card MCU accepts and reports: `card`, `channel`, `mode`, `value`, `enable`, `fault_state`,
`timestamp`, `readback`. The backplane MCU aggregates these onto the single host serial link.

## Reference flow (safe bring-up of a module)
1. `hello` → confirm cards present match the profile's `active_cards`.
2. `reset` → everything safe/open.
3. `set` power rails (vbat off, current_limit per profile), `set` restbus/pattern/sensor channels.
4. `arm CAB-PWR-IGN` with a low current limit → `read` quiescent current (INA) → watch for `fault`.
5. Raise rails / `arm` network + pattern cards → run the profile's checks, `read` outputs.
6. `disarm`/`reset` between steps; `estop` on any unexpected fault.

`canopy/hal/cab.py` implements this with a `MockCABLink` (no hardware) and a `SerialCABLink`
(pyserial), so the test runner and UI can be developed entirely against the mock today.
