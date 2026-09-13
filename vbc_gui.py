from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from vbc_cli import run_cli
from vbc_devices import UsbDevice, scan_devices
from vbc_rules import RULES_PATH, apply_rules, build_rules


def run_gui(args) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError:
        print("tkinter is not available; falling back to the prompt.", file=sys.stderr)
        return run_cli(args)

    devices: List[UsbDevice] = []

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Could not open a window ({exc}); using the prompt.", file=sys.stderr)
        return run_cli(args)

    root.title("VIA Browser Connect")
    root.minsize(640, 480)
    root.configure(bg="#0b0c0d")

    all_hidraw = tk.BooleanVar(master=root, value=bool(args.all))
    include_bl = tk.BooleanVar(master=root, value=not args.no_bootloaders)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background="#0b0c0d", foreground="#ecece6", fieldbackground="#141516")
    style.configure("TFrame", background="#0b0c0d")
    style.configure("TLabel", background="#0b0c0d", foreground="#ecece6")
    style.configure("Muted.TLabel", background="#0b0c0d", foreground="#8c8e8a")
    style.configure("TCheckbutton", background="#0b0c0d", foreground="#ecece6")
    style.configure("TButton", background="#c5cdd4", foreground="#0b0c0d", padding=8)
    style.map("TButton", background=[("active", "#dbe2e8")])

    header = ttk.Frame(root, padding=(20, 16, 20, 8))
    header.pack(fill="x")
    ttk.Label(header, text="VIA Browser Connect", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(
        header,
        text="Select USB keyboards, then enable them for Chrome (VIA / Vial / QMK).",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(4, 0))

    body = ttk.Frame(root, padding=(20, 8, 20, 8))
    body.pack(fill="both", expand=True)
    canvas = tk.Canvas(body, bg="#141516", highlightthickness=0)
    scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    vars_by_index: List[tk.BooleanVar] = []

    def redraw() -> None:
        for child in inner.winfo_children():
            child.destroy()
        vars_by_index.clear()
        if not devices:
            ttk.Label(inner, text="No USB devices found. Plug a keyboard in and press Refresh.").pack(
                anchor="w", padx=8, pady=12
            )
            return
        for d in devices:
            var = tk.BooleanVar(master=root, value=d.selected)
            vars_by_index.append(var)
            row = ttk.Frame(inner)
            row.pack(fill="x", padx=4, pady=2)
            ttk.Checkbutton(row, variable=var).pack(side="left")
            ttk.Label(row, text=f"{d.kind:<4}  {d.ident}   {d.label}", font=("IBM Plex Mono", 10)).pack(
                side="left", padx=6
            )

    def refresh() -> None:
        nonlocal devices
        devices = scan_devices()
        for d in devices:
            d.selected = True if args.all else d.kind == "HID"
        redraw()

    def selected_devices() -> List[UsbDevice]:
        for d, var in zip(devices, vars_by_index):
            d.selected = bool(var.get())
        return devices

    def do_enable() -> None:
        current = selected_devices()
        if not all_hidraw.get() and not any(d.selected for d in current):
            messagebox.showinfo("VIA Browser Connect", "Select at least one keyboard, or enable all hidraw.")
            return
        rules = build_rules(current, all_hidraw=all_hidraw.get(), include_bootloaders=include_bl.get())
        try:
            apply_rules(rules)
        except Exception as exc:
            messagebox.showerror("VIA Browser Connect", str(exc))
            return
        messagebox.showinfo(
            "VIA Browser Connect",
            f"Installed {RULES_PATH}\n\nUnplug and replug each keyboard, then reopen Chrome.\n"
            "VIA: https://usevia.app\nVial: https://vial.rocks",
        )

    def do_save() -> None:
        from tkinter import filedialog

        current = selected_devices()
        rules = build_rules(current, all_hidraw=all_hidraw.get(), include_bootloaders=include_bl.get())
        path = filedialog.asksaveasfilename(
            title="Save udev rules",
            defaultextension=".rules",
            initialfile="70-via-browser-connect.rules",
        )
        if path:
            Path(path).write_text(rules, encoding="utf-8")

    options = ttk.Frame(root, padding=(20, 4, 20, 4))
    options.pack(fill="x")
    ttk.Checkbutton(options, text="Allow every hidraw device (broader, less precise)", variable=all_hidraw).pack(anchor="w")
    ttk.Checkbutton(options, text="Include QMK / RP2040 bootloaders for flashing", variable=include_bl).pack(anchor="w")
    actions = ttk.Frame(root, padding=(20, 8, 20, 16))
    actions.pack(fill="x")
    ttk.Button(actions, text="Refresh list", command=refresh).pack(side="left")
    ttk.Button(actions, text="Save rules…", command=do_save).pack(side="left", padx=8)
    ttk.Button(actions, text="Enable with sudo", command=do_enable).pack(side="right")
    refresh()
    root.mainloop()
    return 0
