from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class UsbDevice:
    vendor_id: str
    product_id: str
    name: str
    manufacturer: str
    kind: str
    bus: str = ""
    sysfs: str = ""
    selected: bool = False

    @property
    def ident(self) -> str:
        return f"{self.vendor_id}:{self.product_id}"

    @property
    def label(self) -> str:
        host = self.manufacturer if self.manufacturer else "USB"
        if self.name:
            return f"{host} {self.name}".strip()
        return f"{host} {self.ident}"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _is_hid_interface(iface: Path) -> bool:
    return _read(iface / "bInterfaceClass").lower() == "03"


def scan_sysfs() -> List[UsbDevice]:
    root = Path("/sys/bus/usb/devices")
    if not root.is_dir():
        return []
    found: List[UsbDevice] = []
    for entry in sorted(root.iterdir()):
        if ":" in entry.name:
            continue
        vendor = _read(entry / "idVendor").lower()
        product = _read(entry / "idProduct").lower()
        if not vendor or not product:
            continue
        hid = False
        for child in entry.iterdir():
            if ":" in child.name and _is_hid_interface(child):
                hid = True
                break
        found.append(
            UsbDevice(
                vendor_id=vendor.zfill(4),
                product_id=product.zfill(4),
                name=_read(entry / "product") or "",
                manufacturer=_read(entry / "manufacturer") or "",
                kind="HID" if hid else "USB",
                bus=f"{_read(entry / 'busnum')} {_read(entry / 'devnum')}".strip(),
                sysfs=str(entry),
                selected=hid,
            )
        )
    return found


def scan_lsusb() -> List[UsbDevice]:
    lsusb = shutil.which("lsusb")
    if not lsusb:
        return []
    try:
        out = subprocess.check_output([lsusb], text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return []
    devices: List[UsbDevice] = []
    for line in out.splitlines():
        parts = line.split()
        if "ID" not in parts:
            continue
        idx = parts.index("ID")
        ident = parts[idx + 1] if idx + 1 < len(parts) else ""
        if ":" not in ident:
            continue
        vid, pid = ident.split(":", 1)
        rest = " ".join(parts[idx + 2 :]).strip()
        manufacturer, _, name = rest.partition(" ")
        devices.append(
            UsbDevice(
                vendor_id=vid.lower().zfill(4),
                product_id=pid.lower().zfill(4),
                name=name or rest,
                manufacturer=manufacturer or "",
                kind="USB",
                bus=" ".join(parts[:4]),
                selected=False,
            )
        )
    return devices


def merge_scans(sysfs_devs: Sequence[UsbDevice], lsusb_devs: Sequence[UsbDevice]) -> List[UsbDevice]:
    by_id = {d.ident: d for d in lsusb_devs}
    merged: List[UsbDevice] = []
    seen = set()
    for d in sysfs_devs:
        seen.add(d.ident)
        other = by_id.get(d.ident)
        if other and not d.name:
            d.name = other.name
            d.manufacturer = d.manufacturer or other.manufacturer
        merged.append(d)
    for d in lsusb_devs:
        if d.ident not in seen:
            merged.append(d)
    return merged


def scan_devices() -> List[UsbDevice]:
    return merge_scans(scan_sysfs(), scan_lsusb())
