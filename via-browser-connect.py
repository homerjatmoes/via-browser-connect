#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""VIA Browser Connect — pick USB keyboards and grant Chromium-based web browsers WebHID access on Linux.

Copy this one file anywhere. On first run it pulls the helper modules next to
itself from GitHub if they are missing.

Usage:
    python3 via-browser-connect.py
    python3 via-browser-connect.py --cli
    python3 via-browser-connect.py --scan
    python3 via-browser-connect.py --install-menu
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

_HERE = Path(__file__).resolve().parent
_HELPERS = ("vbc_devices.py", "vbc_rules.py", "vbc_cli.py", "vbc_gui.py", "vbc_desktop.py")
_RAW = "https://raw.githubusercontent.com/homerjatmoes/via-browser-connect/main/"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


def _ensure_helpers() -> None:
    missing = [name for name in _HELPERS if not (_HERE / name).is_file()]
    if not missing:
        return
    print("Fetching helper files from GitHub:", ", ".join(missing), file=sys.stderr)
    try:
        from urllib.request import urlretrieve
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(f"Cannot download helpers: {exc}") from exc
    for name in missing:
        dest = _HERE / name
        try:
            urlretrieve(_RAW + name, dest)
        except Exception as exc:
            sys.stderr.write(
                f"Could not download {name}: {exc}\n\n"
                "Clone the repo instead:\n"
                "  git clone https://github.com/homerjatmoes/via-browser-connect.git\n"
                "  cd via-browser-connect\n"
                "  python3 via-browser-connect.py\n"
            )
            raise SystemExit(1) from exc


_ensure_helpers()

try:
    from vbc_cli import run_cli
    from vbc_desktop import install_app_menu, remove_app_menu
    from vbc_gui import run_gui
except ModuleNotFoundError:
    sys.stderr.write(
        "Missing helper files (vbc_cli.py and friends).\n"
        "Clone the repo:\n"
        "  git clone https://github.com/homerjatmoes/via-browser-connect.git\n"
        "  cd via-browser-connect\n"
        "  python3 via-browser-connect.py\n"
    )
    raise SystemExit(1)


def has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enable USB keyboards for a Chromium-based web browser (WebHID)."
    )
    parser.add_argument("--cli", action="store_true", help="Use the numbered prompt")
    parser.add_argument("--scan", action="store_true", help="List USB devices and exit")
    parser.add_argument("--all", action="store_true", help="Allow every hidraw device")
    parser.add_argument("--no-bootloaders", action="store_true", help="Skip QMK flashing rules")
    parser.add_argument("--dry-run", action="store_true", help="Print rules without installing")
    parser.add_argument(
        "--install-menu",
        action="store_true",
        help="Install a .desktop launcher for GNOME, KDE, XFCE, and other XDG desktops",
    )
    parser.add_argument("--remove-menu", action="store_true", help="Remove the application-menu launcher")
    args = parser.parse_args(argv)

    if args.install_menu:
        path = install_app_menu()
        print(f"Installed {path}")
        print("Search your application menu for VIA Browser Connect.")
        return 0
    if args.remove_menu:
        remove_app_menu()
        print("Removed the application-menu launcher.")
        return 0

    if sys.platform != "linux" and not args.scan and not args.dry_run:
        print(
            "udev rules are a Linux feature. On macOS, grant the keyboard in the Chromium-based web browser picker. "
            "On Windows, WebHID in a Chromium-based web browser usually works without extra drivers; use Zadig only for flashing.",
            file=sys.stderr,
        )

    if args.scan or args.cli or args.dry_run or not has_display():
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    sys.exit(main())
