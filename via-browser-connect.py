#!/usr/bin/env python3
"""VIA Browser Connect — pick USB keyboards and grant Chrome WebHID access on Linux.

Usage:
    python3 via-browser-connect.py
    python3 via-browser-connect.py --cli
    python3 via-browser-connect.py --scan
    python3 via-browser-connect.py --all
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from vbc_cli import run_cli
from vbc_gui import run_gui


def has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Enable USB keyboards for Chrome WebHID.")
    parser.add_argument("--cli", action="store_true", help="Use the numbered prompt")
    parser.add_argument("--scan", action="store_true", help="List USB devices and exit")
    parser.add_argument("--all", action="store_true", help="Allow every hidraw device")
    parser.add_argument("--no-bootloaders", action="store_true", help="Skip QMK flashing rules")
    parser.add_argument("--dry-run", action="store_true", help="Print rules without installing")
    args = parser.parse_args(argv)

    if sys.platform != "linux" and not args.scan and not args.dry_run:
        print(
            "udev rules are a Linux feature. On macOS, grant the keyboard in the Chrome picker. "
            "On Windows, Chrome WebHID usually works without extra drivers; use Zadig only for flashing.",
            file=sys.stderr,
        )

    if args.scan or args.cli or args.dry_run or not has_display():
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    sys.exit(main())
