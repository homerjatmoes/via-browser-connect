# VIA Browser Connect

Linux helper that writes udev rules so a Chromium-based web browser can open **USB** keyboards through WebHID. Use it for [VIA](https://usevia.app), [Vial](https://vial.rocks), and Keychron Launcher.

**USB cable recommended.** Plug the keyboard in. That is the recommended path — EPOMAKER EK21 over USB (`36b0:3066`) is confirmed working. 2.4G may work with VIA; results will vary. If VIA cannot open the dongle, switch off 2.4G / Bluetooth and use a cable.

No pip packages. Python 3 + sudo (or pkexec) is enough.

AI coded with human review.

## Screenshots

GUI (Olivia Dark):

![VIA Browser Connect GUI](docs/gui.svg)

CLI:

![VIA Browser Connect CLI](docs/cli.svg)

## Run

Clone the **whole** repo (this is not a single-file copy):

```bash
git clone https://github.com/homerjatmoes/via-browser-connect.git
cd via-browser-connect
python3 via-browser-connect.py
```

The launcher needs `vbc_cli.py`, `vbc_gui.py`, `vbc_devices.py`, `vbc_rules.py`, and `vbc_desktop.py` beside it. If you copy only `via-browser-connect.py`, the next run will try to download those helpers next to it.

No display? Use the prompt:

```bash
python3 via-browser-connect.py --cli
```

Other flags:

```bash
python3 via-browser-connect.py --scan          # list USB devices
python3 via-browser-connect.py --all           # allow every hidraw node
python3 via-browser-connect.py --dry-run --cli # print rules, do not install
python3 via-browser-connect.py --install-menu  # add to the application menu
python3 via-browser-connect.py --remove-menu   # remove the launcher
```

If the GUI fails to start, install `python3-tk` or use `--cli`.

## Application menu

GNOME, KDE Plasma, XFCE, Cinnamon, MATE, LXQt, COSMIC, and most Wayland launchers (rofi, fuzzel, wofi) all use the same XDG `.desktop` file. No extra per-desktop scripts.

From the GUI, click **Add to app menu**, or:

```bash
python3 via-browser-connect.py --install-menu
```

That writes:

- `~/.local/share/applications/via-browser-connect.desktop`
- `~/.local/share/icons/hicolor/scalable/apps/via-browser-connect.svg`

Then search **VIA Browser Connect** in Activities, Kickoff, Whisker, or your launcher. Log out/in only if an older desktop does not pick it up immediately.

## After it installs

1. Unplug and replug each **USB** keyboard.
2. Fully quit the Chromium-based web browser and reopen it. Snap-packaged browsers often ignore udev — use a `.deb` or distro package.
3. Open [usevia.app](https://usevia.app) and authorize the wired device.

Rules are written to `/etc/udev/rules.d/70-via-browser-connect.rules` (must sort before `73-seat-late.rules`).

## VIA JSON library

Keyboard definition files live in [`definitions/`](https://github.com/homerjatmoes/via-browser-connect/tree/main/definitions). USB JSON is the supported set. Drop a file in, append a row to `definitions/index.json`, commit.

| File | Mode | VID:PID | VIA packed id |
| --- | --- | --- | --- |
| [EPOMAKER_EK21.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/EPOMAKER_EK21.json) | USB | `36b0:3066` | `0x36B03066` |
| [RK61.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/RK61.json) | USB | `1480:6461` | `0x14806461` |
| [AULA_F75_ULTRA.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/AULA_F75_ULTRA.json) | USB | `fffe:00a9` | `0xFFFE00A9` |
| [EPOMAKER_QK108.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/EPOMAKER_QK108.json) | USB | `36b0:30af` | `0x36B030AF` |
| [EPOMAKER_GALAXY65.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/EPOMAKER_GALAXY65.json) | USB | `28e9:3165` | `0x28E93165` |
| [EPOMAKER_EK21_24G.json](https://github.com/homerjatmoes/via-browser-connect/blob/main/definitions/EPOMAKER_EK21_24G.json) | 2.4G (may work with VIA) | `36b0:3002` | `0x36B03002` |

## EPOMAKER notes

| Device | VID:PID | VIA JSON |
| --- | --- | --- |
| EK21 USB (recommended) | `36b0:3066` | `EPOMAKER_EK21.json` — packed id `0x36B03066` — **tested** |
| Wireless 2.4G dongle (optional) | `36b0:3002` | `EPOMAKER_EK21_24G.json` — packed id `0x36B03002` — **may work with VIA** |

USB cable recommended to avoid connectivity issues. The 2.4G dongle is a different product. It may work with VIA; results will vary. If it does not, switch the board off 2.4G / Bluetooth and plug in a cable.

EPOMAKER pulled the old 2.4G download page. The 2.4G file here is the official July 2025 EK21 layout with `productId` `0x3002`. Enable **Use V2 definitions** if VIA shows a red error.

## `NotAllowedError: Failed to open the device`

That is a Linux hidraw permission error, not a VIA JSON problem. Re-run this script so the matching VID:PID is in the rules, replug, restart the Chromium-based web browser. Check `chrome://device-log/` for HID lines.

## License

[GNU General Public License v3.0](LICENSE)
