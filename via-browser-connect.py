#!/usr/bin/env python3
"""VIA Browser Connect — pick USB keyboards and grant Chrome WebHID access on Linux.

Chrome apps such as VIA, Vial, and Keychron Launcher talk to keyboards through
the WebHID API. On Linux that requires udev rules so hidraw nodes are readable
by your user. This script lists USB devices, lets you choose keyboards, then
writes those rules using pkexec or sudo.

Usage:
    python3 via-browser-connect.py           GUI when a display is available, else prompt
    python3 via-browser-connect.py --cli     numbered prompt
    python3 via-browser-connect.py --scan    print devices and exit
    python3 via-browser-connect.py --all     allow every hidraw device
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

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
\"\"\"


@dataclass
class UsbDevice:
    vendor_id: str
    product_id: str
    name: str
    manufacturer: str
    kind: str
    bus: str = \"\"
    sysfs: str = \"\"
    selected: bool = False

    @property
    def ident(self) -> str:
        return f\"{self.vendor_id}:{self.product_id}\"

    @property
    def label(self) -> str:
        host = self.manufacturer if self.manufacturer else \"USB\"
        if self.name:
            return f\"{host} {self.name}\".strip()
        return f\"{host} {self.ident}\"
