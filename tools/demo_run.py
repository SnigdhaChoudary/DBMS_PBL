"""Console walk-through of the whole system using the same service layer as the screen.
    python tools/demo_run.py
Rebuilds the database first, so the output is repeatable."""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.errors import ParkingError          # noqa: E402
from app.services import ParkingService      # noqa: E402
from tools import reset_db                   # noqa: E402


def show(title):
    print(f"\n=== {title}")


def attempt(label, fn, *args):
    try:
        out = fn(*args)
        print(f"  OK    {label}")
        return out
    except ParkingError as e:
        print(f"  BLOCKED  {label} -> {e}")


reset_db.reset()
svc = ParkingService()

show("1. Dashboard")
print(" ", {k: str(v) for k, v in svc.dashboard().items()})

show("2. Slot search: free car slots in Lakeview Mall Parking")
rows = svc.search_free_slots(1, "Car")
print(f"  {len(rows)} free; first three:", [(r["floor_no"], r["zone_name"], r["slot_no"]) for r in rows[:3]])

show("3. Gate entry and slot allocation")
res = attempt("enter MH12AB3030 (car)", svc.enter_vehicle, "MH12AB3030", 1)
print(f"  allotted: floor {res['floor_no']}, zone {res['zone_name']}, slot {res['slot_no']}")
attempt("enter MH12AB3030 again", svc.enter_vehicle, "MH12AB3030", 1)
attempt("enter an unregistered vehicle", svc.enter_vehicle, "TS01ZZ9999", 1)
attempt("enter with a badly typed number", svc.enter_vehicle, "hello", 1)

show("4. Gate exit, duration billing (demo stay of 200 minutes)")
bill = svc.exit_vehicle(res["session_id"], 200)
print(f"  bill #{bill['bill_id']}: {bill['minutes']} min at Rs {bill['rate_per_hour']}/h = Rs {bill['amount']} ({bill['bill_status']})")

show("5. Payments")
b = svc.pay_bill(bill["bill_id"], 50, "UPI")
print(f"  paid 50 by UPI -> {b['bill_status']}, balance {b['balance']}")
attempt("pay 500 on a balance of 70", svc.pay_bill, bill["bill_id"], 500, "CASH")
b = svc.pay_bill(bill["bill_id"], 70, "CASH")
print(f"  paid 70 in cash -> {b['bill_status']}")

show("6. Pass holder (TS09EA1234 has an active monthly pass)")
r = svc.enter_vehicle("TS09EA1234", 1)
b = svc.exit_vehicle(r["session_id"], 120)
print(f"  pass #{r['pass_id']} applied, bill Rs {b['amount']} ({b['bill_status']})")

show("7. Reservation")
d = (date.today() + timedelta(days=1)).isoformat()
rv = attempt("reserve for TS08GH7788 tomorrow 10:00-12:00", svc.create_reservation, "TS08GH7788", 1, f"{d} 10:00", f"{d} 12:00")
print(f"  slot {rv['slot_no']}, floor {rv['floor_no']}, reservation #{rv['reservation_id']}")
attempt("reserve in the past", svc.create_reservation, "TS08GH7788", 1, "2020-01-01 10:00", "2020-01-01 11:00")
svc.cancel_reservation(rv["reservation_id"])
print("  reservation cancelled")

show("8. Customer CRUD and validation")
cid = svc.add_customer("Demo Person", "9000011111", "demo.person@example.com")
print(f"  created customer #{cid}")
attempt("duplicate phone", svc.add_customer, "Someone Else", "9000011111", "else@example.com")
attempt("invalid phone", svc.add_customer, "Bad Phone", "12345", "bad@example.com")
svc.update_customer(cid, "Demo Renamed", "9000011111", "demo.person@example.com")
print("  updated to:", svc.list_customers("Demo")[0]["name"])
svc.delete_customer(cid)
print("  deleted")
attempt("delete a customer who owns vehicles", svc.delete_customer, 1)

show("9. Reports")
for name in ("Occupancy by floor", "Violations", "Revenue by facility"):
    cols, rows = svc.run_report(name)
    print(f"  {name}: {len(rows)} row(s); first: {dict(list(rows[0].items())[:4]) if rows else '-'}")
svc.close()
