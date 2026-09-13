from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Iterable

from vbc_devices import UsbDevice

RULES_PATH = "/etc/udev/rules.d/70-via-browser-connect.rules"

QMK_BOOTLOADER_RULES = """# QMK flashing (DFU, Caterina, STM32, RP2040, APM32)
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"03eb\", ATTRS{idProduct}==\"2ff4\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"03eb\", ATTRS{idProduct}==\"2ff0\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"2341\", ATTRS{idProduct}==\"0036\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"1b4f\", ATTRS{idProduct}==\"9203\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"1b4f\", ATTRS{idProduct}==\"9205\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"0483\", ATTRS{idProduct}==\"df11\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"2e8a\", ATTRS{idProduct}==\"0003\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
SUBSYSTEMS==\"usb\", ATTRS{idVendor}==\"314b\", ATTRS{idProduct}==\"0106\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
KERNEL==\"hidraw*\", SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"03eb\", ATTRS{idProduct}==\"2067\", MODE=\"0660\", TAG+=\"uaccess\", TAG+=\"udev-acl\"
"""


def build_rules(
    devices: Iterable[UsbDevice],
    *,
    all_hidraw: bool = False,
    include_bootloaders: bool = True,
) -> str:
    lines = [
        "# VIA Browser Connect — Chrome WebHID / VIA / Vial / Keychron Launcher",
        f"# Install as {RULES_PATH}",
        "# Filename must sort before 73-seat-late.rules so TAG+=uaccess is honored.",
        "",
    ]
    if all_hidraw:
        lines.append("# Every hidraw node")
        lines.append(
            'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666", '
            'TAG+="uaccess", TAG+="udev-acl"'
        )
        lines.append("")
    else:
        selected = [d for d in devices if d.selected]
        if not selected:
            lines.append("# No keyboards selected.")
            lines.append("")
        for d in selected:
            pid_match = (
                ""
                if d.product_id in {"0000", "0"}
                else f', ATTRS{{idProduct}}=="{d.product_id}"'
            )
            lines.append(f"# {d.label} ({d.ident})")
            lines.append(
                'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", '
                f'ATTRS{{idVendor}}=="{d.vendor_id}"{pid_match}, '
                'MODE="0666", TAG+="uaccess", TAG+="udev-acl"'
            )
            lines.append(
                'SUBSYSTEM=="usb", '
                f'ATTRS{{idVendor}}=="{d.vendor_id}"{pid_match}, '
                'MODE="0666", TAG+="uaccess", TAG+="udev-acl"'
            )
            lines.append("")
    if include_bootloaders:
        lines.append(QMK_BOOTLOADER_RULES)
    return "\n".join(lines).rstrip() + "\n"


def run_privileged(script: str) -> subprocess.CompletedProcess[str]:
    if os.geteuid() == 0:
        return subprocess.run(["bash", "-c", script], text=True)
    pkexec = shutil.which("pkexec")
    if pkexec and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return subprocess.run([pkexec, "bash", "-c", script], text=True)
    sudo = shutil.which("sudo")
    if not sudo:
        raise RuntimeError("Need pkexec or sudo to write udev rules.")
    return subprocess.run([sudo, "bash", "-c", script], text=True)


def apply_rules(content: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".rules", delete=False) as handle:
        handle.write(content)
        tmp = handle.name
    os.chmod(tmp, 0o644)
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"
    script = f"""
set -euo pipefail
install -m 644 {tmp} {RULES_PATH}
udevadm control --reload-rules
udevadm trigger
if getent group plugdev >/dev/null 2>&1; then
  usermod -aG plugdev {user} || true
fi
rm -f {tmp}
"""
    result = run_privileged(script)
    if result.returncode != 0:
        raise RuntimeError(f"Privileged install failed (exit {result.returncode}).")
