from __future__ import annotations

import sys
from typing import List, Sequence

from vbc_devices import UsbDevice, scan_devices
from vbc_rules import RULES_PATH, apply_rules, build_rules
from vbc_sites import after_install_text


def parse_selection(text: str, count: int) -> List[int]:
    text = text.strip().lower()
    if text in {"all", "a", "*"}:
        return list(range(count))
    if text in {"none", "n", ""}:
        return []
    chosen: List[int] = []
    for chunk in text.replace(" ", "").split(","):
        if not chunk:
            continue
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1)
            start, end = int(start_s), int(end_s)
            chosen.extend(range(start, end + 1))
        else:
            chosen.append(int(chunk))
    return [i - 1 for i in chosen if 1 <= i <= count]


def print_devices(devices: Sequence[UsbDevice]) -> None:
    if not devices:
        print("No USB devices found. Plug a keyboard in and retry.")
        return
    print()
    print("  #  Kind  Vendor:Product  Device")
    print("  -  ----  --------------  ------")
    for i, d in enumerate(devices, start=1):
        mark = "*" if d.kind == "HID" else " "
        print(f" {i:2d}{mark} {d.kind:<4} {d.ident:<14} {d.label}")
    print()
    print("  * = HID interface (typical VIA / Vial / QMK / screen-tool target)")
    print()


def run_cli(args) -> int:
    devices = scan_devices()
    if args.scan:
        print_devices(devices)
        return 0
    if not devices and not args.all:
        print("No USB devices found.")
        return 1
    print("VIA Browser Connect — enable USB keyboards for a Chromium-based web browser (WebHID)")
    print("USB cable recommended. 2.4G may work with VIA; results will vary.")
    print_devices(devices)
    if args.all:
        for d in devices:
            d.selected = True
        all_hidraw = True
    else:
        default = ",".join(
            str(i) for i, d in enumerate(devices, start=1) if d.kind == "HID"
        ) or "all"
        raw = input(f"Select devices (e.g. 1,2 or all) [{default}]: ").strip()
        if not raw:
            raw = default
        try:
            indexes = parse_selection(raw, len(devices))
        except ValueError:
            print("Could not parse that selection.")
            return 2
        for i, d in enumerate(devices):
            d.selected = i in indexes
        all_hidraw = args.all
    include_bl = not args.no_bootloaders
    rules = build_rules(devices, all_hidraw=all_hidraw, include_bootloaders=include_bl)
    print("---- udev rules ----")
    print(rules)
    if args.dry_run:
        return 0
    confirm = input(f"Write {RULES_PATH} with sudo/pkexec? [Y/n]: ").strip().lower()
    if confirm in {"n", "no"}:
        print("Left rules unwritten.")
        return 0
    try:
        apply_rules(rules)
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1
    print()
    print(f"Installed {RULES_PATH}")
    print(after_install_text())
    return 0
