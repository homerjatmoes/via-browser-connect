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
        "Unplug and replug each USB keyboard, then fully quit and reopen Chrome/Edge.",
        "Do not use Snap Chromium — it cannot open hidraw even with udev rules.",
        "",
        "Chrome authorizes each site separately. usevia.app does not cover the screen tool.",
    ]
    for name, url in WEBHID_SITES:
        lines.append(f"  {name}: {url}")
    lines.extend(
        [
            "",
            "QK108 screen still says not authorized:",
            "  The LCD page filters usagePage 0x00FF / usage 1, NOT the VIA interface.",
            "  1. USB-C into the PC (not a dock/KVM if you can avoid it).",
            "  2. Switch on the screen — key under the display, above Num Lock.",
            "     Then put it on GIF/home so the screen HID actually enumerates.",
            "  3. In the Chrome picker, pick the SCREEN / vendor HID, not Keyboard.",
            "  4. If the picker is empty: sudo chmod a+rw /dev/hidraw*  then retry.",
            "  5. chrome://device-log/  — FILE_ERROR_ACCESS_DENIED means udev/Snap.",
            "  6. Still dead: hold Esc, plug USB-C, wait ~5 min (screen MCU firmware).",
            "",
            "lsusb should show 36b0:30af and sometimes a second 36b0:30ee.",
        ]
    )
    return "\n".join(lines)
