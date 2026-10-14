"""Report definitions. Each report is one SQL query over the views from sql/03_views.sql."""
import csv

REPORTS = {
    "Occupancy by floor": (
        "SELECT facility, floor_no, total_slots, occupied, available, maintenance, occupancy_pct "
        "FROM v_occupancy ORDER BY facility, floor_no"),
    "Free slots now": (
        "SELECT facility, type_name AS vehicle_type, COUNT(*) AS free_slots "
        "FROM v_free_slots GROUP BY facility, type_name ORDER BY facility, type_name"),
    "Peak hours": (
        "SELECT hour_of_day, entries, busy_rank FROM v_peak_hours ORDER BY hour_of_day"),
    "Longest stays": (
        "SELECT session_id, reg_number, type_name AS vehicle_type, facility, state, minutes_parked "
        "FROM v_session_duration ORDER BY minutes_parked DESC LIMIT 20"),
    "Pass usage": (
        "SELECT pass_id, customer, pass_type, valid_from, valid_to, pass_state, visits, hours_parked, fee "
        "FROM v_pass_usage ORDER BY pass_id"),
    "Violations": (
        "SELECT violation, session_id, reg_number, detail FROM v_violations ORDER BY violation, session_id"),
    "Revenue by day": (
        "SELECT pay_date, facility, payments, collected FROM v_revenue_daily "
        "ORDER BY pay_date DESC, facility LIMIT 30"),
    "Revenue by facility": (
        "SELECT l.facility, COUNT(*) AS bills, SUM(b.amount) AS billed, "
        "COALESCE(SUM(p.paid),0) AS collected, SUM(b.amount) - COALESCE(SUM(p.paid),0) AS outstanding "
        "FROM bill b JOIN parking_session ps ON ps.session_id = b.session_id "
        "JOIN v_slot_location l ON l.slot_id = ps.slot_id "
        "LEFT JOIN (SELECT bill_id, SUM(amount_paid) AS paid FROM payment GROUP BY bill_id) p ON p.bill_id = b.bill_id "
        "GROUP BY l.facility_id, l.facility"),
    "Revenue by payment method": (
        "SELECT method, COUNT(*) AS payments, SUM(amount_paid) AS collected FROM payment "
        "GROUP BY method ORDER BY collected DESC"),
    "Unpaid bills": (
        "SELECT bill_id, reg_number, facility, amount, paid, balance, bill_status "
        "FROM v_bill_details WHERE balance > 0 ORDER BY balance DESC"),
}

# report -> (label column(s), value column) for the bar chart
CHARTS = {
    "Peak hours": (["hour_of_day"], "entries"),
    "Occupancy by floor": (["facility", "floor_no"], "occupancy_pct"),
    "Revenue by facility": (["facility"], "collected"),
    "Revenue by payment method": (["method"], "collected"),
}


def export_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(c, "") for c in columns])
