"""Rebuilds the database, drives the real application window on a virtual screen and saves
the output screens to screenshots/.   Run:  xvfb-run -a -s "-screen 0 1480x900x24" python tools/make_screenshots.py
(needs Linux with xvfb and ImageMagick; on your own laptop simply run the app and take screenshots by hand)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.gui import App            # noqa: E402
from tools import reset_db         # noqa: E402

OUT = os.path.join(ROOT, "screenshots")
os.makedirs(OUT, exist_ok=True)
reset_db.reset()
app = App(dialogs=False, zoom=100)


def shot(name):
    for _ in range(3):
        app.update_idletasks()
        app.update()
    geometry = f"{app.winfo_width()}x{app.winfo_height()}+0+0"
    subprocess.run(["import", "-window", "root", "-crop", geometry, "+repage", os.path.join(OUT, name + ".png")], check=True)
    print("saved", name)


def tab(name):
    app.show_tab(name)
    app.update()


def pick(table, **match):
    for iid, row in table.rows.items():
        if all(row.get(k) == v for k, v in match.items()):
            table.tree.selection_set(iid)
            table.tree.see(iid)
            app.update()
            return row
    raise RuntimeError(f"row not found: {match}")


def put(entry, text):
    entry.delete(0, "end")
    entry.insert(0, text)


# 1 dashboard
tab("Dashboard"); app.refresh_dashboard(); shot("01_dashboard")

# 2 slot search
tab("Slot Search"); app.sr_facility.current(1); app.sr_type.current(2); app.do_search(); shot("02_slot_search")

# 3-4 gate entry and exit
tab("Gate"); put(app.gt_reg, "MH12AB3030"); app.gt_facility.current(0); app.do_enter(); shot("03_gate_entry")
app.refresh_gate(); pick(app.gt_table, reg_number="MH12AB3030"); put(app.gt_sim, "200"); app.do_exit(); shot("04_gate_exit_bill")

# 5 billing and part payment
tab("Billing"); app.refresh_bills(); row = pick(app.bl_table, reg_number="MH12AB3030")
put(app.bl_amount, "50"); app.bl_method.set("UPI"); app.do_pay(); app.on_bill_select(pick(app.bl_table, reg_number="MH12AB3030")); shot("05_billing_part_payment")

# 6 reservation
tab("Reservations"); put(app.rs_reg, "TS08GH7788"); app.rs_facility.current(0); app.do_reserve(); app.refresh_reservations(); shot("06_reservation")

# 7 customers CRUD
tab("Customers"); put(app.cu_name, "Kiran Kumar"); put(app.cu_phone, "9876543210"); put(app.cu_email, "kiran.kumar@example.com"); app.cu_add()
put(app.cu_search, "Kiran"); app.refresh_customers(); shot("07_customer_added")
app.cu_clear(); put(app.cu_search, ""); app.refresh_customers()

# 8 error handling screens
put(app.cu_name, "Test User"); put(app.cu_phone, "12345"); put(app.cu_email, "test@example.com"); app.cu_add(); shot("08_error_invalid_phone")
app.cu_clear(); pick(app.cu_table, customer_id=1); app.cu_delete(); shot("09_error_delete_customer_in_use")
tab("Gate"); put(app.gt_reg, "TS09FB4421"); app.gt_facility.current(0); app.do_enter(); shot("10_error_vehicle_already_inside")
tab("Reservations"); put(app.rs_reg, "TS99ZZ0000"); app.do_reserve(); shot("11_error_unknown_vehicle")

# 12 vehicles, passes, tariffs
tab("Vehicles"); app.refresh_vehicles(); shot("12_vehicles")
tab("Passes"); app.refresh_passes(); app.ps_customer.current(1); app.ps_plan.set("QUARTERLY"); app.show_price(); app.ps_buy(); shot("13_passes")
tab("Tariffs"); app.refresh_tariffs(); shot("14_tariffs")

# 15-18 reports
tab("Reports")
for name, fname in (("Peak hours", "15_report_peak_hours"), ("Violations", "16_report_violations"),
                    ("Revenue by facility", "17_report_revenue"), ("Occupancy by floor", "18_report_occupancy")):
    app.rp_name.set(name); app.run_report(); shot(fname)

app.destroy()
