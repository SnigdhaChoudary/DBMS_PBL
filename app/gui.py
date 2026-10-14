"""Tkinter screen for the Smart Parking system. One page per task.

Look and feel (colours, fonts, tables, buttons) is defined in app/theme.py and app/widgets.py.
This file only arranges the pages and connects the buttons to app/services.py."""
import sys
import tkinter as tk
from datetime import datetime, date, timedelta
from decimal import Decimal
from tkinter import ttk, messagebox, filedialog

from . import settings
from . import theme as T
from .config import PASS_PLANS, PAYMENT_METHODS
from .errors import ParkingError
from .reports import REPORTS, CHARTS, export_csv
from .services import ParkingService
from .widgets import (Btn, DataTable, KpiCard, NavBar, OccupancyTable, Panel, Pick, Pill, ResultBox,
                      ScrollPage, StatusBar, draw_bar_chart, fmt, human_minutes)

TAB_NAMES = ["Dashboard", "Slot Search", "Gate", "Reservations", "Billing", "Customers",
             "Vehicles", "Passes", "Tariffs", "Reports"]


def enable_hidpi():
    """On Windows, tell the system this program handles high-DPI screens itself.
    Without this Windows stretches the window as a bitmap, which makes all text blurry."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass  # never stop the program because of a display setting


class App(tk.Tk):
    def __init__(self, service=None, dialogs=True, zoom=None):
        enable_hidpi()
        super().__init__()
        self.svc = service or ParkingService()
        self.dialogs = dialogs
        self.last_ok, self.last_error = True, ""
        self.zoom = zoom if zoom is not None else settings.load_zoom()
        self.dpi_factor = max(1.0, self.winfo_fpixels("1i") / 96.0)
        self.title("Smart Parking - Allocation and Billing")
        width = min(1440, self.winfo_screenwidth() - 40)
        height = min(860, self.winfo_screenheight() - 90)
        self.geometry(f"{width}x{height}+0+0")
        self.minsize(900, 560)
        self._shell = None
        self._current = "Dashboard"
        self._apply_scale()
        self._build_ui()
        self._bind_zoom_keys()

    # ------------------------------------------------------------ zoom and rebuild
    def _apply_scale(self):
        T.set_scale(self.zoom, self.dpi_factor)
        T.apply_theme(self)

    def _build_ui(self):
        """Create every widget. Called at start and again whenever the zoom level changes."""
        if self._shell is not None:
            self._shell.destroy()
        self._shell = tk.Frame(self, bg=T.BG)
        self._shell.pack(fill="both", expand=True)
        self._header()
        self.nav = NavBar(self._shell, TAB_NAMES, self.show_tab)
        self.nav.pack(fill="x")
        self.statusbar = StatusBar(self._shell)
        self.statusbar.pack(side="bottom", fill="x")
        self.page_area = tk.Frame(self._shell, bg=T.BG)
        self.page_area.pack(fill="both", expand=True)
        self.tabs, self._visible = {}, None
        builders = {"Dashboard": self._dashboard_tab, "Slot Search": self._search_tab, "Gate": self._gate_tab,
                    "Reservations": self._reservations_tab, "Billing": self._billing_tab,
                    "Customers": self._customers_tab, "Vehicles": self._vehicles_tab, "Passes": self._passes_tab,
                    "Tariffs": self._tariffs_tab, "Reports": self._reports_tab}
        for name in TAB_NAMES:
            page = ScrollPage(self.page_area)
            self.tabs[name] = page
            builders[name](page.inner)
        self.safe(self.load_lookups)
        self.nav.select(self._current if self._current in TAB_NAMES else "Dashboard")

    def set_zoom(self, percent, persist=True):
        levels = settings.ZOOM_LEVELS
        percent = min(levels, key=lambda v: abs(v - percent))
        if percent == self.zoom:
            return
        self.zoom = percent
        if persist:
            settings.save_zoom(percent)
        self.update_idletasks()
        self._apply_scale()
        self._build_ui()
        if percent > 110:
            self._make_room()
        self.notify(f"Zoom {percent}%   (Ctrl + / Ctrl - to change, Ctrl 0 to reset)", kind="info")

    def zoom_step(self, direction):
        levels = settings.ZOOM_LEVELS
        index = levels.index(self.zoom) if self.zoom in levels else levels.index(100)
        index = max(0, min(len(levels) - 1, index + direction))
        self.set_zoom(levels[index])

    def _make_room(self):
        """A bigger zoom needs a bigger window: maximise it where the system allows."""
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass

    def _bind_zoom_keys(self):
        for seq in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            self.bind_all(seq, lambda e: self.zoom_step(+1))
        for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.bind_all(seq, lambda e: self.zoom_step(-1))
        for seq in ("<Control-0>", "<Control-KP_0>"):
            self.bind_all(seq, lambda e: self.set_zoom(100))
        self.bind_all("<Control-MouseWheel>", lambda e: self.zoom_step(+1 if e.delta > 0 else -1))
        self.bind_all("<Control-Button-4>", lambda e: self.zoom_step(+1))
        self.bind_all("<Control-Button-5>", lambda e: self.zoom_step(-1))
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.bind_all("<Button-4>", lambda e: self._on_wheel(e, 1))
        self.bind_all("<Button-5>", lambda e: self._on_wheel(e, -1))

    def _on_wheel(self, event, direction=None):
        """Mouse wheel scrolls the page when it is taller than the window (tables scroll themselves)."""
        if isinstance(event.widget, ttk.Treeview) or self._visible is None:
            return
        step = direction if direction is not None else (1 if event.delta > 0 else -1)
        self.tabs[self._visible].scroll(-3 * step)

    # ----------------------------------------------------------------- plumbing
    def _header(self):
        bar = tk.Frame(self._shell, bg=T.NAVY, height=T.px(66))
        bar.pack(fill="x")
        bar.pack_propagate(False)
        size = T.px(44)
        logo = tk.Canvas(bar, width=size, height=size, bg=T.NAVY, highlightthickness=0)
        logo.create_polygon(5, 12, 12, 5, 32, 5, 39, 12, 39, 32, 32, 39, 12, 39, 5, 32, smooth=True, fill=T.TEAL, outline=T.TEAL)
        logo.create_text(22, 21, text="P", fill="#FFFFFF", font=T.font(18, "bold"))
        logo.create_rectangle(13, 34, 31, 37, fill=T.ACCENT, outline=T.ACCENT)
        logo.scale("all", 0, 0, size / 44, size / 44)
        logo.pack(side="left", padx=(T.XL, T.M), pady=T.px(10))
        titles = tk.Frame(bar, bg=T.NAVY)
        titles.pack(side="left")
        tk.Label(titles, text="Smart Parking Lot Allocation and Billing", bg=T.NAVY, fg="#FFFFFF",
                 font=T.font(16, "bold")).pack(anchor="w")
        tk.Label(titles, text="Parking management system", bg=T.NAVY, fg=T.NAVY_TEXT, font=T.font(9)).pack(anchor="w")

        clock = tk.Frame(bar, bg=T.NAVY)
        clock.pack(side="right", padx=T.XL)
        self.clock_time = tk.Label(clock, bg=T.NAVY, fg="#FFFFFF", font=T.font(15, "bold"), anchor="e")
        self.clock_time.pack(anchor="e")
        self.clock_date = tk.Label(clock, bg=T.NAVY, fg=T.NAVY_TEXT, font=T.font(9), anchor="e")
        self.clock_date.pack(anchor="e")

        zoom = tk.Frame(bar, bg=T.NAVY)
        zoom.pack(side="right", padx=(0, T.L))
        tk.Label(zoom, text="Zoom", bg=T.NAVY, fg=T.NAVY_TEXT, font=T.font(9)).pack(side="left", padx=(0, T.S))
        small = T.px(34)
        Btn(zoom, "A-", lambda: self.zoom_step(-1), "header", width=small, height=small, padx=T.px(6)).pack(side="left")
        Btn(zoom, f"{self.zoom}%", lambda: self.set_zoom(100), "header", width=T.px(58), height=small, padx=T.px(6)).pack(side="left", padx=T.XS)
        Btn(zoom, "A+", lambda: self.zoom_step(+1), "header", width=small, height=small, padx=T.px(6)).pack(side="left")
        self._tick()

    def _tick(self):
        try:
            now = datetime.now()
            self.clock_time.config(text=now.strftime("%H:%M"))
            self.clock_date.config(text=now.strftime("%A, %d %B %Y"))
        except tk.TclError:
            return  # the header was rebuilt; the new header starts its own clock
        self.after(15000, self._tick)

    def show_tab(self, name):
        if self._visible:
            self.tabs[self._visible].pack_forget()
        self._current = self._visible = name
        self.tabs[name].pack(fill="both", expand=True, padx=T.XL, pady=(T.L, T.M))
        if self.nav.current != name:
            self.nav.select(name)
            return
        self.refresh_current()

    def notify(self, message, error=False, kind=None):
        kind = kind or ("error" if error else "success")
        self.statusbar.set(message, kind)
        if error and self.dialogs:
            messagebox.showwarning("Cannot complete", message, parent=self)

    def safe(self, fn, *args, **kwargs):
        """Run fn; show a friendly message instead of crashing on any ParkingError."""
        self.last_ok, self.last_error = True, ""
        try:
            return fn(*args, **kwargs)
        except ParkingError as e:
            self.last_ok, self.last_error = False, str(e)
            self.notify(str(e), error=True)
        except Exception as e:  # last line of defence: never crash the screen
            self.last_ok, self.last_error = False, f"Unexpected problem: {e}"
            self.notify(self.last_error, error=True)
        return None

    def confirm(self, text):
        return messagebox.askyesno("Please confirm", text, parent=self) if self.dialogs else True

    # ---- small builders shared by every page
    def entry(self, parent, width=24):
        return ttk.Entry(parent, width=width, style="Modern.TEntry", font=T.font(10))

    def combo(self, parent, values, width=14):
        box = ttk.Combobox(parent, values=list(values), state="readonly", width=width,
                           style="Modern.TCombobox", font=T.font(10))
        box.current(0)
        return box

    def field(self, parent, label, row, col, widget=None, width=24, colspan=1):
        """Label above a control, laid out on a grid whose columns share extra width."""
        tk.Label(parent, text=label, bg=parent.cget("bg"), fg=T.MUTED, font=T.font(9, "bold"), anchor="w").grid(
            row=row * 2, column=col, columnspan=colspan, sticky="w", padx=(0, T.L), pady=(0 if row == 0 else T.M, 4))
        w = widget or self.entry(parent, width)
        w.grid(row=row * 2 + 1, column=col, columnspan=colspan, sticky="ew", padx=(0, T.L))
        parent.columnconfigure(col, weight=1)
        return w

    def button_row(self, parent, buttons, row, col=0, colspan=4):
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        frame.grid(row=row, column=col, columnspan=colspan, sticky="w", pady=(T.L, 0))
        for text, command, variant in buttons:
            Btn(frame, text, command, variant).pack(side="left", padx=(0, T.S))
        return frame

    def load_lookups(self):
        self.facilities = [(f["name"], f["facility_id"]) for f in self.svc.facilities()]
        self.types = [(t["type_name"], t["type_id"]) for t in self.svc.vehicle_types()]
        for pick, extra in ((self.sr_facility, True), (self.gt_facility, False), (self.rs_facility, False),
                            (self.tf_facility, False)):
            pick.set_items(([("All facilities", None)] if extra else []) + self.facilities)
        self.sr_type.set_items([("All vehicle types", None)] + [(n, n) for n, _ in self.types])
        self.tf_type.set_items(self.types)

    def refresh_current(self):
        refresher = {"Dashboard": self.refresh_dashboard, "Slot Search": self.do_search, "Gate": self.refresh_gate,
                     "Reservations": self.refresh_reservations, "Billing": self.refresh_bills,
                     "Customers": self.refresh_customers, "Vehicles": self.refresh_vehicles,
                     "Passes": self.refresh_passes, "Tariffs": self.refresh_tariffs,
                     "Reports": self.run_report}.get(self._current)
        if refresher:
            self.safe(refresher)

    # ---------------------------------------------------------------- dashboard
    def _dashboard_tab(self, f):
        f.columnconfigure(0, weight=1)
        tiles = tk.Frame(f, bg=T.BG)
        tiles.grid(row=0, column=0, sticky="ew")
        self.kpi, self._kpi_cards = {}, []
        spec = [("open_sessions", "Vehicles inside", "currently parked", T.INFO, "car", T.TINT["info"]),
                ("free_slots", "Free slots", "ready to allot", T.TEAL, "check", T.TINT["teal"]),
                ("occupied_slots", "Occupied slots", "in use now", T.NAVY, "parking", T.TINT["navy"]),
                ("unpaid_balance", "Unpaid amount", "outstanding (Rs)", T.WARNING, "rupee", T.TINT["warning"]),
                ("violations", "Violations", "need attention", T.ERROR, "warning", T.TINT["error"])]
        for key, title, caption, color, icon, tint in spec:
            card = KpiCard(tiles, title, caption, color, icon, tint)
            self.kpi[key] = card
            self._kpi_cards.append(card)
        tiles.bind("<Configure>", lambda e: self._reflow(tiles, self._kpi_cards, T.px(235), T.M, e.width))

        f.rowconfigure(1, weight=1)
        lower = tk.Frame(f, bg=T.BG)
        lower.grid(row=1, column=0, sticky="nsew", pady=(T.M, 0))
        self._lower = lower

        occ = Panel(lower, "Occupancy by floor", padding=T.M)
        Btn(occ.actions, "Refresh", lambda: self.safe(self.refresh_dashboard), "primary", height=T.px(32), padx=T.px(14)).pack(side="right")
        Btn(occ.actions, "Expire old reservations", self.do_expire, "secondary", height=T.px(32), padx=T.px(14)).pack(side="right", padx=(0, T.S))
        self.occ_table = OccupancyTable(occ.body)
        self.occ_table.pack(fill="both", expand=True)

        now = Panel(lower, "Vehicles inside now", padding=T.M)
        lower.bind("<Configure>", lambda e: self._dash_layout(occ, now, e.width))
        self.now_table = DataTable(now.body, [("reg_number", "Registration", 110), ("vehicle_type", "Type", 62),
                                              ("facility", "Facility", 150), ("floor_no", "Floor", 56),
                                              ("slot_no", "Slot", 56), ("entry_time", "Entered", 128),
                                              ("duration", "Duration", 86)], height=6,
                                   empty_text="No vehicles are inside right now")
        self.now_table.pack(fill="both", expand=True)

    @staticmethod
    def _reflow(container, widgets, min_width, gap, width):
        """Place widgets in as many equal columns as fit in `width` (used for cards)."""
        cols = max(1, min(len(widgets), width // min_width))
        for c in range(len(widgets)):
            container.columnconfigure(c, weight=0, uniform="")
        for c in range(cols):
            container.columnconfigure(c, weight=1, uniform="reflow")
        for i, w in enumerate(widgets):
            w.grid(row=i // cols, column=i % cols, sticky="nsew",
                   padx=(0 if i % cols == 0 else gap, 0), pady=(0 if i < cols else gap, 0))

    def _dash_layout(self, occ, now, width):
        """Occupancy and vehicle tables side by side when wide, stacked when zoomed or narrow."""
        wide = width >= T.px(1120)
        lower = self._lower
        for c in (0, 1):
            lower.columnconfigure(c, weight=0, uniform="")
        for r in (0, 1):
            lower.rowconfigure(r, weight=0)
        if wide:
            lower.columnconfigure(0, weight=1, uniform="dash")
            lower.columnconfigure(1, weight=1, uniform="dash")
            lower.rowconfigure(0, weight=1)
            occ.grid(row=0, column=0, sticky="nsew", padx=(0, T.M), pady=0)
            now.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        else:
            lower.columnconfigure(0, weight=1)
            lower.rowconfigure(1, weight=1)
            occ.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            now.grid(row=1, column=0, sticky="nsew", padx=0, pady=(T.M, 0))

    def refresh_dashboard(self):
        d = self.svc.dashboard()
        for key, card in self.kpi.items():
            val = d[key]
            card.set(f"{val:,.0f}" if isinstance(val, Decimal) else str(val))
        occ = self.svc.run_report("Occupancy by floor")[1]
        self.occ_table.load(occ)
        rows = self.svc.parked_now()
        for r in rows:
            r["duration"] = human_minutes(r["minutes_inside"])
        self.now_table.load(rows)

    def do_expire(self):
        n = self.safe(self.svc.expire_reservations)
        if n is not None:
            self.notify(f"{n} unused reservation(s) marked as expired.")
            self.safe(self.refresh_current)

    # -------------------------------------------------------------- slot search
    def _search_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        bar = Panel(f, "Find a slot")
        bar.grid(row=0, column=0, sticky="ew")
        form = bar.body
        self.sr_facility = self.field(form, "FACILITY", 0, 0, Pick(form, 28))
        self.sr_type = self.field(form, "VEHICLE TYPE", 0, 1, Pick(form, 20))
        self.sr_mode = self.field(form, "SHOW", 0, 2, self.combo(form, ["Free slots", "Under maintenance"], 22))
        Btn(form, "Search", lambda: self.safe(self.do_search), "primary").grid(row=1, column=3, sticky="s")
        info = tk.Frame(form, bg=T.CARD)
        info.grid(row=2, column=0, columnspan=4, sticky="w", pady=(T.M, 0))
        self.sr_count = Pill(info, "", "teal")
        self.sr_count.pack(side="left")
        for text, color in (("Available", T.SUCCESS), ("Under maintenance", T.WARNING)):
            dot = tk.Canvas(info, width=10, height=10, bg=T.CARD, highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=color, outline=color)
            dot.pack(side="left", padx=(T.L, 4))
            tk.Label(info, text=text, bg=T.CARD, fg=T.MUTED, font=T.font(9)).pack(side="left")

        res = Panel(f, "Results")
        res.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        Btn(res.actions, "Return selected slot to service", lambda: self.set_slot("AVAILABLE"), "secondary").pack(side="right")
        Btn(res.actions, "Set selected slot under maintenance", lambda: self.set_slot("MAINTENANCE"), "secondary").pack(side="right", padx=(0, T.S))
        self.sr_table = DataTable(res.body, [("facility", "Facility", 260), ("floor_no", "Floor", 80), ("zone_name", "Zone", 140),
                                             ("slot_no", "Slot", 100), ("type_name", "Suits", 120), ("slot_status", "Status", 150)],
                                  height=12, status_key="slot_status", empty_text="No slots match this search")
        self.sr_table.pack(fill="both", expand=True)

    def do_search(self):
        fid, tname = self.sr_facility.value(), self.sr_type.value()
        if self.sr_mode.get() == "Free slots":
            rows = self.svc.search_free_slots(fid, tname)
            status = "AVAILABLE"
            self.sr_count.set(f"{len(rows)} free slot(s)", "teal")
        else:
            rows = self.svc.list_maintenance_slots(fid, tname)
            status = "MAINTENANCE"
            self.sr_count.set(f"{len(rows)} slot(s) under maintenance", "warning")
        for r in rows:
            r["slot_status"] = status
        self.sr_table.load(rows)

    def set_slot(self, status):
        row = self.sr_table.selected()
        if row is None:
            self.notify("Select a slot in the table first.", error=True)
            return
        self.safe(self.svc.set_slot_status, row["slot_id"], status)
        if self.last_ok:
            self.notify("Slot is now under maintenance." if status == "MAINTENANCE" else "Slot returned to service.")
        self.safe(self.do_search)

    # --------------------------------------------------------------------- gate
    def _gate_tab(self, f):
        f.columnconfigure(0, weight=2, uniform="gate")
        f.columnconfigure(1, weight=3, uniform="gate")
        f.rowconfigure(0, weight=1)
        left = Panel(f, "Vehicle entry")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, T.L))
        form = left.body
        self.gt_reg = self.field(form, "REGISTRATION NUMBER", 0, 0)
        self.gt_reg.bind("<Return>", lambda e: self.do_enter())
        self.gt_facility = self.field(form, "FACILITY", 1, 0, Pick(form, 26))
        Btn(form, "Allow entry and allot slot", self.do_enter, "primary").grid(row=4, column=0, sticky="w", pady=(T.L, T.M))
        self.gt_entry_msg = ResultBox(form, "The allotted slot appears here.", 300)
        self.gt_entry_msg.grid(row=5, column=0, sticky="ew")
        tk.Label(form, text="A valid reservation or pass is applied automatically.", bg=T.CARD, fg=T.MUTED,
                 font=T.font(9), wraplength=T.px(300), justify="left").grid(row=6, column=0, sticky="w", pady=(T.M, 0))

        right = Panel(f, "Vehicle exit and billing")
        right.grid(row=0, column=1, sticky="nsew")
        self.gt_table = DataTable(right.body, [("session_id", "Session", 62), ("reg_number", "Registration", 118),
                                               ("vehicle_type", "Type", 62), ("facility", "Facility", 160),
                                               ("slot_no", "Slot", 52), ("entry_time", "Entered", 125),
                                               ("duration", "Duration", 80)], height=9,
                                  empty_text="No vehicles are inside")
        self.gt_table.pack(fill="both", expand=True)
        row = tk.Frame(right.body, bg=T.CARD)
        row.pack(fill="x", pady=(T.M, 0))
        tk.Label(row, text="Simulate stay (minutes, optional)", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="left")
        self.gt_sim = self.entry(row, 8)
        self.gt_sim.pack(side="left", padx=T.S)
        Btn(row, "Exit and generate bill", self.do_exit, "primary").pack(side="left", padx=(T.S, 0))
        self.gt_exit_msg = ResultBox(right.body, "The bill appears here after the vehicle exits.", 640)
        self.gt_exit_msg.pack(fill="x", pady=(T.M, 0))

    def refresh_gate(self):
        rows = self.svc.open_sessions()
        for r in rows:
            r["duration"] = human_minutes(r["minutes_inside"])
        self.gt_table.load(rows)

    def do_enter(self):
        res = self.safe(self.svc.enter_vehicle, self.gt_reg.get(), self.gt_facility.value())
        if res is None:
            self.gt_entry_msg.show(self.last_error, "error")
            return
        extra = []
        if res["reservation_id"]:
            extra.append(f"reservation #{res['reservation_id']} used")
        if res["pass_id"]:
            extra.append(f"pass #{res['pass_id']} applied (no parking charge)")
        text = f"Slot {res['slot_no']}, floor {res['floor_no']}, zone {res['zone_name']}\n{res['facility']}"
        if extra:
            text += "\n" + "; ".join(extra)
        self.gt_entry_msg.show(text, "success")
        self.notify(f"Entry recorded, session #{res['session_id']}.")
        self.gt_reg.delete(0, "end")
        self.safe(self.refresh_gate)

    def do_exit(self):
        row = self.gt_table.selected()
        if row is None:
            self.notify("Select the vehicle that is leaving.", error=True)
            return
        bill = self.safe(self.svc.exit_vehicle, row["session_id"], self.gt_sim.get())
        if bill is None:
            self.gt_exit_msg.show(self.last_error, "error")
            return
        hours = max(1, -(-bill["minutes"] // 60))
        how = "pass holder, no charge" if bill["pass_id"] else f"{hours} h at Rs {bill['rate_per_hour']}/h"
        self.gt_exit_msg.show(f"Bill #{bill['bill_id']} for {bill['reg_number']}: Rs {bill['amount']:.2f}  "
                              f"({bill['minutes']} min, {how})  status {bill['bill_status']}", "success")
        self.notify(f"Exit recorded. Bill #{bill['bill_id']} created.")
        self.gt_sim.delete(0, "end")
        self.safe(self.refresh_gate)

    # ------------------------------------------------------------- reservations
    def _reservations_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        top = Panel(f, "New reservation")
        top.grid(row=0, column=0, sticky="ew")
        form = top.body
        now = datetime.now().replace(second=0, microsecond=0)
        self.rs_reg = self.field(form, "REGISTRATION NUMBER", 0, 0)
        self.rs_facility = self.field(form, "FACILITY", 0, 1, Pick(form, 26))
        self.rs_start = self.field(form, "START (YYYY-MM-DD HH:MM)", 0, 2, width=20)
        self.rs_expiry = self.field(form, "EXPIRY (YYYY-MM-DD HH:MM)", 0, 3, width=20)
        self.rs_start.insert(0, (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))
        self.rs_expiry.insert(0, (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"))
        Btn(form, "Find slot and reserve", self.do_reserve, "primary").grid(row=1, column=4, sticky="s")
        self.rs_msg = ResultBox(form, "The reserved slot appears here.", 900)
        self.rs_msg.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(T.M, 0))

        lst = Panel(f, "Reservations")
        lst.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        Btn(lst.actions, "Expire old reservations", self.do_expire, "secondary").pack(side="right")
        Btn(lst.actions, "Cancel selected reservation", self.do_cancel, "danger").pack(side="right", padx=(0, T.S))
        self.rs_filter = self.combo(lst.actions, ["ALL", "ACTIVE", "USED", "EXPIRED", "CANCELLED"], 12)
        self.rs_filter.pack(side="right", padx=(0, T.M))
        tk.Label(lst.actions, text="Show", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="right", padx=(0, T.S))
        self.rs_filter.bind("<<ComboboxSelected>>", lambda e: self.safe(self.refresh_reservations))
        self.rs_table = DataTable(lst.body, [("reservation_id", "ID", 50), ("reg_number", "Vehicle", 120), ("owner", "Owner", 150),
                                             ("facility", "Facility", 190), ("floor_no", "Floor", 55), ("slot_no", "Slot", 60),
                                             ("start_time", "From", 130), ("expiry_time", "Until", 130), ("status", "Status", 110)],
                                  height=9, status_key="status", empty_text="No reservations found")
        self.rs_table.pack(fill="both", expand=True)

    def refresh_reservations(self):
        st = self.rs_filter.get()
        self.rs_table.load(self.svc.list_reservations(None if st == "ALL" else st))

    def do_reserve(self):
        res = self.safe(self.svc.create_reservation, self.rs_reg.get(), self.rs_facility.value(),
                        self.rs_start.get(), self.rs_expiry.get())
        if res:
            self.rs_msg.show(f"Reserved: slot {res['slot_no']}, floor {res['floor_no']}, zone {res['zone_name']} "
                             f"(reservation #{res['reservation_id']})", "success")
            self.notify("Reservation created.")
            self.safe(self.refresh_reservations)
        else:
            self.rs_msg.show(self.last_error, "error")

    def do_cancel(self):
        row = self.rs_table.selected()
        if row and self.confirm(f"Cancel reservation #{row['reservation_id']}?"):
            self.safe(self.svc.cancel_reservation, row["reservation_id"])
            if self.last_ok:
                self.notify("Reservation cancelled.")
            self.safe(self.refresh_reservations)
        elif row is None:
            self.notify("Select a reservation first.", error=True)

    # ------------------------------------------------------------------ billing
    def _billing_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        lst = Panel(f, "Bills")
        lst.grid(row=0, column=0, sticky="nsew")
        self.bl_filter = self.combo(lst.actions, ["ALL", "UNPAID", "PARTIAL", "PAID"], 12)
        self.bl_filter.pack(side="right")
        tk.Label(lst.actions, text="Show", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="right", padx=(0, T.S))
        self.bl_filter.bind("<<ComboboxSelected>>", lambda e: self.safe(self.refresh_bills))
        self.bl_table = DataTable(lst.body, [("bill_id", "Bill", 55), ("reg_number", "Vehicle", 120), ("facility", "Facility", 190),
                                             ("minutes", "Minutes", 80), ("amount", "Amount", 90), ("paid", "Paid", 90),
                                             ("balance", "Balance", 90), ("bill_status", "Status", 120), ("generated_at", "Billed at", 130)],
                                  height=9, on_select=self.on_bill_select, status_key="bill_status",
                                  empty_text="No bills found")
        self.bl_table.pack(fill="both", expand=True)

        pay = Panel(f, "Take a payment")
        pay.grid(row=1, column=0, sticky="ew", pady=(T.L, 0))
        body = pay.body
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        left = tk.Frame(body, bg=T.TINT["neutral"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, T.XL))
        tk.Label(left, text="OUTSTANDING BALANCE", bg=T.TINT["neutral"], fg=T.MUTED, font=T.font(9, "bold")).pack(anchor="w", padx=T.L, pady=(T.M, 0))
        self.bl_balance = tk.Label(left, text="Rs 0.00", bg=T.TINT["neutral"], fg=T.NAVY, font=T.font(24, "bold"))
        self.bl_balance.pack(anchor="w", padx=T.L)
        self.bl_info = tk.Label(left, text="Select a bill above.", bg=T.TINT["neutral"], fg=T.MUTED, font=T.font(9),
                                justify="left", anchor="w", wraplength=T.px(380))
        self.bl_info.pack(anchor="w", padx=T.L, pady=(0, T.M))
        right = tk.Frame(body, bg=T.CARD)
        right.grid(row=0, column=1, sticky="nsew")
        self.bl_amount = self.field(right, "AMOUNT (RS)", 0, 0, width=14)
        self.bl_method = self.field(right, "METHOD", 0, 1, self.combo(right, PAYMENT_METHODS, 12))
        Btn(right, "Pay", self.do_pay, "primary").grid(row=1, column=2, sticky="s", padx=(0, T.S))
        Btn(right, "Fill full balance", self.fill_balance, "secondary").grid(row=1, column=3, sticky="s")

    def refresh_bills(self):
        st = self.bl_filter.get()
        self.bl_table.load(self.svc.list_bills(None if st == "ALL" else st))

    def on_bill_select(self, row):
        if row:
            balance = row["balance"]
            color = T.ERROR if row["bill_status"] == "UNPAID" else T.WARNING if row["bill_status"] == "PARTIAL" else T.SUCCESS
            self.bl_balance.config(text=f"Rs {balance:.2f}", fg=color)
            self.bl_info.config(text=f"Bill #{row['bill_id']}  |  {row['reg_number']}\nAmount Rs {row['amount']:.2f}  |  "
                                     f"Paid Rs {row['paid']:.2f}  |  {row['bill_status']}", fg=T.TEXT)

    def fill_balance(self):
        row = self.bl_table.selected()
        if row:
            self.bl_amount.delete(0, "end")
            self.bl_amount.insert(0, f"{row['balance']:.2f}")

    def do_pay(self):
        row = self.bl_table.selected()
        if row is None:
            self.notify("Select a bill first.", error=True)
            return
        res = self.safe(self.svc.pay_bill, row["bill_id"], self.bl_amount.get(), self.bl_method.get())
        if res:
            self.notify(f"Payment recorded. Bill #{res['bill_id']} is now {res['bill_status']}.")
            self.bl_amount.delete(0, "end")
            self.safe(self.refresh_bills)

    # ---------------------------------------------------------------- customers
    def _customers_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        top = Panel(f, "Customer details")
        top.grid(row=0, column=0, sticky="ew")
        form = top.body
        self.cu_name = self.field(form, "NAME", 0, 0)
        self.cu_phone = self.field(form, "PHONE", 0, 1)
        self.cu_email = self.field(form, "EMAIL", 0, 2, width=30)
        self.cu_id = None
        self.button_row(form, [("Add", self.cu_add, "primary"), ("Update selected", self.cu_update, "secondary"),
                               ("Delete selected", self.cu_delete, "danger"), ("Clear", self.cu_clear, "ghost")], 2, colspan=3)
        lst = Panel(f, "Customers")
        lst.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        self.cu_search = self.entry(lst.actions, 28)
        self.cu_search.pack(side="right")
        tk.Label(lst.actions, text="Search", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="right", padx=(0, T.S))
        self.cu_search.bind("<KeyRelease>", lambda e: self.safe(self.refresh_customers))
        self.cu_table = DataTable(lst.body, [("customer_id", "ID", 55), ("name", "Name", 220), ("phone", "Phone", 130),
                                             ("email", "Email", 260), ("vehicles", "Vehicles", 80)], height=9,
                                  on_select=self.cu_pick, empty_text="No customers found")
        self.cu_table.pack(fill="both", expand=True)

    def refresh_customers(self):
        self.cu_table.load(self.svc.list_customers(self.cu_search.get()))
        self.customer_items = [(f"{c['customer_id']} - {c['name']}", c["customer_id"]) for c in self.svc.list_customers("")]
        for pick in (getattr(self, "vh_owner", None), getattr(self, "ps_customer", None)):
            if pick is not None:
                pick.set_items(self.customer_items)

    def cu_pick(self, row):
        if row:
            self.cu_id = row["customer_id"]
            for e, k in ((self.cu_name, "name"), (self.cu_phone, "phone"), (self.cu_email, "email")):
                e.delete(0, "end")
                e.insert(0, row[k])

    def cu_clear(self):
        self.cu_id = None
        for e in (self.cu_name, self.cu_phone, self.cu_email):
            e.delete(0, "end")

    def cu_add(self):
        if self.safe(self.svc.add_customer, self.cu_name.get(), self.cu_phone.get(), self.cu_email.get()):
            self.notify("Customer added.")
            self.cu_clear()
            self.safe(self.refresh_customers)

    def cu_update(self):
        if self.cu_id is None:
            self.notify("Select a customer in the table first.", error=True)
            return
        self.safe(self.svc.update_customer, self.cu_id, self.cu_name.get(), self.cu_phone.get(), self.cu_email.get())
        if self.last_ok:
            self.notify("Customer updated.")
        self.safe(self.refresh_customers)

    def cu_delete(self):
        if self.cu_id is None:
            self.notify("Select a customer in the table first.", error=True)
            return
        if self.confirm("Delete this customer?"):
            self.safe(self.svc.delete_customer, self.cu_id)
            if self.last_ok:
                self.notify("Customer deleted.")
                self.cu_clear()
            self.safe(self.refresh_customers)

    # ----------------------------------------------------------------- vehicles
    def _vehicles_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        top = Panel(f, "Vehicle details")
        top.grid(row=0, column=0, sticky="ew")
        form = top.body
        self.vh_reg = self.field(form, "REGISTRATION NUMBER", 0, 0)
        self.vh_owner = self.field(form, "OWNER", 0, 1, Pick(form, 28))
        self.vh_type = self.field(form, "VEHICLE TYPE", 0, 2, Pick(form, 16))
        self.vh_id = None
        self.button_row(form, [("Add", self.vh_add, "primary"), ("Update selected", self.vh_update, "secondary"),
                               ("Delete selected", self.vh_delete, "danger"),
                               ("Clear", lambda: self.vh_reg.delete(0, "end"), "ghost")], 2, colspan=3)
        lst = Panel(f, "Vehicles")
        lst.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        self.vh_search = self.entry(lst.actions, 28)
        self.vh_search.pack(side="right")
        tk.Label(lst.actions, text="Search registration or owner", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="right", padx=(0, T.S))
        self.vh_search.bind("<KeyRelease>", lambda e: self.safe(self.refresh_vehicles))
        self.vh_table = DataTable(lst.body, [("vehicle_id", "ID", 55), ("reg_number", "Registration", 160),
                                             ("vehicle_type", "Type", 100), ("owner", "Owner", 260)], height=9,
                                  on_select=self.vh_pick, empty_text="No vehicles found")
        self.vh_table.pack(fill="both", expand=True)

    def refresh_vehicles(self):
        self.safe(self.refresh_customers)
        self.vh_type.set_items([(n, i) for n, i in self.types])
        self.vh_table.load(self.svc.list_vehicles(self.vh_search.get()))

    def vh_pick(self, row):
        if row:
            self.vh_id = row["vehicle_id"]
            self.vh_reg.delete(0, "end")
            self.vh_reg.insert(0, row["reg_number"])
            for pick, val in ((self.vh_owner, row["customer_id"]), (self.vh_type, row["type_id"])):
                for label, value in pick.map.items():
                    if value == val:
                        pick.set(label)

    def vh_add(self):
        if self.safe(self.svc.add_vehicle, self.vh_owner.value(), self.vh_type.value(), self.vh_reg.get()):
            self.notify("Vehicle added.")
            self.vh_reg.delete(0, "end")
            self.safe(self.refresh_vehicles)

    def vh_update(self):
        if self.vh_id is None:
            self.notify("Select a vehicle in the table first.", error=True)
            return
        self.safe(self.svc.update_vehicle, self.vh_id, self.vh_owner.value(), self.vh_type.value(), self.vh_reg.get())
        if self.last_ok:
            self.notify("Vehicle updated.")
        self.safe(self.refresh_vehicles)

    def vh_delete(self):
        if self.vh_id is None:
            self.notify("Select a vehicle in the table first.", error=True)
            return
        if self.confirm("Delete this vehicle?"):
            self.safe(self.svc.delete_vehicle, self.vh_id)
            if self.last_ok:
                self.notify("Vehicle deleted.")
                self.vh_id = None
            self.safe(self.refresh_vehicles)

    # ------------------------------------------------------------------- passes
    def _passes_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        top = Panel(f, "Sell or renew a pass")
        top.grid(row=0, column=0, sticky="ew")
        form = top.body
        self.ps_customer = self.field(form, "CUSTOMER", 0, 0, Pick(form, 28))
        self.ps_plan = self.field(form, "PLAN", 0, 1, self.combo(form, list(PASS_PLANS), 16))
        self.ps_start = self.field(form, "START DATE (YYYY-MM-DD)", 0, 2, width=16)
        self.ps_start.insert(0, date.today().isoformat())
        self.ps_price = Pill(form, "", "info")
        self.ps_price.grid(row=1, column=3, sticky="sw", pady=(0, 4))
        self.ps_plan.bind("<<ComboboxSelected>>", self.show_price)
        self.show_price()
        self.button_row(form, [("Sell pass", self.ps_buy, "primary"), ("Renew selected pass", self.ps_renew, "secondary"),
                               ("Delete selected pass", self.ps_delete, "danger")], 2, colspan=4)
        lst = Panel(f, "Passes")
        lst.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        self.ps_table = DataTable(lst.body, [("pass_id", "Pass", 55), ("customer", "Holder", 180), ("pass_type", "Plan", 100),
                                             ("valid_from", "From", 110), ("valid_to", "To", 110), ("pass_state", "State", 120),
                                             ("visits", "Visits", 70), ("hours_parked", "Hours", 80), ("fee", "Fee (Rs)", 90)],
                                  height=9, status_key="pass_state", empty_text="No passes sold yet")
        self.ps_table.pack(fill="both", expand=True)

    def show_price(self, event=None):
        days, fee = PASS_PLANS[self.ps_plan.get()]
        self.ps_price.set(f"{days} days  |  Rs {fee}", "info")

    def refresh_passes(self):
        self.safe(self.refresh_customers)
        self.ps_table.load(self.svc.list_passes())

    def ps_buy(self):
        if self.safe(self.svc.buy_pass, self.ps_customer.value(), self.ps_plan.get(), self.ps_start.get()):
            self.notify("Pass sold.")
            self.safe(self.refresh_passes)

    def ps_renew(self):
        row = self.ps_table.selected()
        if row is None:
            self.notify("Select a pass first.", error=True)
            return
        if self.safe(self.svc.renew_pass, row["pass_id"]):
            self.notify("Pass renewed (a new pass was created after the old one ends).")
            self.safe(self.refresh_passes)

    def ps_delete(self):
        row = self.ps_table.selected()
        if row is None:
            self.notify("Select a pass first.", error=True)
            return
        if self.confirm(f"Delete pass #{row['pass_id']}?"):
            self.safe(self.svc.delete_pass, row["pass_id"])
            if self.last_ok:
                self.notify("Pass deleted.")
            self.safe(self.refresh_passes)

    # ------------------------------------------------------------------ tariffs
    def _tariffs_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        top = Panel(f, "Add or change a tariff")
        top.grid(row=0, column=0, sticky="ew")
        form = top.body
        self.tf_facility = self.field(form, "FACILITY", 0, 0, Pick(form, 26))
        self.tf_type = self.field(form, "VEHICLE TYPE", 0, 1, Pick(form, 14))
        self.tf_from = self.field(form, "EFFECTIVE FROM (YYYY-MM-DD)", 0, 2, width=16)
        self.tf_from.insert(0, date.today().isoformat())
        self.tf_rate = self.field(form, "RATE PER HOUR (RS)", 0, 3, width=14)
        self.tf_cap = self.field(form, "DAILY CAP (RS, BLANK = NONE)", 0, 4, width=14)
        self.button_row(form, [("Add tariff", self.tf_add, "primary"),
                               ("Update selected rate and cap", self.tf_update, "secondary")], 2, colspan=5)
        lst = Panel(f, "Tariffs")
        lst.grid(row=1, column=0, sticky="nsew", pady=(T.L, 0))
        self.tf_table = DataTable(lst.body, [("tariff_id", "ID", 55), ("facility", "Facility", 240), ("vehicle_type", "Type", 100),
                                             ("effective_from", "Effective from", 130), ("rate_per_hour", "Rate / hour (Rs)", 130),
                                             ("daily_cap", "Daily cap (Rs)", 130)], height=9, empty_text="No tariffs defined")
        self.tf_table.pack(fill="both", expand=True)

    def refresh_tariffs(self):
        self.tf_table.load(self.svc.list_tariffs())

    def tf_add(self):
        if self.safe(self.svc.add_tariff, self.tf_facility.value(), self.tf_type.value(), self.tf_from.get(),
                     self.tf_rate.get(), self.tf_cap.get()):
            self.notify("Tariff added. New stays use it from the effective date.")
            self.safe(self.refresh_tariffs)

    def tf_update(self):
        row = self.tf_table.selected()
        if row is None:
            self.notify("Select a tariff first.", error=True)
            return
        self.safe(self.svc.update_tariff, row["tariff_id"], self.tf_rate.get(), self.tf_cap.get())
        if self.last_ok:
            self.notify("Tariff updated.")
        self.safe(self.refresh_tariffs)

    # ------------------------------------------------------------------ reports
    def _reports_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1, minsize=190)
        res = Panel(f, "Report results", padding=T.M)
        res.grid(row=0, column=0, sticky="nsew")
        Btn(res.actions, "Export to CSV", self.do_export, "secondary", height=T.px(32), padx=T.px(14)).pack(side="right")
        Btn(res.actions, "Run", lambda: self.safe(self.run_report), "primary", height=T.px(32), padx=T.px(14)).pack(side="right", padx=(0, T.S))
        self.rp_name = self.combo(res.actions, list(REPORTS), 30)
        self.rp_name.pack(side="right", padx=(0, T.S))
        self.rp_name.bind("<<ComboboxSelected>>", lambda e: self.safe(self.run_report))
        tk.Label(res.actions, text="Choose a report", bg=T.CARD, fg=T.MUTED, font=T.font(9, "bold")).pack(side="right", padx=(0, T.S))
        self.rp_table = DataTable(res.body, [("x", "", 100)], height=5, empty_text="Choose a report and press Run")
        self.rp_table.pack(fill="both", expand=True)
        chart = Panel(f, "Chart", padding=T.S)
        chart.grid(row=1, column=0, sticky="ew", pady=(T.M, 0))
        self.rp_canvas = tk.Canvas(chart.body, height=190, bg=T.CARD, highlightthickness=0)
        self.rp_canvas.pack(fill="x")
        f.bind("<Configure>", self._fit_chart)
        self.rp_canvas.bind("<Configure>", lambda e: self._redraw_chart())
        self.rp_cols, self.rp_rows, self._chart_args = [], [], None

    def _fit_chart(self, event):
        """Give the chart about a third of the page, so tables keep their space on small screens."""
        height = int(max(120, min(220, event.height * 0.28)))
        if abs(int(self.rp_canvas.cget("height")) - height) > 6:
            self.rp_canvas.configure(height=height)

    def run_report(self):
        name = self.rp_name.get()
        cols, rows = self.svc.run_report(name)
        self.rp_cols, self.rp_rows = cols, rows
        width = max(90, min(200, 1100 // max(1, len(cols))))
        self.rp_table.status_key = next((k for k in ("pass_state", "bill_status", "state") if k in cols), None)
        self.rp_table.set_columns([(c, c.replace("_", " ").title(), width) for c in cols] or [("x", "No data", 200)])
        self.rp_table.load(rows)
        self.draw_chart(name, rows)
        self.notify(f"{name}: {len(rows)} row(s).")

    def draw_chart(self, name, rows):
        spec = CHARTS.get(name)
        if not spec or not rows:
            self._chart_args = None
            self.rp_canvas.delete("all")
            self.rp_canvas.create_text(20, 70, anchor="w", fill=T.MUTED, font=T.font(11),
                                       text="No chart for this report. Charts are drawn for Peak hours, Occupancy and Revenue reports.")
            return
        label_cols, value_col = spec
        labels = [" ".join(fmt(r[c]) for c in label_cols) for r in rows]
        values = [float(r[value_col] or 0) for r in rows]
        title = f"{name}: {value_col.replace('_', ' ')}"
        self._chart_args = (title, labels, values, name == "Peak hours")
        self._redraw_chart()

    def _redraw_chart(self):
        if self._chart_args:
            draw_bar_chart(self.rp_canvas, *self._chart_args)

    def do_export(self):
        if not self.rp_rows:
            self.notify("Run a report first.", error=True)
            return
        name = self.rp_name.get().lower().replace(" ", "_") + ".csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=name) if self.dialogs else name
        if path:
            export_csv(path, self.rp_cols, self.rp_rows)
            self.notify(f"Saved {len(self.rp_rows)} rows to {path}.")


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.svc.close(), app.destroy()))
    app.mainloop()
