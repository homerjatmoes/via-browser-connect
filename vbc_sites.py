"""WebHID sites that need their own Chrome authorization."""

from __future__ import annotations

WEBHID_SITES = (
    ("VIA", "https://usevia.app"),
    ("Vial", "https://vial.rocks"),
    ("EPOMAKER LCD Screen Driver", "https://image.rdmctmzt.com/"),
    ("EPOMAKER Hub", "https://hub.epomaker.com"),
)


def after_install_text() -> str:
    lines = [
        "Unplug and replug each USB keyboard, then fully quit and reopen the Chromium-based web browser.",
        "Snap Chrome often ignores udev — use a .deb or distro package.",
        "",
        "Chrome authorizes each site separately. A grant on usevia.app does not cover the screen tool.",
    ]
    for name, url in WEBHID_SITES:
        lines.append(f"  {name}: {url}")
    lines.extend(
        [
            "",
            "QK108 clock / GIFs:",
            "  1. USB-C cable (not 2.4G / Bluetooth).",
            "  2. Turn the screen on (dedicated key under the display, above Num Lock).",
            "  3. Open https://image.rdmctmzt.com/ in Chrome or Edge.",
            "  4. Connect Device → pick the QK108 HID → Allow.",
            "  Connecting usually syncs date and time from the PC.",
            "",
            "If the picker is empty or open fails, check chrome://device-log/",
        ]
    )
    return "\n".join(lines)
