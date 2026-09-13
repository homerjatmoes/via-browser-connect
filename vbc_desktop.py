from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_ID = "via-browser-connect"
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<rect width="32" height="32" rx="6" fill="#1c1b1a"/>
<rect x="5" y="9" width="22" height="14" rx="2.5" fill="none" stroke="#e8c4b8" stroke-width="1.6"/>
<rect x="8" y="12" width="2.4" height="2.4" rx="0.4" fill="#e8c4b8"/>
<rect x="11.8" y="12" width="2.4" height="2.4" rx="0.4" fill="#e8c4b8"/>
<rect x="15.6" y="12" width="2.4" height="2.4" rx="0.4" fill="#e8c4b8"/>
<rect x="19.4" y="12" width="2.4" height="2.4" rx="0.4" fill="#e8c4b8"/>
<rect x="8" y="16.4" width="16" height="3.2" rx="0.5" fill="#f1ebe0"/>
</svg>
"""


def _desktop_quote(value: str) -> str:
    if not any(ch in value for ch in ' \t"'):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _xdg_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def desktop_paths():
    data = _xdg_home()
    return (
        data / "applications" / f"{APP_ID}.desktop",
        data / "icons" / "hicolor" / "scalable" / "apps" / f"{APP_ID}.svg",
    )


def launcher_script() -> Path:
    here = Path(__file__).resolve().parent
    candidate = here / "via-browser-connect.py"
    return candidate if candidate.is_file() else Path(__file__).resolve()


def install_app_menu() -> Path:
    script = launcher_script()
    python = sys.executable or "python3"
    desktop_path, icon_path = desktop_paths()
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    desktop_path.parent.mkdir(parents=True, exist_ok=True)
    icon_path.write_text(ICON_SVG.strip() + "\n", encoding="utf-8")
    desktop_path.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Version=1.0",
                "Type=Application",
                "Name=VIA Browser Connect",
                "GenericName=Keyboard WebHID helper",
                "Comment=Enable USB keyboards for VIA, Vial, and Keychron Launcher. USB cable recommended.",
                f"Exec={_desktop_quote(python)} {_desktop_quote(str(script))}",
                f"Path={script.parent}",
                f"Icon={APP_ID}",
                "Terminal=false",
                "StartupNotify=true",
                "StartupWMClass=VIA Browser Connect",
                "Categories=Settings;HardwareSettings;Utility;",
                "Keywords=VIA;Vial;QMK;keyboard;udev;HID;WebHID;",
                "",
            ]
        ),
        encoding="utf-8",
    )
    os.chmod(desktop_path, 0o644)
    db = shutil.which("update-desktop-database")
    if db:
        subprocess.run([db, str(desktop_path.parent)], check=False, capture_output=True)
    return desktop_path


def remove_app_menu() -> None:
    desktop_path, icon_path = desktop_paths()
    for path in (desktop_path, icon_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    db = shutil.which("update-desktop-database")
    if db:
        subprocess.run([db, str(desktop_path.parent)], check=False, capture_output=True)
