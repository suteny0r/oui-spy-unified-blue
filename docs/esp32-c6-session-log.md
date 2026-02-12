# ESP32-C6 Build Session Log

Chronological record of prompts, problems, and solutions from the build session.

---

## 1. Initial Request
**Prompt:** Implement a plan to add an ESP32-C6 build target for Flock-You.

**Actions:**
- Created `partitions_c6.csv` (4MB partition table)
- Created `src/main_c6_flockyou.cpp` (standalone entry point)
- Modified `src/raw/flockyou.cpp` (NimBLE 2.x compat, BUZZER_PIN guard)
- Modified `platformio.ini` (added C6 environment)

---

## 2. Build Error: Multiple definition of setup()/loop()
**Problem:** S3 build failed — `main_c6_flockyou.cpp` compiled alongside `main.cpp`, causing duplicate `setup()`/`loop()`.

**Fix:** Added `-<main_c6_flockyou.cpp>` to S3's `src_filter`.

---

## 3. Build Error: Unknown board ID
**Problem:** pioarduino tag 51.03.07 didn't include `seeed_xiao_esp32c6`.

**Fix:** Changed platform URL to `stable` release (version 55.3.36).

---

## 4. Build Error: FRAMEWORK_DIR is None
**Problem:** pioarduino couldn't find `framework-arduinoespressif32`.

**Fix:** The stable URL auto-downloads the framework (3.3.6). This issue recurs when the S3 build overwrites the framework with version 3.0.5.

---

## 5. Build Error: riscv32-esp-elf-g++ not found
**Problem:** pioarduino's custom toolchain package from its registry contained only metadata (package.json, tools.json), no binaries.

**Fix:** Added `platformio/toolchain-riscv32-esp` to `platform_packages` to force standard PlatformIO registry toolchain.

---

## 6. Build Error: BOOT_PIN macro conflict
**Problem:** `-DBOOT_PIN=9` in build flags conflicted with Arduino framework's built-in `static const uint8_t BOOT_PIN = 9;`.

**Fix:** Removed BOOT_PIN, LED_PIN, NEOPIXEL_PIN from build flags — not needed by flockyou.cpp.

---

## 7. Build Error: esptool ModuleNotFoundError
**Problem:** pioarduino's `tool-esptoolpy` was also an empty stub.

**Fix:** Added `platformio/tool-esptoolpy` to `platform_packages`. Also had to fix PlatformIO's Python venv broken editable esptool install.

---

## 8. Both Builds Succeeded
- S3: 1.18MB flash
- C6: 1.40MB flash

---

## 9. Flashing
**Prompt:** Is `pio run -t upload` enough for a new board?

**Answer:** Yes, for a new board that's enough. No separate bootloader/filesystem upload needed — esptool writes bootloader + partitions + firmware.

---

## 10. PlatformIO Upload Failed on User's Machine
**Problem:** FRAMEWORK_DIR None error on user's machine (different cached platform instance).

**Fix:** Used esptool directly:
```
esptool --chip esp32c6 --port COM17 --baud 921600 write_flash --flash_mode dio --flash_size 4MB 0x0 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin
```

---

## 11. Boot Loop: tcp_alloc Assertion
**Problem:** `assert failed: tcp_alloc ... Required to lock TCPIP core functionality!` — repeated crash on boot.

**Root cause:** ESPAsyncWebServer 3.0.6 doesn't hold lwIP TCPIP core lock when creating TCP sockets. ESP-IDF 5.5 (used by C6) enforces this.

**Fix:** Changed lib_deps from `mathieucarbou/ESP Async WebServer@^3.0.6` to `https://github.com/mathieucarbou/ESPAsyncWebServer.git` (pulled v3.6.0 with the fix).

---

## 12. Successful Boot
Device booted correctly. BLE scanning, WiFi AP, and web dashboard all working.

---

## 13. Antenna Question
**Prompt:** Does the C6 have an internal antenna? Do I need the external antenna connector?

**Answer:** Yes, built-in ceramic antenna is the default. GPIO14 controls RF switch (LOW=internal, HIGH=external). No changes needed.

---

## 14. Buzzer Setup
**Prompt:** How to connect a buzzer using a breadboard?

**Answer:** Passive piezo buzzer: + to D2, - to GND.

---

## 15. Buzzer Compatibility Check
**Prompt:** Will this Amazon buzzer work? (passive, 42 ohm, 3V-12V, 12mm)

**Answer:** Yes, compatible.

---

## 16. LED/NeoPixel Question
**Prompt:** I saw mention of an LED in the OUI-SPY code. What was it and can I add it to the C6?

**Answer:** The S3 build uses a NeoPixel (WS2812) on GPIO4 in detector mode. Initially stated (incorrectly) that the C6 had a built-in WS2812 on GPIO8.

---

## 17. NeoPixel Integration (Started)
**Prompt:** Add NeoPixel support to the Flock-You C6 build.

**Actions:** Added `#ifdef FLOCKYOU_NEOPIXEL` guarded code with RGB animation functions.

---

## 18. Verification Challenge
**Prompt:** There is no visible LED that you activated. Show me manufacturer documentation.

**Finding:** Seeed Wiki confirmed: **No built-in WS2812 on the C6.** The C6 has a plain LED on GPIO15, not a NeoPixel on GPIO8. The initial claim was wrong.

**Correction:** Changed approach to use both:
1. Built-in LED on GPIO15 (active LOW, on/off only)
2. External WS2812 NeoPixel wired to D1/GPIO1 (optional)

---

## 19. Both LEDs Implementation
**Prompt:** Use both the built-in LED and an external NeoPixel.

**Actions:**
- Added `FLOCKYOU_LED_PIN` code (GPIO15, active LOW, blink patterns)
- Changed `FLOCKYOU_NEOPIXEL` from GPIO8 to GPIO1 (D1)
- Added `-DFLOCKYOU_LED_PIN=15` to build flags
- Both builds succeeded, flashed to C6, boot blink confirmed

---

## 20. NeoPixel Breakout Compatibility
**Prompt:** Would this WS2812 breakout board work for breadboard use?

**Answer:** Yes — 5-pack WS2812B breakout boards with through-holes. Wire VIN→3.3V, GND→GND, DIN→D1.

---

## 21. Commit
**Prompt:** Save everything.

**Actions:** Committed all changes as `91e3c87` on master (not pushed).
