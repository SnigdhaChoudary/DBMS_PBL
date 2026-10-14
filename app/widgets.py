"""Reusable, themed widgets. All colours, fonts and sizes come from app.theme,
so they follow the user's zoom level."""
import math
import tkinter as tk
from datetime import date, datetime
from decimal import Decimal
from tkinter import font as tkfont
from tkinter import ttk

from . import theme as T

# --------------------------------------------------------------- value formatting
RIGHT_KEYS = {"amount", "paid", "balance", "fee", "rate_per_hour", "daily_cap", "minutes", "minutes_parked",
              "minutes_inside", "entries", "total_slots", "occupied", "available", "maintenance", "free_slots",
              "bills", "billed", "collected", "outstanding", "payments", "visits", "hours_parked", "vehicles",
              "busy_rank"}
CENTER_KEYS = {"floor_no", "slot_no", "status", "bill_status", "pass_state", "slot_status", "state", "bill_id",
               "session_id", "customer_id", "vehicle_id", "reservation_id", "pass_id", "tariff_id", "hour_of_day",
               "duration", "pass_type", "vehicle_type", "type_name"}


def fmt(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(value)  # keeps 120.00 for money and 2 for counts
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def default_anchor(key):
    if key in RIGHT_KEYS:
        return "e"
    if key in CENTER_KEYS:
        return "center"
    return "w"


def pad_text(text, anchor):
    """Treeview has no cell padding, so add a little space inside the text."""
    if anchor == "w":
        return "  " + text
    if anchor == "e":
        return text + "  "
    return text


def human_minutes(minutes):
    minutes = int(minutes or 0)
    days, rest = divmod(minutes, 1440)
    hours, mins = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {mins:02d}m"


# --------------------------------------------------------------------- buttons
class Btn(tk.Canvas):
    """Rounded button with hover, pressed, focus and disabled states.
    variant: primary (teal), secondary (white), danger (red), ghost (text only), header (on navy)."""

    VARIANTS = {
        #            fill,        hover,      pressed,      text,      border
        "primary": (T.TEAL, T.TEAL_DARK, "#0A4F4D", "#FFFFFF", T.TEAL),
        "secondary": (T.CARD, "#EEF3F8", "#E1E9F2", T.TEXT, T.BORDER),
        "danger": (T.ERROR, "#B92D3B", "#9E2431", "#FFFFFF", T.ERROR),
        "ghost": (None, "#EEF3F8", "#E1E9F2", T.MUTED, None),
        "header": (None, "#2C4160", "#3A5278", "#FFFFFF", "#3A4F6B"),
    }

    def __init__(self, parent, text, command=None, variant="secondary", width=None, height=None, padx=None):
        self._bg_parent = parent.cget("bg")
        height = height or T.CONTROL_HEIGHT
        padx = T.px(18) if padx is None else padx
        self._font = tkfont.Font(font=T.font(10, "bold" if variant in ("primary", "danger", "header") else "normal"))
        w = max(width or 0, self._font.measure(text) + 2 * padx, T.px(72) if variant != "header" else 0)
        super().__init__(parent, width=w, height=height, bg=self._bg_parent, highlightthickness=0, bd=0,
                         cursor="hand2", takefocus=1)
        self.text, self.command, self.variant = text, command, variant
        self._bw, self._bh = w, height
        self._state, self._hover, self._pressed, self._focus = "normal", False, False, False
        self.bind("<Enter>", lambda e: self._set(hover=True))
        self.bind("<Leave>", lambda e: self._set(hover=False, pressed=False))
        self.bind("<ButtonPress-1>", lambda e: self._set(pressed=True))
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<FocusIn>", lambda e: self._set(focus=True))
        self.bind("<FocusOut>", lambda e: self._set(focus=False))
        self.bind("<Return>", lambda e: self.invoke())
        self.bind("<space>", lambda e: self.invoke())
        self._draw()

    def _set(self, **kw):
        for k, v in kw.items():
            setattr(self, "_" + k, v)
        self._draw()

    def _release(self, event):
        was = self._pressed
        self._set(pressed=False)
        if was and 0 <= event.x <= self._bw and 0 <= event.y <= self._bh:
            self.invoke()

    def invoke(self):
        if self._state == "normal" and self.command:
            self.command()

    def enable(self, flag=True):
        self._state = "normal" if flag else "disabled"
        self.configure(cursor="hand2" if flag else "arrow")
        self._draw()

    def _rounded(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
               x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self):
        self.delete("all")
        fill, hover, pressed, fg, border = self.VARIANTS[self.variant]
        if self._state == "disabled":
            fill, fg, border = (T.INPUT_DISABLED if fill else None), "#9AA6B6", (T.BORDER if border else None)
        elif self._pressed:
            fill = pressed
        elif self._hover:
            fill = hover
        outline = T.TEAL if (self._focus and self._state == "normal" and self.variant in ("secondary", "ghost")) else border
        if fill or outline:
            self._rounded(1, 1, self._bw - 1, self._bh - 1, T.px(7), fill=fill or self._bg_parent,
                          outline=outline or fill or self._bg_parent, width=1)
        self.create_text(self._bw / 2, self._bh / 2, text=self.text, fill=fg, font=self._font)


# ---------------------------------------------------------------------- panels
class Panel(tk.Frame):
    """White card with a thin border, an optional heading and a right-hand action area."""

    def __init__(self, parent, title=None, padding=None):
        padding = T.L if padding is None else padding
        super().__init__(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER,
                         highlightcolor=T.BORDER)
        self.actions = None
        if title:
            head = tk.Frame(self, bg=T.CARD)
            head.pack(fill="x", padx=padding, pady=(T.M, T.M))
            tk.Label(head, text=title, bg=T.CARD, fg=T.NAVY, font=T.font(12, "bold")).pack(side="left")
            self.actions = tk.Frame(head, bg=T.CARD)
            self.actions.pack(side="right")
            tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x")
        self.body = tk.Frame(self, bg=T.CARD)
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)


class Pill(tk.Label):
    """Small label such as '22 free slot(s)'."""

    def __init__(self, parent, text="", kind="teal"):
        super().__init__(parent, padx=T.px(10), pady=T.px(3), font=T.font(9, "bold"))
        self.set(text, kind)

    def set(self, text, kind="teal"):
        self.configure(text=text, bg=T.TINT[kind], fg=T.KIND_COLOR[kind])


class ResultBox(tk.Frame):
    """Message area with a coloured edge: success, error or info. Shows a hint while empty."""

    def __init__(self, parent, hint="", wraplength=420):
        super().__init__(parent, bg=T.TINT["neutral"])
        self.hint = hint
        self.bar = tk.Frame(self, width=T.px(4), bg=T.BORDER)
        self.bar.pack(side="left", fill="y")
        self.label = tk.Label(self, justify="left", anchor="w", padx=T.M, pady=T.px(10), wraplength=T.px(wraplength))
        self.label.pack(side="left", fill="both", expand=True)
        self.clear()

    def show(self, text, kind="success"):
        bg = T.TINT[kind]
        self.configure(bg=bg)
        self.bar.configure(bg=T.KIND_COLOR[kind])
        self.label.configure(text=text, bg=bg, fg=T.TEXT, font=T.font(10, "bold"))

    def clear(self):
        self.configure(bg=T.TINT["neutral"])
        self.bar.configure(bg=T.BORDER)
        self.label.configure(text=self.hint, bg=T.TINT["neutral"], fg=T.MUTED, font=T.font(10))


# ------------------------------------------------------------------ scrolling page
class ScrollPage(tk.Frame):
    """A page that fills the window when it fits and scrolls vertically when zoomed content does not.
    Build the page inside `.inner`."""

    def __init__(self, parent):
        super().__init__(parent, bg=T.BG)
        self.canvas = tk.Canvas(self, bg=T.BG, highlightthickness=0, bd=0, yscrollincrement=T.px(24))
        self.vbar = ttk.Scrollbar(self, orient="vertical", style="Modern.Vertical.TScrollbar", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=T.BG)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._fit)
        self.inner.bind("<Configure>", self._fit)
        self._bar_visible = False

    def _fit(self, _event=None):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        need = self.inner.winfo_reqheight()
        total = max(height, need)
        self.canvas.itemconfigure(self._win, width=width, height=total)
        self.canvas.configure(scrollregion=(0, 0, width, total))

    def _on_scroll(self, first, last):
        self.vbar.set(first, last)
        needed = not (float(first) <= 0.0 and float(last) >= 1.0)
        if needed and not self._bar_visible:
            self.vbar.pack(side="right", fill="y", padx=(T.S, 0))
            self._bar_visible = True
        elif not needed and self._bar_visible:
            self.vbar.pack_forget()
            self._bar_visible = False

    def scroll(self, units):
        if self._bar_visible:
            self.canvas.yview_scroll(units, "units")


# ----------------------------------------------------------------------- tables
class DataTable(tk.Frame):
    """Themed table: navy headings, zebra rows, hover and selection highlight, status colours,
    an empty-state message, columns that always fit the available width, and a scroll bar
    that appears only when needed."""

    def __init__(self, parent, columns, height=8, on_select=None, status_key=None,
                 empty_text="No records to display"):
        super().__init__(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER)
        self.on_select, self.status_key = on_select, status_key
        self.rows, self.keys, self._weights = {}, [], {}
        self._base, self._hover, self._sel = {}, None, None
        self.tree = ttk.Treeview(self, style="Modern.Treeview", show="headings", height=height, selectmode="browse")
        self.vbar = ttk.Scrollbar(self, orient="vertical", style="Modern.Vertical.TScrollbar", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_scroll)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.empty = tk.Label(self, text=empty_text, bg=T.CARD, fg=T.MUTED, font=T.font(11))
        self._configure_tags()
        self.set_columns(columns)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_event)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda e: self._unhover())
        self.tree.bind("<Configure>", self._fit_columns)

    # ---- setup
    def _configure_tags(self):
        t = self.tree
        t.tag_configure("odd", background=T.STRIPE)
        t.tag_configure("even", background=T.CARD)
        t.tag_configure("hover", background=T.HOVER_BG, foreground=T.TEXT)
        t.tag_configure("sel", background=T.SELECT_BG, foreground=T.TEXT)
        self._strike_font = tkfont.Font(font=T.font(10, overstrike=True))
        for name, (bg, fg, strikes) in T.STATUS_STYLES.items():
            opts = {"foreground": fg}
            if bg:
                opts["background"] = bg
            if strikes:
                opts["font"] = self._strike_font
            t.tag_configure("st_" + name, **opts)

    def set_columns(self, columns):
        """columns: list of (key, heading, relative_width) or (key, heading, relative_width, anchor).
        Widths are relative: the table stretches them to fill whatever width it has."""
        self.keys = [c[0] for c in columns]
        self.anchors, self._weights = {}, {}
        self.tree["columns"] = self.keys
        for col in columns:
            key, heading, width = col[:3]
            anchor = col[3] if len(col) > 3 else default_anchor(key)
            self.anchors[key] = anchor
            self._weights[key] = width
            self.tree.heading(key, text=pad_text(heading, anchor), anchor=anchor)
            self.tree.column(key, width=T.px(width), minwidth=T.px(36), anchor=anchor, stretch=False)

    def _fit_columns(self, event=None):
        if not self.keys:
            return
        available = (event.width if event else self.tree.winfo_width()) - 2
        total = sum(self._weights.values()) or 1
        for key in self.keys:
            self.tree.column(key, width=max(T.px(36), int(available * self._weights[key] / total)))

    # ---- data
    def load(self, rows):
        self.tree.delete(*self.tree.get_children())
        self.rows, self._base, self._hover, self._sel = {}, {}, None, None
        for i, row in enumerate(rows):
            values = [pad_text(self._cell(key, row), self.anchors[key]) for key in self.keys]
            tags = self._tags_for(row, i)
            iid = self.tree.insert("", "end", values=values, tags=tags)
            self.rows[iid], self._base[iid] = row, tags
        if rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.58, anchor="center")
        self._fit_columns()

    def _cell(self, key, row):
        text = fmt(row.get(key))
        if key == self.status_key and text.upper() in T.STATUS_STYLES:
            return "●  " + text.upper()
        return text

    def _tags_for(self, row, index):
        zebra = "odd" if index % 2 else "even"
        value = fmt(row.get(self.status_key)).upper() if self.status_key else ""
        if value in T.STATUS_STYLES:
            bg = T.STATUS_STYLES[value][0]
            return ("st_" + value,) if bg else (zebra, "st_" + value)
        return (zebra,)

    def selected(self):
        sel = self.tree.selection()
        return self.rows.get(sel[0]) if sel else None

    # ---- interaction
    def _on_scroll(self, first, last):
        self.vbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.vbar.grid_remove()
        else:
            self.vbar.grid()

    def _on_select_event(self, _event=None):
        sel = self.tree.selection()
        new = sel[0] if sel else None
        if self._sel and self._sel != new and self._sel in self._base:
            self.tree.item(self._sel, tags=self._base[self._sel])
        self._sel = new
        if new:
            self.tree.item(new, tags=("sel",))
            if self._hover == new:
                self._hover = None
        if self.on_select:
            self.on_select(self.selected())

    def _on_motion(self, event):
        iid = self.tree.identify_row(event.y)
        if iid == self._hover:
            return
        self._unhover()
        if iid and iid != self._sel and iid in self._base:
            self.tree.item(iid, tags=("hover",))
            self._hover = iid

    def _unhover(self):
        if self._hover and self._hover in self._base and self._hover != self._sel:
            self.tree.item(self._hover, tags=self._base[self._hover])
        self._hover = None


# ------------------------------------------------------------- occupancy table
class OccupancyTable(tk.Frame):
    """Read-only table whose last column is a real progress bar (teal, amber above 70 %, red above 90 %).
    Labels request no width of their own, so a narrow table clips text instead of overlapping columns."""

    COLS = [("Facility", 150, "w"), ("Floor", 48, "center"), ("Slots", 50, "e"), ("Used", 46, "e"),
            ("Free", 44, "e"), ("Maint.", 54, "e"), ("Occupancy", 150, "w")]

    def __init__(self, parent):
        super().__init__(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER)
        self.body = tk.Frame(self, bg=T.CARD)
        self.body.pack(fill="both", expand=True)
        bold = tkfont.Font(font=T.font(10, "bold"))
        for i, (name, weight, _) in enumerate(self.COLS):
            floor = bold.measure(name) + 2 * T.px(8) if i not in (0, 6) else T.px(90)
            self.body.columnconfigure(i, weight=weight, minsize=floor)

    def _label(self, row, col, text, bg, fg, font, anchor, pady):
        tk.Label(self.body, text=text, bg=bg, fg=fg, font=font, anchor=anchor, width=1,
                 padx=T.px(8), pady=pady).grid(row=row, column=col, sticky="nsew")

    def load(self, rows):
        for child in self.body.winfo_children():
            child.destroy()
        for c, (name, _, anchor) in enumerate(self.COLS):
            self._label(0, c, name, T.NAVY, "#FFFFFF", T.font(10, "bold"), anchor, T.px(7))
        if not rows:
            tk.Label(self.body, text="No occupancy data", bg=T.CARD, fg=T.MUTED, font=T.font(11),
                     pady=T.px(18)).grid(row=1, column=0, columnspan=len(self.COLS))
            return
        for r, row in enumerate(rows, start=1):
            bg = T.STRIPE if r % 2 == 0 else T.CARD
            values = [row["facility"], row["floor_no"], row["total_slots"], row["occupied"], row["available"], row["maintenance"]]
            for c, val in enumerate(values):
                self._label(r, c, fmt(val), bg, T.TEXT, T.font(10), self.COLS[c][2], T.px(6))
            cell = tk.Frame(self.body, bg=bg)
            cell.grid(row=r, column=6, sticky="nsew")
            pct = float(row["occupancy_pct"] or 0)
            color = T.ERROR if pct >= 90 else T.WARNING if pct >= 70 else T.TEAL
            tk.Label(cell, text=f"{pct:.1f}%", bg=bg, fg=T.TEXT, font=T.font(10, "bold"), width=6,
                     anchor="e").pack(side="right", padx=(0, T.px(8)))
            cv = tk.Canvas(cell, width=1, height=T.px(14), bg=bg, highlightthickness=0)
            cv.pack(side="left", fill="x", expand=True, padx=(T.px(8), T.px(4)), pady=T.px(7))
            cv.bind("<Configure>", lambda e, c=cv, p=pct, col=color: self._bar(c, p, col))

    @staticmethod
    def _bar(cv, pct, color):
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        pad = max(2, h // 5)
        cv.create_rectangle(0, pad, w, h - pad, fill="#E5EBF2", outline="")
        if pct > 0:
            cv.create_rectangle(0, pad, max(4, w * min(pct, 100) / 100), h - pad, fill=color, outline="")


# ------------------------------------------------------------------- selectors
class Pick(ttk.Combobox):
    """A drop-down that shows labels but returns ids."""

    def __init__(self, parent, width=24, **kw):
        super().__init__(parent, state="readonly", width=width, style="Modern.TCombobox", font=T.font(10), **kw)
        self.map = {}

    def set_items(self, items, keep=True):
        old = self.get()
        self.map = {label: value for label, value in items}
        self["values"] = list(self.map)
        if keep and old in self.map:
            self.set(old)
        elif self.map:
            self.current(0)

    def value(self):
        return self.map.get(self.get())


# ------------------------------------------------------------------ icons, cards
def draw_icon(cv, kind, cx, cy, color):
    """Small icons drawn with canvas primitives (no image files). Drawn on a 52 px grid, scaled afterwards."""
    if kind == "car":
        cv.create_polygon(cx - 9, cy - 1, cx - 6, cy - 9, cx + 6, cy - 9, cx + 9, cy - 1, fill=color, outline=color)
        cv.create_rectangle(cx - 13, cy - 2, cx + 13, cy + 6, fill=color, outline=color)
        for dx in (-7, 7):
            cv.create_oval(cx + dx - 3.5, cy + 3, cx + dx + 3.5, cy + 10, fill=color, outline=T.TINT["info"], width=2)
    elif kind == "check":
        cv.create_line(cx - 8, cy, cx - 2, cy + 6, cx + 9, cy - 6, fill=color, width=3, capstyle="round", joinstyle="round")
    elif kind == "parking":
        cv.create_rectangle(cx - 10, cy - 11, cx + 10, cy + 11, outline=color, width=2)
        cv.create_text(cx, cy, text="P", fill=color, font=T.font(12, "bold"))
    elif kind == "rupee":
        cv.create_text(cx, cy, text="₹", fill=color, font=T.font(16, "bold"))
    elif kind == "warning":
        cv.create_polygon(cx, cy - 11, cx + 12, cy + 9, cx - 12, cy + 9, outline=color, fill="", width=2, joinstyle="round")
        cv.create_line(cx, cy - 4, cx, cy + 2, fill=color, width=2, capstyle="round")
        cv.create_oval(cx - 1.5, cy + 4, cx + 1.5, cy + 7, fill=color, outline=color)


class KpiCard(tk.Frame):
    """Dashboard number card: coloured top edge, tinted icon circle, large value, caption."""

    def __init__(self, parent, title, caption, color, icon, tint):
        super().__init__(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER)
        tk.Frame(self, bg=color, height=T.px(4)).pack(fill="x")
        row = tk.Frame(self, bg=T.CARD)
        row.pack(fill="both", expand=True, padx=T.L, pady=(T.S, T.M))
        size = T.px(52)
        cv = tk.Canvas(row, width=size, height=size, bg=T.CARD, highlightthickness=0)
        cv.create_oval(2, 2, 50, 50, fill=tint, outline=tint)
        draw_icon(cv, icon, 26, 26, color)
        cv.scale("all", 0, 0, size / 52, size / 52)
        cv.pack(side="left", padx=(0, T.M))
        text = tk.Frame(row, bg=T.CARD)
        text.pack(side="left", fill="both", expand=True)
        tk.Label(text, text=title, bg=T.CARD, fg=T.MUTED, font=T.font(10, "bold"), anchor="w").pack(fill="x")
        self.value = tk.Label(text, text="-", bg=T.CARD, fg=T.NAVY, font=T.font(26, "bold"), anchor="w")
        self.value.pack(fill="x")
        tk.Label(text, text=caption, bg=T.CARD, fg=T.MUTED, font=T.font(9), anchor="w").pack(fill="x")

    def set(self, text):
        self.value.configure(text=text)


# ------------------------------------------------------------ navigation, status
class NavBar(tk.Frame):
    """Tabs that share the full width equally, with a teal underline on the active tab."""

    def __init__(self, parent, names, on_change):
        super().__init__(parent, bg=T.NAVY_2)
        self.on_change, self.current, self.items = on_change, None, {}
        f_bold = tkfont.Font(font=T.font(10, "bold"))
        minimum = max(f_bold.measure(n) for n in names) + 2 * T.M
        inner = tk.Frame(self, bg=T.NAVY_2)
        inner.pack(fill="x", padx=(T.M, T.M))
        for col, name in enumerate(names):
            inner.columnconfigure(col, weight=1, uniform="tabs", minsize=minimum)
            cell = tk.Frame(inner, bg=T.NAVY_2, height=T.px(46), cursor="hand2")
            cell.grid(row=0, column=col, sticky="ew")
            cell.pack_propagate(False)
            label = tk.Label(cell, text=name, bg=T.NAVY_2, fg=T.NAVY_TEXT, font=T.font(10), cursor="hand2")
            label.pack(fill="both", expand=True)
            line = tk.Frame(cell, bg=T.NAVY_2, height=max(3, T.px(3)))
            line.pack(fill="x", side="bottom")
            for w in (cell, label):
                w.bind("<Button-1>", lambda e, n=name: self.select(n))
                w.bind("<Enter>", lambda e, n=name: self._hover(n, True))
                w.bind("<Leave>", lambda e, n=name: self._hover(n, False))
            self.items[name] = (cell, label, line)

    def _hover(self, name, on):
        if name == self.current:
            return
        cell, label, _ = self.items[name]
        bg = "#2C4160" if on else T.NAVY_2
        cell.configure(bg=bg)
        label.configure(bg=bg, fg="#FFFFFF" if on else T.NAVY_TEXT)

    def select(self, name):
        for n, (cell, label, line) in self.items.items():
            active = n == name
            cell.configure(bg=T.NAVY_2)
            label.configure(bg=T.NAVY_2, fg="#FFFFFF" if active else T.NAVY_TEXT, font=T.font(10, "bold" if active else "normal"))
            line.configure(bg=T.TEAL if active else T.NAVY_2)
        self.current = name
        self.on_change(name)


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=T.CARD, highlightthickness=0)
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x")
        row = tk.Frame(self, bg=T.CARD)
        row.pack(fill="x", padx=T.L, pady=T.px(7))
        d = T.px(12)
        self.dot = tk.Canvas(row, width=d, height=d, bg=T.CARD, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, T.S))
        self.text = tk.Label(row, text="Ready", bg=T.CARD, fg=T.MUTED, font=T.font(10), anchor="w")
        self.text.pack(side="left", fill="x", expand=True)
        self.set("Ready", "neutral")

    def set(self, message, kind="success"):
        color = T.KIND_COLOR[kind]
        d = T.px(12)
        self.dot.delete("all")
        self.dot.create_oval(d * 0.17, d * 0.17, d * 0.83, d * 0.83, fill=color, outline=color)
        self.text.configure(text=message, fg=color if kind == "error" else T.TEXT if kind != "neutral" else T.MUTED)


# ------------------------------------------------------------------------ chart
def _nice_max(value):
    if value <= 0:
        return 1
    mag = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * mag:
            return m * mag
    return 10 * mag


def draw_bar_chart(cv, title, labels, values, highlight_max=False):
    cv.delete("all")
    p = T.px
    w, h = max(cv.winfo_width(), p(700)), max(cv.winfo_height(), p(160))
    left, right, top, bottom = p(58), p(24), p(44), h - p(38)
    cv.create_text(p(22), p(18), anchor="w", text=title, font=T.font(11, "bold"), fill=T.NAVY)
    if not values:
        cv.create_text(w / 2, h / 2, text="No data to chart", fill=T.MUTED, font=T.font(11))
        return
    top_value = _nice_max(max(values))
    for i in range(5):
        y = bottom - (bottom - top) * i / 4
        cv.create_line(left, y, w - right, y, fill=T.BORDER if i else "#B8C4D3")
        cv.create_text(left - p(8), y, anchor="e", text=f"{top_value * i / 4:g}", font=T.font(9), fill=T.MUTED)
    slot = (w - left - right) / len(values)
    bar_w = min(p(54), slot * 0.62)
    peak = max(values)
    small = len(values) > 14
    for i, (lab, val) in enumerate(zip(labels, values)):
        cx = left + slot * (i + 0.5)
        y = bottom - (bottom - top) * val / top_value
        color = T.ACCENT if (highlight_max and val == peak) else T.TEAL
        cv.create_rectangle(cx - bar_w / 2, y, cx + bar_w / 2, bottom, fill=color, outline="")
        cv.create_text(cx, y - p(9), text=f"{val:g}", font=T.font(9, "bold"), fill=T.NAVY)
        cv.create_text(cx, bottom + p(16), text=lab[:14 if small else 22], font=T.font(8 if small else 9), fill=T.MUTED)
