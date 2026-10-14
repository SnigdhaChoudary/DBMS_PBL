"""Business operations used by the screen. Every function validates its input, then
calls the database. The database enforces the business rules a second time."""
from datetime import datetime, timedelta, date

from . import validators as v
from .config import PASS_PLANS, PAYMENT_METHODS
from .db import Database
from .errors import ParkingError
from .reports import REPORTS


class ParkingService:
    def __init__(self, db=None):
        self.db = db or Database()

    # ------------------------------------------------------------------ lookups
    def facilities(self):
        return self.db.query("SELECT facility_id, name FROM facility ORDER BY name")

    def vehicle_types(self):
        return self.db.query("SELECT type_id, type_name FROM vehicle_type ORDER BY type_id")

    # ---------------------------------------------------------------- dashboard
    def dashboard(self):
        q = self.db.query_one
        return {
            "open_sessions": q("SELECT COUNT(*) AS n FROM parking_session WHERE exit_time IS NULL")["n"],
            "free_slots": q("SELECT COUNT(*) AS n FROM v_free_slots")["n"],
            "occupied_slots": q("SELECT COUNT(*) AS n FROM slot WHERE status='OCCUPIED'")["n"],
            "unpaid_balance": q("SELECT COALESCE(SUM(balance),0) AS n FROM v_bill_details WHERE balance > 0")["n"],
            "violations": q("SELECT COUNT(*) AS n FROM v_violations")["n"],
        }

    def parked_now(self):
        return self.db.query(
            "SELECT ps.session_id, v.reg_number, vt.type_name AS vehicle_type, l.facility, l.floor_no, l.slot_no, "
            "ps.entry_time, TIMESTAMPDIFF(MINUTE, ps.entry_time, NOW()) AS minutes_inside "
            "FROM parking_session ps JOIN vehicle v ON v.vehicle_id = ps.vehicle_id "
            "JOIN vehicle_type vt ON vt.type_id = v.type_id JOIN v_slot_location l ON l.slot_id = ps.slot_id "
            "WHERE ps.exit_time IS NULL ORDER BY ps.entry_time")

    # -------------------------------------------------------------- slot search
    def search_free_slots(self, facility_id=None, type_name=None):
        return self.db.query(
            "SELECT f.slot_id, f.facility, f.floor_no, f.zone_name, f.slot_no, f.type_name "
            "FROM v_free_slots f JOIN v_slot_location l ON l.slot_id = f.slot_id "
            "WHERE (%s IS NULL OR l.facility_id = %s) AND (%s IS NULL OR f.type_name = %s) "
            "ORDER BY f.facility, f.floor_no, f.slot_no",
            (facility_id, facility_id, type_name, type_name))

    def list_maintenance_slots(self, facility_id=None, type_name=None):
        return self.db.query(
            "SELECT slot_id, facility, floor_no, zone_name, slot_no, type_name FROM v_slot_location "
            "WHERE status = 'MAINTENANCE' AND (%s IS NULL OR facility_id = %s) AND (%s IS NULL OR type_name = %s) "
            "ORDER BY facility, floor_no, slot_no", (facility_id, facility_id, type_name, type_name))

    def set_slot_status(self, slot_id, status):
        slot_id = v.require_id(slot_id, "slot")
        status = v.clean_choice(status, ("AVAILABLE", "MAINTENANCE"), "Status")
        needed = "MAINTENANCE" if status == "AVAILABLE" else "AVAILABLE"
        n, _ = self.db.execute("UPDATE slot SET status = %s WHERE slot_id = %s AND status = %s",
                               (status, slot_id, needed))
        if n == 0:
            raise ParkingError("Slot not changed: an occupied slot cannot be switched, "
                               "and it must already be in the opposite state.")

    # ---------------------------------------------------------------- customers
    def list_customers(self, text=""):
        like = f"%{text.strip()}%"
        return self.db.query(
            "SELECT c.customer_id, c.name, c.phone, c.email, COUNT(v.vehicle_id) AS vehicles "
            "FROM customer c LEFT JOIN vehicle v ON v.customer_id = c.customer_id "
            "WHERE c.name LIKE %s OR c.phone LIKE %s OR c.email LIKE %s "
            "GROUP BY c.customer_id, c.name, c.phone, c.email ORDER BY c.customer_id", (like, like, like))

    def add_customer(self, name, phone, email):
        _, new_id = self.db.execute("INSERT INTO customer (name, phone, email) VALUES (%s, %s, %s)",
                                    (v.clean_name(name), v.clean_phone(phone), v.clean_email(email)))
        return new_id

    def update_customer(self, customer_id, name, phone, email):
        customer_id = v.require_id(customer_id, "customer")
        self.db.execute("UPDATE customer SET name=%s, phone=%s, email=%s WHERE customer_id=%s",
                        (v.clean_name(name), v.clean_phone(phone), v.clean_email(email), customer_id))

    def delete_customer(self, customer_id):
        customer_id = v.require_id(customer_id, "customer")
        n, _ = self.db.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        if n == 0:
            raise ParkingError("Customer not found.")

    # ----------------------------------------------------------------- vehicles
    def list_vehicles(self, text=""):
        like = f"%{text.strip().upper()}%"
        like2 = f"%{text.strip()}%"
        return self.db.query(
            "SELECT v.vehicle_id, v.reg_number, vt.type_name AS vehicle_type, c.name AS owner, v.customer_id, v.type_id "
            "FROM vehicle v JOIN customer c ON c.customer_id = v.customer_id "
            "JOIN vehicle_type vt ON vt.type_id = v.type_id "
            "WHERE v.reg_number LIKE %s OR c.name LIKE %s ORDER BY v.vehicle_id", (like, like2))

    def find_vehicle(self, reg):
        row = self.db.query_one("SELECT vehicle_id, customer_id, type_id, reg_number FROM vehicle WHERE reg_number = %s",
                                (v.clean_reg(reg),))
        if row is None:
            raise ParkingError("No vehicle with that registration number. Add it on the Vehicles tab first.")
        return row

    def add_vehicle(self, customer_id, type_id, reg):
        customer_id = v.require_id(customer_id, "owner")
        type_id = v.require_id(type_id, "vehicle type")
        _, new_id = self.db.execute("INSERT INTO vehicle (customer_id, type_id, reg_number) VALUES (%s, %s, %s)",
                                    (customer_id, type_id, v.clean_reg(reg)))
        return new_id

    def update_vehicle(self, vehicle_id, customer_id, type_id, reg):
        vehicle_id = v.require_id(vehicle_id, "vehicle")
        self.db.execute("UPDATE vehicle SET customer_id=%s, type_id=%s, reg_number=%s WHERE vehicle_id=%s",
                        (v.require_id(customer_id, "owner"), v.require_id(type_id, "vehicle type"),
                         v.clean_reg(reg), vehicle_id))

    def delete_vehicle(self, vehicle_id):
        vehicle_id = v.require_id(vehicle_id, "vehicle")
        n, _ = self.db.execute("DELETE FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
        if n == 0:
            raise ParkingError("Vehicle not found.")

    # ------------------------------------------------------------- reservations
    def list_reservations(self, status=None):
        return self.db.query(
            "SELECT r.reservation_id, v.reg_number, c.name AS owner, l.facility, l.floor_no, l.slot_no, "
            "r.start_time, r.expiry_time, r.status "
            "FROM reservation r JOIN vehicle v ON v.vehicle_id = r.vehicle_id "
            "JOIN customer c ON c.customer_id = v.customer_id JOIN v_slot_location l ON l.slot_id = r.slot_id "
            "WHERE (%s IS NULL OR r.status = %s) ORDER BY r.reservation_id DESC LIMIT 200", (status, status))

    def find_slot_for_window(self, vehicle_id, facility_id, start, expiry):
        row = self.db.query_one(
            "SELECT s.slot_id FROM slot s JOIN zone z ON z.zone_id = s.zone_id JOIN floor f ON f.floor_id = z.floor_id "
            "JOIN vehicle v ON v.type_id = s.type_id AND v.vehicle_id = %s "
            "WHERE f.facility_id = %s AND s.status <> 'MAINTENANCE' "
            "AND NOT EXISTS (SELECT 1 FROM reservation r WHERE r.slot_id = s.slot_id AND r.status = 'ACTIVE' "
            "                AND %s < r.expiry_time AND %s > r.start_time) "
            "AND NOT EXISTS (SELECT 1 FROM parking_session p WHERE p.slot_id = s.slot_id "
            "                AND p.entry_time < %s AND COALESCE(p.exit_time, '9999-12-31') > %s) "
            "ORDER BY f.floor_no, s.slot_id LIMIT 1", (vehicle_id, facility_id, start, expiry, expiry, start))
        return row["slot_id"] if row else None

    def create_reservation(self, reg, facility_id, start_text, expiry_text):
        vehicle = self.find_vehicle(reg)
        facility_id = v.require_id(facility_id, "facility")
        start = v.parse_datetime(start_text, "Start time")
        expiry = v.parse_datetime(expiry_text, "Expiry time")
        if expiry <= start:
            raise v.ValidationError("Expiry time must be after the start time.")
        if expiry - start > timedelta(hours=24):
            raise v.ValidationError("A reservation can cover at most 24 hours.")
        if start < datetime.now() - timedelta(minutes=5):
            raise v.ValidationError("Start time cannot be in the past.")
        slot_id = self.find_slot_for_window(vehicle["vehicle_id"], facility_id, start, expiry)
        if slot_id is None:
            raise ParkingError("No free slot of this vehicle's type is available for that period.")
        _, new_id = self.db.execute(
            "INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (%s, %s, %s, %s)",
            (vehicle["vehicle_id"], slot_id, start, expiry))
        loc = self.db.query_one("SELECT facility, floor_no, zone_name, slot_no FROM v_slot_location WHERE slot_id=%s", (slot_id,))
        return {"reservation_id": new_id, "slot_id": slot_id, **loc}

    def cancel_reservation(self, reservation_id):
        reservation_id = v.require_id(reservation_id, "reservation")
        n, _ = self.db.execute("UPDATE reservation SET status='CANCELLED' WHERE reservation_id=%s AND status='ACTIVE'",
                               (reservation_id,))
        if n == 0:
            raise ParkingError("Only an ACTIVE reservation can be cancelled.")

    def expire_reservations(self):
        return self.db.call("sp_expire_reservations")[0][0]["reservations_expired"]

    # --------------------------------------------------------------------- gate
    def find_active_reservation(self, vehicle_id):
        return self.db.query_one(
            "SELECT reservation_id FROM reservation WHERE vehicle_id=%s AND status='ACTIVE' "
            "AND NOW() BETWEEN start_time AND expiry_time LIMIT 1", (vehicle_id,))

    def find_valid_pass(self, customer_id):
        return self.db.query_one(
            "SELECT pass_id FROM pass WHERE customer_id=%s AND CURDATE() BETWEEN valid_from AND valid_to "
            "ORDER BY valid_to DESC LIMIT 1", (customer_id,))

    def enter_vehicle(self, reg, facility_id):
        """Gate entry: uses a reservation or a pass automatically if the vehicle has a valid one."""
        vehicle = self.find_vehicle(reg)
        facility_id = v.require_id(facility_id, "facility")
        resv = self.find_active_reservation(vehicle["vehicle_id"])
        pass_row = self.find_valid_pass(vehicle["customer_id"])
        resv_id = resv["reservation_id"] if resv else None
        pass_id = pass_row["pass_id"] if pass_row else None
        res = self.db.call("sp_vehicle_entry", (vehicle["vehicle_id"], facility_id, resv_id, pass_id))[0][0]
        loc = self.db.query_one("SELECT facility, floor_no, zone_name, slot_no FROM v_slot_location WHERE slot_id=%s",
                                (res["allotted_slot_id"],))
        return {"session_id": res["session_id"], "slot_id": res["allotted_slot_id"],
                "reservation_id": resv_id, "pass_id": pass_id, **loc}

    def open_sessions(self):
        return self.parked_now()

    def exit_vehicle(self, session_id, simulate_minutes=None):
        """Gate exit: closes the stay and creates the bill. simulate_minutes is for demos and tests."""
        session_id = v.require_id(session_id, "session")
        row = self.db.query_one("SELECT entry_time, exit_time FROM parking_session WHERE session_id=%s", (session_id,))
        if row is None:
            raise ParkingError("Session not found.")
        if row["exit_time"] is not None:
            raise ParkingError("This vehicle has already left.")
        if simulate_minutes not in (None, ""):
            minutes = v.positive_int(simulate_minutes, 1, 2880, "Simulated stay (minutes)")
            exit_time = row["entry_time"] + timedelta(minutes=minutes)
        else:  # real exit: now, but never earlier than one minute after entry
            exit_time = self.db.query_one("SELECT GREATEST(NOW(), %s + INTERVAL 1 MINUTE) AS t",
                                          (row["entry_time"],))["t"]
        bill = self.db.call("sp_vehicle_exit", (session_id, exit_time))[0][0]
        return self.bill_detail(bill["bill_id"])

    # ------------------------------------------------------------------ billing
    _BILL_SQL = (
        "SELECT b.bill_id, v.reg_number, l.facility, TIMESTAMPDIFF(MINUTE, ps.entry_time, ps.exit_time) AS minutes, "
        "t.rate_per_hour, b.amount, COALESCE(p.paid, 0) AS paid, b.amount - COALESCE(p.paid, 0) AS balance, "
        "b.bill_status, b.generated_at, ps.pass_id "
        "FROM bill b JOIN parking_session ps ON ps.session_id = b.session_id "
        "JOIN vehicle v ON v.vehicle_id = ps.vehicle_id JOIN v_slot_location l ON l.slot_id = ps.slot_id "
        "JOIN tariff t ON t.tariff_id = b.tariff_id "
        "LEFT JOIN (SELECT bill_id, SUM(amount_paid) AS paid FROM payment GROUP BY bill_id) p ON p.bill_id = b.bill_id ")

    def list_bills(self, status=None):
        return self.db.query(self._BILL_SQL + "WHERE (%s IS NULL OR b.bill_status = %s) "
                             "ORDER BY b.bill_id DESC LIMIT 200", (status, status))

    def bill_detail(self, bill_id):
        row = self.db.query_one(self._BILL_SQL + "WHERE b.bill_id = %s", (bill_id,))
        if row is None:
            raise ParkingError("Bill not found.")
        return row

    def pay_bill(self, bill_id, amount, method):
        bill_id = v.require_id(bill_id, "bill")
        amount = v.positive_money(amount)
        method = v.clean_choice(method, PAYMENT_METHODS, "Payment method")
        self.db.call("sp_make_payment", (bill_id, amount, method))
        return self.bill_detail(bill_id)

    # ------------------------------------------------------------------- passes
    def list_passes(self):
        return self.db.query(
            "SELECT u.pass_id, u.customer, u.pass_type, u.valid_from, u.valid_to, u.pass_state, u.visits, "
            "u.hours_parked, u.fee FROM v_pass_usage u ORDER BY u.pass_id DESC")

    def buy_pass(self, customer_id, plan, start_text):
        customer_id = v.require_id(customer_id, "customer")
        plan = v.clean_choice(plan, tuple(PASS_PLANS), "Pass plan")
        start = v.parse_date(start_text, "Start date")
        days, fee = PASS_PLANS[plan]
        _, new_id = self.db.execute(
            "INSERT INTO pass (customer_id, pass_type, valid_from, valid_to, fee) VALUES (%s, %s, %s, %s, %s)",
            (customer_id, plan, start, start + timedelta(days=days - 1), fee))
        return new_id

    def renew_pass(self, pass_id):
        pass_id = v.require_id(pass_id, "pass")
        old = self.db.query_one("SELECT customer_id, pass_type, valid_to FROM pass WHERE pass_id=%s", (pass_id,))
        if old is None:
            raise ParkingError("Pass not found.")
        start = max(date.today(), old["valid_to"] + timedelta(days=1))
        return self.buy_pass(old["customer_id"], old["pass_type"], start.isoformat())

    def delete_pass(self, pass_id):
        pass_id = v.require_id(pass_id, "pass")
        n, _ = self.db.execute("DELETE FROM pass WHERE pass_id=%s", (pass_id,))
        if n == 0:
            raise ParkingError("Pass not found.")

    # ------------------------------------------------------------------ tariffs
    def list_tariffs(self):
        return self.db.query(
            "SELECT t.tariff_id, f.name AS facility, vt.type_name AS vehicle_type, t.effective_from, "
            "t.rate_per_hour, t.daily_cap FROM tariff t JOIN facility f ON f.facility_id = t.facility_id "
            "JOIN vehicle_type vt ON vt.type_id = t.type_id ORDER BY f.name, vt.type_id, t.effective_from DESC")

    def add_tariff(self, facility_id, type_id, effective_from, rate, cap):
        rate = v.positive_money(rate, 5000)
        cap = v.positive_money(cap, 50000) if str(cap).strip() else None
        _, new_id = self.db.execute(
            "INSERT INTO tariff (facility_id, type_id, effective_from, rate_per_hour, daily_cap) VALUES (%s,%s,%s,%s,%s)",
            (v.require_id(facility_id, "facility"), v.require_id(type_id, "vehicle type"),
             v.parse_date(effective_from, "Effective from"), rate, cap))
        return new_id

    def update_tariff(self, tariff_id, rate, cap):
        tariff_id = v.require_id(tariff_id, "tariff")
        rate = v.positive_money(rate, 5000)
        cap = v.positive_money(cap, 50000) if str(cap).strip() else None
        self.db.execute("UPDATE tariff SET rate_per_hour=%s, daily_cap=%s WHERE tariff_id=%s", (rate, cap, tariff_id))

    # ------------------------------------------------------------------ reports
    def run_report(self, name):
        if name not in REPORTS:
            raise ParkingError("Unknown report.")
        rows = self.db.query(REPORTS[name])
        columns = list(rows[0].keys()) if rows else []
        return columns, rows

    def close(self):
        self.db.close()
