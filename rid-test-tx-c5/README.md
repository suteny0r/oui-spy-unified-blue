# Remote ID Test Transmitter - XIAO ESP32-C5

## DISCLAIMER

**THIS SOFTWARE IS PROVIDED FOR AUTHORIZED TESTING AND DEVELOPMENT PURPOSES ONLY.**

This firmware transmits simulated Open Drone ID (ODID) broadcasts on 5GHz Wi-Fi (UNII-3) channels. It is intended **exclusively** for bench-testing and validating Remote ID detection firmware in a controlled lab environment.

**By using this software, you acknowledge and agree that:**

- Transmitting fake or spoofed Remote ID signals **may violate federal, state, and local laws**, including but not limited to FAA regulations (14 CFR Part 89), FCC regulations, and laws governing the operation of unmanned aircraft systems (UAS).
- You are **solely responsible** for ensuring compliance with all applicable laws and regulations in your jurisdiction before operating this device.
- This tool must **never** be used to interfere with, impersonate, or disrupt legitimate drone operations or Remote ID systems.
- The authors and contributors accept **no liability** for any misuse, legal consequences, or damages arising from the use of this software.
- This is a **development and QA tool** -- not a product, not a toy, not a weapon.

**If you are unsure whether using this tool is legal in your area, do not use it.**

---

## What It Does

- Generates a **random drone identity** (serial number, operator ID, MAC address) at boot
- Simulates a **circular flight path** (~220m radius, 60s orbit, ~100m altitude) at a random location in the continental US
- Broadcasts **ODID-compliant NAN Action Frames** on 5GHz UNII-3 channels (149, 153, 157, 161, 165)
- Rotates channels each transmission, 4 broadcasts per second
- Plays a short beep once per second to confirm operation
- Logs TX status over USB serial at 115200 baud

## Hardware

- XIAO ESP32-C5
- Buzzer on GPIO25 (D2)

## Build & Flash

```bash
# Build
pio run

# Flash
pio run -t upload

# Monitor serial output
pio device monitor
```

## Notes

- Each power cycle generates a **new random drone** at a **new random location**
- Frame format uses the official ODID library (`odid_wifi_build_message_pack_nan_action_frame`) to guarantee compatibility with any compliant receiver
- Designed to validate OUI Spy Sky Spy and other detection firmwares on 5GHz
