from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from vbc_cli import run_cli
from vbc_desktop import install_app_menu
from vbc_devices import UsbDevice, scan_devices
from vbc_rules import RULES_PATH, apply_rules, build_rules
from vbc_sites import after_install_text


def run_gui(args) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError:
        print("tkinter is not available; falling back to the prompt.", file=sys.stderr)
        return run_cli(args)

    def pill(canvas, x1, y1, x2, y2, **kwargs):
        h = max(2, y2 - y1)
        r = h / 2
        canvas.create_oval(x1, y1, x1 + h, y2, **kwargs)
        canvas.create_oval(x2 - h, y1, x2, y2, **kwargs)
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)

    class CircleToggle(tk.Canvas):
        def __init__(self, master, variable, *, fill, ring, empty, parent_bg, size=18):
            super().__init__(
                master, width=size, height=size, highlightthickness=0, bd=0, bg=parent_bg, cursor="hand2"
            )
            self.variable = variable
            self.size, self.fill, self.ring, self.empty = size, fill, ring, empty
            self.bind("<Button-1>", self._toggle)
            variable.trace_add("write", lambda *_: self._paint())
            self._paint()

        def _toggle(self, _event=None):
            self.variable.set(not bool(self.variable.get()))

        def _paint(self):
            self.delete("all")
            on = bool(self.variable.get())
            self.create_oval(
                1, 1, self.size - 1, self.size - 1,
                fill=self.fill if on else self.empty,
                outline=self.fill if on else self.ring, width=2,
            )

    class PillButton(tk.Canvas):
        def __init__(self, master, text, command, *, fill, text_fill, parent_bg, padx=16, pady=8):
            font = ("Segoe UI", 10)
            probe = tk.Label(master, text=text, font=font)
            probe.update_idletasks()
            tw, th = probe.winfo_reqwidth(), probe.winfo_reqheight()
            probe.destroy()
            width, height = tw + padx * 2, th + pady * 2
            super().__init__(
                master, width=width, height=height, highlightthickness=0, bd=0, bg=parent_bg, cursor="hand2"
            )
            self._command, self._fill, self._text, self._text_fill, self._font = command, fill, text, text_fill, font
            self._width, self._height = width, height
            self.bind("<Button-1>", lambda e: self._command and self._command())
            self.delete("all")
            pill(self, 1, 1, width - 1, height - 1, fill=fill, outline=fill)
            self.create_text(width / 2, height / 2, text=text, fill=text_fill, font=font)

    devices: List[UsbDevice] = []
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Could not open a window ({exc}); using the prompt.", file=sys.stderr)
        return run_cli(args)

    root.title("VIA Browser Connect")
    root.minsize(640, 480)
    bg, surface, muted, accent = "#1c1b1a", "#363434", "#a89890", "#e8c4b8"
    root.configure(bg=bg)
    all_hidraw = tk.BooleanVar(master=root, value=bool(args.all))
    include_bl = tk.BooleanVar(master=root, value=not args.no_bootloaders)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background=bg, foreground="#f1ebe0", fieldbackground=surface)
    style.configure("TFrame", background=bg)
    style.configure("Surface.TFrame", background=surface)
    style.configure("TLabel", background=bg, foreground="#f1ebe0")
    style.configure("Surface.TLabel", background=surface, foreground="#f1ebe0")
    style.configure("Muted.TLabel", background=bg, foreground=muted)
    style.configure(
        "TScrollbar", background=accent, troughcolor=surface, bordercolor=surface,
        lightcolor=accent, darkcolor=accent, arrowcolor=surface, relief="flat",
    )
    style.map(
        "TScrollbar",
        background=[("active", accent), ("pressed", accent), ("!disabled", accent)],
        arrowcolor=[("active", surface), ("pressed", surface), ("!disabled", surface)],
        lightcolor=[("active", accent), ("pressed", accent)],
        darkcolor=[("active", accent), ("pressed", accent)],
    )

    header = ttk.Frame(root, padding=(20, 16, 20, 8))
    header.pack(fill="x")
    ttk.Label(header, text="VIA Browser Connect", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(
        header,
        text="USB cable recommended. Select wired keyboards, then enable them for VIA / Vial / screen tools. 2.4G may work with VIA; results will vary.",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(4, 0))
    body = ttk.Frame(root, padding=(20, 8, 20, 8))
    body.pack(fill="both", expand=True)
    canvas = tk.Canvas(body, bg=surface, highlightthickness=0)
    scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas, style="Surface.TFrame")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    vars_by_index: List[tk.BooleanVar] = []

    def redraw():
        for child in inner.winfo_children():
            child.destroy()
        vars_by_index.clear()
        if not devices:
            ttk.Label(
                inner, text="No USB devices found. Plug a keyboard in and press Refresh.", style="Surface.TLabel"
            ).pack(anchor="w", padx=8, pady=12)
            return
        for d in devices:
            var = tk.BooleanVar(master=root, value=d.selected)
            vars_by_index.append(var)
            row = ttk.Frame(inner, style="Surface.TFrame")
            row.pack(fill="x", padx=8, pady=4)
            CircleToggle(row, var, fill=accent, ring=muted, empty=surface, parent_bg=surface).pack(side="left")
            ttk.Label(
                row, text=f"{d.kind:<4}  {d.ident}   {d.label}", font=("IBM Plex Mono", 11), style="Surface.TLabel"
            ).pack(side="left", padx=8)

    def refresh():
        nonlocal devices
        devices = scan_devices()
        for d in devices:
            d.selected = True if args.all or d.kind == "HID" else False
        redraw()

    def selected_devices():
        for d, var in zip(devices, vars_by_index):
            d.selected = bool(var.get())
        return devices

    def do_enable():
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
            f"Installed {RULES_PATH}\n\n{after_install_text()}",
        )

    def do_save():
        from tkinter import filedialog
        current = selected_devices()
        rules = build_rules(current, all_hidraw=all_hidraw.get(), include_bootloaders=include_bl.get())
        path = filedialog.asksaveasfilename(
            title="Save udev rules", defaultextension=".rules", initialfile="70-via-browser-connect.rules"
        )
        if path:
            Path(path).write_text(rules, encoding="utf-8")

    def do_install_menu():
        try:
            path = install_app_menu()
        except Exception as exc:
            messagebox.showerror("VIA Browser Connect", str(exc))
            return
        messagebox.showinfo(
            "VIA Browser Connect",
            f"Added to the application menu:\n{path}\n\nSearch GNOME, KDE, XFCE, Cinnamon, MATE, or LXQt for VIA Browser Connect.",
        )

    def option_row(parent, label, variable):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=3)
        CircleToggle(row, variable, fill=accent, ring=muted, empty=bg, parent_bg=bg).pack(side="left")
        ttk.Label(row, text=label).pack(side="left", padx=8)

    options = ttk.Frame(root, padding=(20, 4, 20, 4))
    options.pack(fill="x")
    option_row(options, "Allow every hidraw device (broader, less precise)", all_hidraw)
    option_row(options, "Include QMK / RP2040 bootloaders for flashing", include_bl)
    actions = ttk.Frame(root, padding=(20, 8, 20, 16))
    actions.pack(fill="x")
    PillButton(actions, "Refresh list", refresh, fill=accent, text_fill=surface, parent_bg=bg).pack(side="left")
    PillButton(actions, "Save rules…", do_save, fill=accent, text_fill=surface, parent_bg=bg).pack(side="left", padx=8)
    PillButton(actions, "Add to app menu", do_install_menu, fill=accent, text_fill=surface, parent_bg=bg).pack(
        side="left", padx=8
    )
    PillButton(actions, "Enable with sudo", do_enable, fill=accent, text_fill=surface, parent_bg=bg).pack(side="right")
    refresh()
    root.mainloop()
    return 0
