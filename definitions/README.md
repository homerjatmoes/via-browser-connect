# VIA keyboard JSON

Drop VIA / Vial definition files here as you collect them. The app lists whatever is in `index.json`.

## Add a board

1. Put the `.json` in this folder (`VENDOR_MODEL.json` and `VENDOR_MODEL_24G.json` if wired and 2.4G differ).
2. Append an entry to `index.json`.
3. Commit. The web app reads GitHub first, then the local copy.

```json
{
  "name": "AULA F75 Ultra",
  "file": "AULA_F75_ULTRA.json",
  "vendorId": "0xFFFE",
  "productId": "0x00A9",
  "mode": "usb",
  "viaPackedId": "0xFFFE00A9",
  "notes": "Optional. VIA packed id is (VID << 16) | PID."
}
```

`mode` is `usb` or `2.4g`. VIA Design tab packed ids look like `0x36B03066` (USB EK21) and `0x36B03002` (2.4G dongle).

## Current files

| File | Mode | VID:PID | VIA packed id |
| --- | --- | --- | --- |
| [EPOMAKER_EK21.json](EPOMAKER_EK21.json) | USB | `36B0:3066` | `0x36B03066` |
| [EPOMAKER_EK21_24G.json](EPOMAKER_EK21_24G.json) | 2.4G | `36B0:3002` | `0x36B03002` |

Load the file in VIA: Settings → Show Design tab → Design → Load. Enable **Use V2 definitions** if VIA shows a red error.
