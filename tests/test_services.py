"""Integration tests: they run against a real MySQL database.
The database is rebuilt from the SQL files before the tests start (tools/reset_db.py)."""
import os
import sys
import unittest
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.errors import ParkingError, ValidationError
from app.reports import REPORTS
from app.services import ParkingService
from tools import reset_db


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db.reset()
        cls.svc = ParkingService()

    @classmethod
    def tearDownClass(cls):
        cls.svc.close()

    def tomorrow(self, hour):
        d = date.today() + timedelta(days=1)
        return f"{d.isoformat()} {hour:02d}:00"

    # ---------------------------------------------------------- slot search
    def test_01_dashboard_and_search(self):
        d = self.svc.dashboard()
        self.assertEqual(d["open_sessions"], 5)
        cars = self.svc.search_free_slots(1, "Car")
        self.assertTrue(cars and all(r["type_name"] == "Car" for r in cars))
        everything = self.svc.search_free_slots()
        self.assertGreater(len(everything), len(cars))

    def test_02_slot_maintenance(self):
        slot = self.svc.search_free_slots(2, "Bike")[0]["slot_id"]
        self.svc.set_slot_status(slot, "MAINTENANCE")
        self.assertIn(slot, [r["slot_id"] for r in self.svc.list_maintenance_slots()])
        self.svc.set_slot_status(slot, "AVAILABLE")
        occupied = self.svc.parked_now()[0]
        with self.assertRaises(ParkingError):
            self.svc.set_slot_status(self.svc.db.query_one(
                "SELECT slot_id FROM slot WHERE status='OCCUPIED' LIMIT 1")["slot_id"], "MAINTENANCE")
        self.assertTrue(occupied)

    # ---------------------------------------------------- gate, billing, payment
    def test_03_entry_exit_billing_and_payment(self):
        res = self.svc.enter_vehicle("ts12 rs 1111", 2)  # car, Tech Park, Rs 25/hour
        self.assertEqual(res["facility"], "Tech Park Parking")
        slot_type = self.svc.db.query_one("SELECT type_name FROM v_slot_location WHERE slot_id=%s", (res["slot_id"],))
        self.assertEqual(slot_type["type_name"], "Car")
        with self.assertRaises(ParkingError) as ctx:
            self.svc.enter_vehicle("TS12RS1111", 2)
        self.assertIn("already parked", str(ctx.exception))
        bill = self.svc.exit_vehicle(res["session_id"], 200)  # 200 min -> 4 h * 25
        self.assertEqual(str(bill["amount"]), "100.00")
        self.assertEqual(bill["bill_status"], "UNPAID")
        bill = self.svc.pay_bill(bill["bill_id"], 40, "upi")
        self.assertEqual(bill["bill_status"], "PARTIAL")
        with self.assertRaises(ParkingError) as ctx:
            self.svc.pay_bill(bill["bill_id"], 100, "cash")
        self.assertIn("exceeds", str(ctx.exception))
        bill = self.svc.pay_bill(bill["bill_id"], 60, "cash")
        self.assertEqual(bill["bill_status"], "PAID")
        with self.assertRaises(ParkingError):
            self.svc.exit_vehicle(res["session_id"], 10)

    def test_04_minimum_one_hour_and_reservation_used(self):
        res = self.svc.enter_vehicle("TS13LM2020", 1)  # has an ACTIVE reservation covering now
        self.assertIsNotNone(res["reservation_id"])
        bill = self.svc.exit_vehicle(res["session_id"], 20)
        self.assertEqual(str(bill["amount"]), "30.00")  # 1 hour minimum at Rs 30

    def test_05_daily_cap(self):
        res = self.svc.enter_vehicle("MH12AB3030", 1)
        bill = self.svc.exit_vehicle(res["session_id"], 600)  # 10 h * 30 = 300, capped at 250
        self.assertEqual(str(bill["amount"]), "250.00")

    def test_06_pass_holder_pays_nothing(self):
        res = self.svc.enter_vehicle("TS09EA1234", 1)
        self.assertEqual(res["pass_id"], 1)
        bill = self.svc.exit_vehicle(res["session_id"], 120)
        self.assertEqual(str(bill["amount"]), "0.00")
        self.assertEqual(bill["bill_status"], "PAID")

    def test_07_unknown_vehicle_and_bad_input(self):
        with self.assertRaises(ParkingError):
            self.svc.enter_vehicle("TS01ZZ9999", 1)
        with self.assertRaises(ValidationError):
            self.svc.enter_vehicle("bad reg", 1)
        with self.assertRaises(ValidationError):
            self.svc.pay_bill(1, "abc", "CASH")
        with self.assertRaises(ValidationError):
            self.svc.pay_bill(1, 50, "cheque")

    # --------------------------------------------------------- reservations
    def test_08_reservation_flow(self):
        r1 = self.svc.create_reservation("TS08GH7788", 1, self.tomorrow(14), self.tomorrow(16))
        r2 = self.svc.create_reservation("AP28CD5521", 1, self.tomorrow(14), self.tomorrow(16))
        self.assertNotEqual(r1["slot_id"], r2["slot_id"])  # same time, different slots
        self.svc.cancel_reservation(r1["reservation_id"])
        row = [r for r in self.svc.list_reservations("CANCELLED") if r["reservation_id"] == r1["reservation_id"]]
        self.assertEqual(len(row), 1)
        with self.assertRaises(ParkingError):
            self.svc.cancel_reservation(r1["reservation_id"])
        with self.assertRaises(ValidationError):
            self.svc.create_reservation("TS08GH7788", 1, "2020-01-01 10:00", "2020-01-01 11:00")
        with self.assertRaises(ValidationError):
            self.svc.create_reservation("TS08GH7788", 1, self.tomorrow(16), self.tomorrow(14))

    def test_09_expire_reservations(self):
        self.assertIsInstance(self.svc.expire_reservations(), int)

    # ------------------------------------------------- customers and vehicles
    def test_10_customer_crud_and_errors(self):
        cid = self.svc.add_customer("Test Person", "9000000001", "test.person@example.com")
        with self.assertRaises(ParkingError) as ctx:
            self.svc.add_customer("Other Person", "9000000001", "other@example.com")
        self.assertIn("phone", str(ctx.exception).lower())
        with self.assertRaises(ValidationError):
            self.svc.add_customer("Bad Phone", "12345", "bad@example.com")
        self.svc.update_customer(cid, "Test Renamed", "9000000001", "test.person@example.com")
        self.assertEqual(self.svc.list_customers("Renamed")[0]["name"], "Test Renamed")
        self.svc.delete_customer(cid)
        self.assertEqual(self.svc.list_customers("Renamed"), [])
        with self.assertRaises(ParkingError) as ctx:  # customer 1 owns vehicles
            self.svc.delete_customer(1)
        self.assertIn("Cannot delete", str(ctx.exception))

    def test_11_vehicle_crud_and_errors(self):
        cid = self.svc.add_customer("Vehicle Owner", "9000000002", "vehicle.owner@example.com")
        vid = self.svc.add_vehicle(cid, 2, "ts 99 zz 0001")
        self.assertEqual(self.svc.find_vehicle("TS99ZZ0001")["vehicle_id"], vid)
        with self.assertRaises(ParkingError) as ctx:
            self.svc.add_vehicle(cid, 2, "TS99ZZ0001")
        self.assertIn("already exists", str(ctx.exception))
        with self.assertRaises(ValidationError):
            self.svc.add_vehicle(cid, 2, "NOPE")
        self.svc.update_vehicle(vid, cid, 1, "TS99ZZ0001")
        self.assertEqual(self.svc.list_vehicles("TS99ZZ0001")[0]["vehicle_type"], "Bike")
        self.svc.delete_vehicle(vid)
        self.svc.delete_customer(cid)

    # --------------------------------------------------------- passes, tariffs
    def test_12_pass_buy_renew_delete(self):
        pid = self.svc.buy_pass(2, "monthly", date.today().isoformat())
        new_id = self.svc.renew_pass(pid)
        self.assertGreater(new_id, pid)
        rows = {r["pass_id"]: r for r in self.svc.list_passes()}
        self.assertEqual(rows[pid]["pass_type"], "MONTHLY")
        self.assertGreater(rows[new_id]["valid_from"], rows[pid]["valid_to"])
        self.svc.delete_pass(new_id)
        self.svc.delete_pass(pid)
        with self.assertRaises(ValidationError):
            self.svc.buy_pass(2, "weekly", date.today().isoformat())

    def test_13_tariff_add_update_and_validation(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        tid = self.svc.add_tariff(1, 1, future, "12", "70")
        self.svc.update_tariff(tid, "15", "")
        row = [t for t in self.svc.list_tariffs() if t["tariff_id"] == tid][0]
        self.assertEqual(str(row["rate_per_hour"]), "15.00")
        self.assertIsNone(row["daily_cap"])
        with self.assertRaises(ParkingError):
            self.svc.add_tariff(1, 1, future, "12", "70")  # duplicate
        with self.assertRaises(ValidationError):
            self.svc.add_tariff(1, 1, future, "-3", "")

    # -------------------------------------------------------------- reports
    def test_14_every_report_runs(self):
        for name in REPORTS:
            cols, rows = self.svc.run_report(name)
            self.assertIsInstance(cols, list, name)
        cols, rows = self.svc.run_report("Revenue by facility")
        self.assertEqual(len(rows), 2)

    def test_15_database_errors_become_friendly(self):
        with self.assertRaises(ParkingError) as ctx:
            self.svc.db.execute("INSERT INTO tariff (facility_id, type_id, effective_from, rate_per_hour) "
                                "VALUES (1, 1, '2030-01-01', -5)")
        self.assertIn("greater than zero", str(ctx.exception))

    def test_16_failed_billing_rolls_back_the_exit(self):
        """Transaction check: a vehicle type with no tariff cannot be billed, so the exit must be undone."""
        db = self.svc.db
        db.execute("INSERT INTO vehicle_type (type_name) VALUES ('Bus')")
        type_id = db.query_one("SELECT type_id FROM vehicle_type WHERE type_name='Bus'")["type_id"]
        zone_id = db.query_one("SELECT zone_id FROM zone WHERE zone_name='G-TRK' LIMIT 1")["zone_id"]
        db.execute("INSERT INTO slot (zone_id, type_id, slot_no) VALUES (%s, %s, 'X99')", (zone_id, type_id))
        cid = self.svc.add_customer("Bus Owner", "9000000003", "bus.owner@example.com")
        self.svc.add_vehicle(cid, type_id, "TS88BB0001")
        res = self.svc.enter_vehicle("TS88BB0001", 1)
        with self.assertRaises(ParkingError) as ctx:
            self.svc.exit_vehicle(res["session_id"], 60)
        self.assertIn("No tariff", str(ctx.exception))
        row = db.query_one("SELECT exit_time FROM parking_session WHERE session_id=%s", (res["session_id"],))
        self.assertIsNone(row["exit_time"], "exit time must be rolled back when billing fails")
        self.assertIsNone(db.query_one("SELECT bill_id FROM bill WHERE session_id=%s", (res["session_id"],)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
