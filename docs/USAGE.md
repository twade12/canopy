# CANOPY — Using the Software Stack with a USB-to-CAN Adapter

> An exhaustive, hands-on guide to driving the current CANOPY stack against **real CAN
> hardware** via a USB-to-CAN adapter. Everything here also works on a virtual bus
> (`vcan0`) with zero hardware — see the [README](../README.md) — but this document is
> about putting real electrons on the wire. For the AI wiring-diagram tool, see
> [AI-VISION.md](AI-VISION.md).

---

## Contents
1. [What the stack can do today](#1-what-the-stack-can-do-today)
2. [Prerequisites & install](#2-prerequisites--install)
3. [How SocketCAN works (the mental model)](#3-how-socketcan-works-the-mental-model)
4. [Choosing a USB-to-CAN adapter](#4-choosing-a-usb-to-can-adapter)
5. [Bringing up a real adapter (`can0`)](#5-bringing-up-a-real-adapter-can0)
6. [Verifying the link with `can-utils`](#6-verifying-the-link-with-can-utils)
7. [Wiring an adapter to a module (safely)](#7-wiring-an-adapter-to-a-module-safely)
8. [Using the CLI on real hardware](#8-using-the-cli-on-real-hardware)
9. [Two-channel setups (restbus + tester)](#9-two-channel-setups-restbus--tester)
10. [Configuration & environment variables](#10-configuration--environment-variables)
11. [End-to-end worked example: 2016 F-250 PCM](#11-end-to-end-worked-example-2016-f-250-pcm)
12. [Troubleshooting](#12-troubleshooting)
13. [Command cheat-sheet](#13-command-cheat-sheet)

---

## 1. What the stack can do today

With a USB-CAN adapter you can, **right now**:

| Capability | Command | Module |
|---|---|---|
| Send a raw frame | `canopy send can0 …` | [hal/can_iface.py](../canopy/hal/can_iface.py) |
| Sniff / decode live traffic | `canopy monitor can0 --dbc …` | [decode.py](../canopy/decode.py) |
| Log a Vector-compatible BLF trace | `canopy monitor can0 --trace` | [trace.py](../canopy/trace.py) |
| Decode a recorded trace | `canopy decode run.blf --dbc …` | — |
| **Run a virtual vehicle (restbus)** on real CAN | `canopy sim run …yaml --channel can0` | [sim/](../canopy/sim/) |
| **Act as a UDS tester** (VIN, read/clear DTCs) | `canopy uds … can0` | [hal/uds.py](../canopy/hal/uds.py) |

The "car in a box" simulator broadcasts a full restbus — with rolling alive-counters and
checksums — so a real module on the bench leaves limp/sleep mode and behaves as installed.

---

## 2. Prerequisites & install

- **Linux** (SocketCAN is a Linux kernel subsystem — this is mandatory). Ubuntu 24.04 LTS
  or Raspberry Pi OS 64-bit recommended.
- **Python ≥ 3.10**.
- **`can-utils`** for low-level bring-up/verification: `sudo apt install can-utils`.

```bash
git clone <your-canopy-remote> && cd canopy
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # core + dev
# (optional) AI wiring-diagram tool:  pip install -e ".[vision]"
```

Confirm the CLI: `canopy --help` (prints the banner + commands).

---

## 3. How SocketCAN works (the mental model)

SocketCAN exposes each CAN channel as a **network interface** (like `eth0`), named
`can0`, `can1`, … A "virtual" interface `vcan0` behaves identically but has no hardware
behind it. **The CANOPY code does not care which it is** — you select the channel by name.
That's the entire point: develop on `vcan0`, deploy on `can0`, no code change.

Key consequences:
- You bring a channel **up** with `ip link`, set its **bitrate**, then apps can use it.
- The **bitrate must match the bus** exactly, or you get error frames / bus-off.
- A real CAN bus needs **two 120 Ω termination resistors** (one at each physical end). On a
  short bench you often need at least one; many adapters have a switchable terminator.
- A transmitter needs **at least one other node to ACK** its frames, or it retransmits and
  eventually goes bus-off. (On `vcan0` there's no ACK requirement.)

---

## 4. Choosing a USB-to-CAN adapter

**Hard requirement: it must present as a native SocketCAN device.** Avoid ELM327/“OBD
Bluetooth” dongles as the primary interface (they’re serial AT-command devices, poor for
ISO-TP/UDS timing).

| Tier | Adapter | Driver | Notes |
|---|---|---|---|
| **Dev / MVP** | **CANable 2.0** (~$50, CAN-FD) | `gs_usb` (candleLight fw) | Shows up as `can0` automatically. Recommended starting point. |
| **Production** | **PEAK PCAN-USB FD** | `peak_usb` (in-kernel) | Rock-solid timing. |
| **Production** | **Kvaser Leaf / USBcan Pro** | `kvaser_usb` (in-kernel) | Excellent driver; Pro = 2 channels. |
| **Budget 2nd ch.** | MCP2515/MCP2518FD SPI HAT | `mcp251x`/`mcp251xfd` | OK as a second channel; not for production timing. |

> **CANable variants:** CANable boards can be flashed with either **candleLight**
> (`gs_usb`, native SocketCAN — preferred) or **slcan** (serial line, needs `slcand`).
> Prefer candleLight. Check with `lsusb` (look for "OpenMoko / candleLight" or
> "STM32 ... gs_usb").

---

## 5. Bringing up a real adapter (`can0`)

### 5.1 candleLight / `gs_usb` (CANable 2.0, most PEAK/Kvaser)
Plug it in, then:

```bash
# Confirm the kernel created an interface
ip -details link show | grep -A2 can

# Classic CAN at 500 kbit/s (most powertrain buses)
sudo ip link set can0 up type can bitrate 500000

# CAN FD (nominal 500k arbitration, 2M data phase)
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on

# Bus-monitoring (listen-only: never transmits/ACKs — safe for sniffing a live vehicle)
sudo ip link set can0 up type can bitrate 500000 listen-only on
```

Bring it back down (e.g. to change bitrate):
```bash
sudo ip link set can0 down
```

Common bus speeds: **500 kbit/s** (HS-CAN powertrain), **250 kbit/s** (some body/J1939),
**125 kbit/s** (comfort/MS-CAN). Match the module.

### 5.2 slcan adapters (if your CANable runs slcan firmware)
```bash
sudo slcand -o -c -s6 /dev/ttyACM0 can0   # -s6 = 500k (see slcand -h for codes)
sudo ip link set can0 up
```

### 5.3 Make it persistent (optional, systemd-networkd)
Create `/etc/systemd/network/80-can0.network` + a `.link`/`can` config, or a simple
systemd service running the `ip link set can0 up …` command at boot. For bench use, a
shell alias or a `canup` script is usually enough.

### 5.4 Permissions
Bringing interfaces up needs root (`sudo`) or the `CAP_NET_ADMIN` capability. **Using** an
already-up interface needs no special privilege. To let your user manage CAN without sudo,
grant the capability to `ip` or run the bring-up via a small sudoers-allowed script.

---

## 6. Verifying the link with `can-utils`

Always sanity-check at the `can-utils` level before bringing in CANOPY:

```bash
candump can0                      # dump all traffic (Ctrl-C to stop)
candump -ta can0                  # with absolute timestamps
cansend can0 123#DEADBEEF         # send standard-id 0x123, payload DE AD BE EF
cansend can0 18FEF100#0102030405060708   # extended id
cangen can0 -I 200 -L 8 -g 10     # generate random traffic for testing
ip -details -statistics link show can0   # see state, bitrate, error counters, bus-off
```

If `candump` shows traffic and `cansend` is ACK’d (no error), the link is good and CANOPY
will work on that channel.

---

## 7. Wiring an adapter to a module (safely)

You need, at minimum, three connections between the adapter/bench and the module:

| Adapter / bench | Module pin (from its pinout) |
|---|---|
| **CAN-H** | module CAN-H |
| **CAN-L** | module CAN-L |
| **GND** | module ground |
| **+12 V (KL30)** from a current-limited PSU | module battery feed |
| **+12 V (KL15)** if required to wake | module ignition feed |

**Safety (protect the core and yourself):**
1. **Identify power/ground/CAN pins from a verified pinout** — use the
   [AI wiring-diagram tool](AI-VISION.md) to draft them, then **confirm with a multimeter**.
2. **Set the PSU current limit low first** (e.g. 0.2–0.5 A) before energizing; raise it once
   you see sane draw. A short shows up as an instant current-limit hit, not a fried board.
3. **Common ground**: adapter GND, PSU GND, and module GND must be tied together.
4. **Termination**: enable the adapter’s 120 Ω terminator (or add a resistor across H–L).
   With only the adapter + module you have two nodes, which is enough to ACK.
5. Keep a **hardware power cut** (the PSU output switch or an e-stop) within reach.

---

## 8. Using the CLI on real hardware

Every command takes the channel name; just use `can0` instead of `vcan0`.

```bash
# Sniff and decode against a platform DBC, logging a trace
canopy monitor can0 --dbc dbc/ford_f250_powertrain.dbc --trace --timeout 10

# Send a frame
canopy send can0 7DF 0201050000000000          # OBD-II mode 01 PID 05 (coolant temp) request

# Decode a captured trace later
canopy decode traces/2026…_monitor.blf --dbc dbc/ford_f250_powertrain.dbc
```

### 8.1 Run the "car in a box" onto a real module
Broadcast a full simulated vehicle (restbus + UDS) onto the real bus so the module wakes:

```bash
canopy sim run vehicles/ford_f250_6.7.yaml --channel can0
# → vehicle 'ford_f250_6.7' up on can0: ECUs [PCM, TCM, BCM]
#   broadcasting… Ctrl-C to stop
```

### 8.2 Act as the UDS tester against the module
In another terminal (module powered + on the bus):

```bash
canopy uds vin can0                 # read VIN (multi-frame ISO-TP)
canopy uds read-dtc can0            # read stored DTCs
canopy uds clear-dtc can0           # clear DTCs
# Non-default addressing (e.g. a body module):
canopy uds read-dtc can0 --req 0x726 --rsp 0x72E
```

> The same `uds` commands work against the **simulator** too — point one terminal’s
> `sim run` and another’s `uds` at the same channel to rehearse the whole flow before a real
> module is on the bench.

---

## 9. Two-channel setups (restbus + tester)

For realistic work you often want the simulator broadcasting on one bus while you talk to
the DUT on another (or bridge them). Two CANables give you `can0` and `can1`:

```bash
sudo ip link set can0 up type can bitrate 500000   # restbus to the DUT
sudo ip link set can1 up type can bitrate 500000   # tester / sniffer

canopy sim run vehicles/ford_f250_6.7.yaml --channel can0 &
canopy monitor can1 --dbc dbc/ford_f250_powertrain.dbc   # watch the DUT’s responses
```

A multi-channel adapter (Kvaser USBcan Pro 2xHS, PEAK PCAN-USB Pro FD) does the same with
one device and tighter timing.

---

## 10. Configuration & environment variables

All CLI channel options can also come from the environment (CLI flags win):

| Variable | Default | Meaning |
|---|---|---|
| `CANOPY_CAN_INTERFACE` | `socketcan` | python-can backend (`socketcan`, `virtual`, `pcan`, …) |
| `CANOPY_CAN_CHANNEL` | `vcan0` | Channel name (`can0`, `vcan0`, …) |
| `CANOPY_CAN_BITRATE` | `500000` | Nominal bitrate (honored by non-SocketCAN backends; SocketCAN uses `ip link`) |
| `CANOPY_CAN_FD` | `false` | Enable CAN FD frames |
| `CANOPY_CAN_DATA_BITRATE` | `2000000` | FD data-phase bitrate |
| `CANOPY_CAN_RECEIVE_OWN_MESSAGES` | `false` | Loop back own frames (keep **off** for ISO-TP/UDS) |

```bash
export CANOPY_CAN_CHANNEL=can0
canopy monitor                       # now defaults to can0
```

Database (for run logging, Phase 1): `docker compose up -d db` and
`CANOPY_DATABASE_URL=postgresql+psycopg://canopy:canopy@localhost:5432/canopy`.

---

## 11. End-to-end worked example: 2016 F-250 PCM

```bash
# 0) (once) install + bring up the adapter
sudo ip link set can0 up type can bitrate 500000

# 1) Wire PCM: CAN-H/L + GND to the adapter, KL30/KL15 from a current-limited PSU.
#    Verify power/ground pins with a meter. Set PSU limit to 0.5 A, then energize.

# 2) Confirm the bus is alive
candump can0            # you should see the PCM's own frames once it's awake

# 3) Bring up the rest of the "vehicle" so the PCM exits limp mode
canopy sim run vehicles/ford_f250_6.7.yaml --channel can0 &

# 4) Diagnose it as a tester
canopy uds vin can0
canopy uds read-dtc can0
canopy monitor can0 --dbc dbc/ford_f250_powertrain.dbc --trace --timeout 15

# 5) Stop the simulator
kill %1
```

You now have: a woken module, a decoded live trace (BLF), and its DTCs — the raw material
for a diagnosis record.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Cannot find device "can0"` | Adapter not enumerated / wrong driver | `lsusb`, `dmesg | tail`; for CANable confirm candleLight (`gs_usb`) firmware |
| `RTNETLINK answers: Operation not permitted` | Not root | Use `sudo ip link …` or grant `CAP_NET_ADMIN` |
| Interface up but **no traffic** in `candump` | Bitrate mismatch, or bus asleep | Match bitrate exactly; run `sim run` to wake the module; check wiring/termination |
| `candump` shows **error frames** / counters climbing | Bitrate mismatch or bad termination | Fix bitrate; add/enable 120 Ω termination |
| Transmit fails, adapter goes **bus-off** | No other node to ACK, or wiring | Need ≥2 nodes + termination; check `ip -details link show can0` for `BUS-OFF`, then `ip link set can0 down/up` |
| UDS calls time out | Wrong request/response IDs, or DUT not in the right session | Set `--req/--rsp`; confirm with `candump` that the ECU responds; keep `RECEIVE_OWN_MESSAGES` off |
| `RX buffer overflow` / dropped frames | Slow link (slcan) or txqueue too small | Prefer `gs_usb`; `sudo ip link set can0 txqueuelen 1000` |
| CAN FD frames rejected | Channel not FD-enabled | Bring up with `dbitrate … fd on`; pass `--fd` to CLI |
| `gs_usb` not loading | Old kernel | `sudo modprobe gs_usb`; update kernel; verify with `dmesg` on plug-in |

Diagnostics: `ip -details -statistics link show can0` shows state (ERROR-ACTIVE / WARNING /
BUS-OFF), bitrate, sample point, and error counters — your first stop for any link problem.

---

## 13. Command cheat-sheet

```bash
# --- bring-up ---
sudo ip link set can0 up type can bitrate 500000                 # classic
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on   # CAN FD
sudo ip link set can0 up type can bitrate 500000 listen-only on  # safe sniff
sudo ip link set can0 down

# --- verify (can-utils) ---
candump can0 ; cansend can0 123#DEADBEEF ; cangen can0 -I 200
ip -details -statistics link show can0

# --- CANOPY ---
canopy monitor can0 --dbc dbc/ford_f250_powertrain.dbc --trace
canopy send can0 7DF 0201050000000000
canopy decode traces/<file>.blf --dbc dbc/ford_f250_powertrain.dbc
canopy sim run vehicles/ford_f250_6.7.yaml --channel can0
canopy uds vin can0 ; canopy uds read-dtc can0 ; canopy uds clear-dtc can0
```
