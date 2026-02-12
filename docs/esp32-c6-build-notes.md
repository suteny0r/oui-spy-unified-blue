# ESP32-C6 Build Notes

## Overview

Added a standalone Flock-You build for the **Seeed Studio XIAO ESP32-C6**, running alongside the existing XIAO ESP32-S3 unified build. The C6 runs Flock-You only (no selector UI, no other modes).

## Hardware: XIAO ESP32-C6

- **Chip:** ESP32-C6FH4 (RISC-V, 160MHz, 4MB flash, 512KB SRAM, no PSRAM)
- **Wireless:** WiFi 6 (802.11ax), BLE 5.3, IEEE 802.15.4
- **Antenna:** Built-in ceramic antenna (default). External UFL connector available — GPIO14 controls RF switch (LOW = internal, HIGH = external).
- **No onboard WS2812/NeoPixel** (unlike some other XIAO boards)
- **Built-in LED:** GPIO15 (active LOW)
- **Boot button:** GPIO9

## GPIO Mapping (C6 vs S3)

| Function | S3 GPIO | C6 GPIO | Notes |
|----------|---------|---------|-------|
| Buzzer | 3 | 2 (D2) | GPIO3 is antenna control on C6 |
| Built-in LED | 21 | 15 | Both active LOW |
| Boot Button | 0 | 9 | |
| NeoPixel (external) | 4 | 1 (D1) | C6 has no onboard NeoPixel; wire a WS2812 to D1 |
| Antenna Switch | N/A | 14 | LOW=internal, HIGH=external |

## Build Commands

```bash
# Build C6 firmware
pio run -e xiao_esp32c6_flockyou

# Build S3 firmware (unchanged)
pio run -e seeed_xiao_esp32s3

# Flash C6 via esptool (PlatformIO upload has issues with pioarduino on Windows)
esptool --chip esp32c6 --port COM17 --baud 921600 write_flash --flash_mode dio --flash_size 4MB 0x0 .pio/build/xiao_esp32c6_flockyou/bootloader.bin 0x8000 .pio/build/xiao_esp32c6_flockyou/partitions.bin 0x10000 .pio/build/xiao_esp32c6_flockyou/firmware.bin
```

## Key Technical Decisions

### Platform: pioarduino fork
The official `espressif32` PlatformIO platform (v6.x) does not support ESP32-C6. The C6 requires arduino-esp32 3.x, which is only available via the **pioarduino** community fork:
```
platform = https://github.com/pioarduino/platform-espressif32/releases/download/stable/platform-espressif32.zip
```

### NimBLE 1.4 vs 2.x
The S3 uses NimBLE-Arduino 1.4.x. The C6 requires NimBLE-Arduino 2.x. API differences are handled with `#ifdef CONFIG_IDF_TARGET_ESP32C6` guards:

| NimBLE 1.4.x (S3) | NimBLE 2.x (C6) |
|---|---|
| `NimBLEAdvertisedDeviceCallbacks` | `NimBLEScanCallbacks` |
| `void onResult(NimBLEAdvertisedDevice* dev)` | `void onResult(const NimBLEAdvertisedDevice* dev)` |
| `setAdvertisedDeviceCallbacks(cb)` | `setScanCallbacks(cb)` |
| `checkRavenUUID(NimBLEAdvertisedDevice*)` | `checkRavenUUID(const NimBLEAdvertisedDevice*)` |

### ESPAsyncWebServer version
ESPAsyncWebServer 3.0.6 (PlatformIO registry) crashes on ESP-IDF 5.x (used by C6) with `tcp_alloc` assertion failure — it doesn't hold the lwIP TCPIP core lock. Fixed by pulling directly from GitHub which provides v3.6.0+:
```
lib_deps = https://github.com/mathieucarbou/ESPAsyncWebServer.git
```

### Toolchain workarounds (Windows)
pioarduino's custom registry packages for toolchain and esptool are empty stubs (metadata only, no binaries). Fixed by overriding with standard PlatformIO registry packages:
```ini
platform_packages =
    platformio/toolchain-riscv32-esp
    platformio/tool-esptoolpy
```

### Framework package conflicts
The S3 (espressif32 6.x) and C6 (pioarduino 55.x) share the same `framework-arduinoespressif32` package directory but need different versions (3.0.5 vs 3.3.6). Building one target can overwrite the other's framework. If builds fail with `FRAMEWORK_DIR is None`, the framework may need reinstalling. Download from:
```
https://github.com/espressif/arduino-esp32/releases/download/3.3.6/esp32-core-3.3.6.tar.xz
```
Extract to `~/.platformio/packages/framework-arduinoespressif32/`.

## Files Added/Modified

### New files
- `partitions_c6.csv` — 4MB partition table (~3MB app, ~960KB SPIFFS)
- `src/main_c6_flockyou.cpp` — Standalone entry point (calls `flockyou_setup()`/`flockyou_loop()`)

### Modified files
- `platformio.ini` — Added `[env:xiao_esp32c6_flockyou]` section; added `-<main_c6_flockyou.cpp>` to S3 src_filter
- `src/raw/flockyou.cpp` — NimBLE 2.x compat guards, `#ifndef BUZZER_PIN` guard, built-in LED support (`FLOCKYOU_LED_PIN`), optional NeoPixel support (`FLOCKYOU_NEOPIXEL`)
- `src/mode_flockyou.cpp` — Conditional `#include <Adafruit_NeoPixel.h>`

## LED Indicators

### Built-in LED (GPIO15) — always active on C6
| State | Behavior |
|-------|----------|
| Boot | 3 quick blinks |
| Idle scanning | Off |
| Device nearby | Slow blink (500ms on/off) |
| New detection | Rapid blink for 1.5s |

### External NeoPixel (GPIO1/D1) — requires wiring a WS2812 to D1
| State | Behavior |
|-------|----------|
| Boot | Pink flash, purple flash, off |
| Idle scanning | Dim purple breathing |
| Device nearby | Pink pulse |
| New detection | Hot pink strobe for 1.5s |

#### Wiring a WS2812 breakout to the C6
| WS2812 Pin | XIAO C6 Pin |
|---|---|
| VIN / 5V | 3.3V |
| GND | GND |
| DIN | D1 |
| DOUT | Not connected |

WS2812B is rated for 5V but works at 3.3V (slightly dimmer). Leave DOUT unconnected.

## Buzzer

Connect a passive piezo buzzer:
- **+** to D2 (GPIO2)
- **-** to GND

Compatible: 3V-12V passive piezo buzzers (e.g., 42 ohm, 12mm).

## Build Sizes (as of initial commit)

| Target | Flash | RAM |
|--------|-------|-----|
| C6 (Flock-You only) | 1.41MB (44.9% of 3MB) | 77KB (23.7%) |
| S3 (all modes) | 1.18MB (18.7% of 6MB) | 83KB (25.3%) |
