# Digital logic and interface IC diagnosis

> tags: digital, logic, spi, i2c, uart, level-shifter, optocoupler, buffer, isolator, interface

Digital failures often look like “bad firmware” until the physical electrical layer is checked. Treat every digital interface as rails, ground reference, idle state, pull-ups, signal activity, and loading.

## Common digital interface parts
- Level shifters between 5 V and 3.3 V domains.
- Buffers, gates, latches, and bus switches.
- Optocouplers and digital isolators between hazardous/dirty domains and logic.
- EEPROM/Flash, ADCs, sensor ASICs, display drivers, and gate drivers on SPI/I2C/UART.
- Pull-up/pull-down resistor networks and ESD diode arrays.

## I2C checks
- SDA and SCL idle high through pull-ups.
- A stuck-low line can be a shorted device, missing pull-up rail, MCU pin fault, or device holding the bus after a failed transaction.
- Check pull-up voltage and resistance. Wrong pull-up value can make edges too slow or load devices.
- Scope for clean transitions and ACK behavior; a logic analyzer is useful only after voltage levels are known.

## SPI checks
- Identify SCLK, MOSI, MISO, chip select, and device supply.
- Chip select should toggle only for the selected device. A stuck chip select can make a shared MISO line look shorted.
- MISO stuck high/low can be a dead peripheral, bus contention, wrong supply, or ESD-damaged pin.
- Verify clock polarity/phase only after physical levels and wiring are correct.

## UART and single-ended logic
- Idle is typically high for TTL UART, but confirm voltage level.
- A TX line stuck low can prevent boot messages or jam a transceiver.
- Do not connect RS-232 voltage levels directly to TTL UART pins.

## Optocouplers and isolators
- Check input LED forward drop/current and output-side supply/pull-up.
- Aging optocouplers can become slow or weak, especially in hot power supplies.
- Digital isolators need both side supplies. Missing isolated supply makes the logic appear dead.

## Comparative channel method
- On multi-channel boards, compare suspect channel diode-mode readings to known-good channels.
- Compare waveforms at the same state and load.
- A single channel with different clamp-diode reading, hot input IC, or missing pull-up is a strong suspect.

Sources: [Fluke diode testing](https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-test-diodes), [Keysight oscilloscope probing](https://prc.keysight.com/Content/PDF_Files/5989-7894EN.pdf), [Microchip power-up troubleshooting](https://ww1.microchip.com/downloads/en/Appnotes/00000607C.pdf), [Renesas watchdog overview](https://renesas.github.io/fsp/group___w_d_t.html).
