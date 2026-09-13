# VIA keyboard JSON

Drop VIA / Vial definition files here as you collect them. The app lists whatever is in `index.json`.

**USB is required.** Wired JSON is the supported set. A 2.4G file may exist for experiments; results vary.

## Add a board

1. Put the `.json` in this folder (`VENDOR_MODEL.json`). Add `VENDOR_MODEL_24G.json` only if you are documenting an optional dongle — it is unsupported.
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

`mode` is `usb` (supported) or `2.4g` (optional, results vary). VIA packed id is `(VID << 16) | PID`.

## Current files

| File | Mode | VID:PID | VIA packed id |
| --- | --- | --- | --- |
| [EPOMAKER_EK21.json](EPOMAKER_EK21.json) | USB | `36B0:3066` | `0x36B03066` |
| [RK61.json](RK61.json) | USB | `1480:6461` | `0x14806461` |
| [AULA_F75_ULTRA.json](AULA_F75_ULTRA.json) | USB | `FFFE:00A9` | `0xFFFE00A9` |
| [EPOMAKER_QK108.json](EPOMAKER_QK108.json) | USB | `36B0:30AF` | `0x36B030AF` |
| [EPOMAKER_GALAXY65.json](EPOMAKER_GALAXY65.json) | USB | `28E9:3165` | `0x28E93165` |
| [EPOMAKER_EK21_24G.json](EPOMAKER_EK21_24G.json) | 2.4G (unsupported) | `36B0:3002` | `0x36B03002` |

Official zips for F75 Ultra, QK108, Galaxy65, and RK61 only included **one** JSON each (USB). I did not invent 2.4G PIDs.

Load in VIA: Settings → Show Design tab → Design → Load. Enable **Use V2 definitions** if VIA shows a red error. Use a USB cable.
