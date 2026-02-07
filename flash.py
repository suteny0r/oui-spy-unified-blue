#!/usr/bin/env python3
"""
OUI Spy Unified Blue — Firmware Flasher

Drop your .bin in the firmware/ folder (or pass a path), plug in your
XIAO ESP32-S3, and run:

    python flash.py

That's it.

Requirements:  pip install esptool
"""

import glob
import os
import sys
import subprocess
import serial.tools.list_ports

# ── Config ───────────────────────────────────────────────────────────────
APP_OFFSET    = "0x10000"
BAUD          = "921600"
CHIP          = "esp32s3"
FIRMWARE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firmware")

# Known USB VID:PID pairs for ESP32-S3 / common UART bridges
ESP_VIDS = {
    "303A",  # Espressif USB JTAG/serial
    "1A86",  # CH340/CH341
    "10C4",  # CP210x
    "0403",  # FTDI
}


def find_port():
    """Auto-detect the ESP32 serial port."""
    ports = serial.tools.list_ports.comports()
    candidates = []
    for p in ports:
        vid = f"{p.vid:04X}" if p.vid else ""
        if vid in ESP_VIDS:
            candidates.append(p)
        elif "esp" in (p.description or "").lower():
            candidates.append(p)
        elif "usbmodem" in (p.device or "").lower():
            candidates.append(p)
        elif "usbserial" in (p.device or "").lower():
            candidates.append(p)
        elif "ttyACM" in (p.device or ""):
            candidates.append(p)
        elif "ttyUSB" in (p.device or ""):
            candidates.append(p)
    if len(candidates) == 1:
        return candidates[0].device
    if len(candidates) > 1:
        print("\n  Multiple serial ports found:\n")
        for i, p in enumerate(candidates):
            desc = p.description or "unknown"
            print(f"    [{i + 1}] {p.device}  ({desc})")
        print()
        while True:
            try:
                choice = input("  Pick a port [1]: ").strip()
                idx = int(choice) - 1 if choice else 0
                if 0 <= idx < len(candidates):
                    return candidates[idx].device
            except (ValueError, IndexError):
                pass
            print("  Invalid choice, try again.")
    return None


def find_firmware(path_arg=None):
    """Locate the .bin file to flash."""
    # Explicit path from CLI
    if path_arg:
        if os.path.isfile(path_arg):
            return os.path.abspath(path_arg)
        print(f"\n  File not found: {path_arg}")
        sys.exit(1)

    # Look in firmware/ folder
    if os.path.isdir(FIRMWARE_DIR):
        bins = sorted(glob.glob(os.path.join(FIRMWARE_DIR, "*.bin")), key=os.path.getmtime, reverse=True)
        if len(bins) == 1:
            return bins[0]
        if len(bins) > 1:
            print("\n  Multiple .bin files found:\n")
            for i, b in enumerate(bins):
                size = os.path.getsize(b) / 1024
                print(f"    [{i + 1}] {os.path.basename(b)}  ({size:.0f} KB)")
            print()
            while True:
                try:
                    choice = input("  Pick a firmware [1]: ").strip()
                    idx = int(choice) - 1 if choice else 0
                    if 0 <= idx < len(bins):
                        return bins[idx]
                except (ValueError, IndexError):
                    pass
                print("  Invalid choice, try again.")

    # Check current directory
    bins = sorted(glob.glob("*.bin"), key=os.path.getmtime, reverse=True)
    if bins:
        return os.path.abspath(bins[0])

    return None


def flash(port, firmware):
    """Flash the firmware using esptool."""
    size_kb = os.path.getsize(firmware) / 1024
    print(f"""
  ╔══════════════════════════════════════════╗
  ║   OUI Spy Unified Blue — Flasher        ║
  ╚══════════════════════════════════════════╝

  Port:       {port}
  Firmware:   {os.path.basename(firmware)}  ({size_kb:.0f} KB)
  Chip:       {CHIP}
  Offset:     {APP_OFFSET}
  Baud:       {BAUD}
""")

    confirm = input("  Flash? [Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("  Aborted.")
        sys.exit(0)

    print("\n  Flashing...\n")

    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP,
        "--port", port,
        "--baud", BAUD,
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash",
        "-z",
        "--flash_mode", "qio",
        "--flash_freq", "80m",
        "--flash_size", "detect",
        APP_OFFSET, firmware,
    ]

    try:
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print("\n  Done! Device will reboot into the new firmware.\n")
        else:
            print(f"\n  esptool exited with code {result.returncode}")
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("  esptool not found. Install it:\n")
        print("    pip install esptool\n")
        sys.exit(1)


def erase(port):
    """Full flash erase."""
    print(f"\n  Erasing flash on {port}...\n")
    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP,
        "--port", port,
        "--baud", BAUD,
        "erase_flash",
    ]
    subprocess.run(cmd)
    print()


def main():
    # Parse args
    args = sys.argv[1:]
    do_erase = "--erase" in args
    bin_path = None

    for a in args:
        if a == "--erase":
            continue
        if a in ("-h", "--help"):
            print("""
  Usage:  python flash.py [firmware.bin] [--erase]

  Options:
    firmware.bin   Path to .bin file (auto-detects from firmware/ folder)
    --erase        Erase entire flash before writing

  Setup:
    pip install esptool pyserial
    mkdir firmware
    # drop your .bin in firmware/
    python flash.py
""")
            sys.exit(0)
        bin_path = a

    # Check esptool is installed
    try:
        subprocess.run([sys.executable, "-m", "esptool", "version"],
                       capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n  esptool not found. Install it:\n")
        print("    pip install esptool\n")
        sys.exit(1)

    # Find port
    port = find_port()
    if not port:
        print("\n  No ESP32 detected. Is the board plugged in?")
        print("  Make sure drivers are installed (CH340/CP210x).\n")
        sys.exit(1)

    print(f"  Found: {port}")

    # Erase if requested
    if do_erase:
        erase(port)

    # Find firmware
    firmware = find_firmware(bin_path)
    if not firmware:
        print(f"\n  No .bin file found.")
        print(f"  Drop your firmware in:  {FIRMWARE_DIR}/")
        print(f"  Or pass it directly:    python flash.py my_firmware.bin\n")
        sys.exit(1)

    # Flash
    flash(port, firmware)


if __name__ == "__main__":
    main()
