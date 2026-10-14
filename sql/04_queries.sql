-- =====================================================================
-- File 4: Report queries (joins, subqueries, aggregation, views, window function)
-- Run:  mysql -u root -p smart_parking < 04_queries.sql
-- =====================================================================
USE smart_parking;

SELECT '--- Q1 JOIN (5 tables): who is parked where, right now' AS '';
SELECT v.reg_number, c.name AS owner, vt.type_name, l.facility, l.floor_no, l.zone_name, l.slot_no,
       ps.entry_time, TIMESTAMPDIFF(MINUTE, ps.entry_time, NOW()) AS minutes_inside
FROM parking_session ps
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
JOIN customer c ON c.customer_id = v.customer_id
JOIN vehicle_type vt ON vt.type_id = v.type_id
JOIN v_slot_location l ON l.slot_id = ps.slot_id
WHERE ps.exit_time IS NULL
ORDER BY ps.entry_time;

SELECT '--- Q2 LEFT JOIN: customers who have never made a reservation' AS '';
SELECT c.customer_id, c.name
FROM customer c
LEFT JOIN vehicle v ON v.customer_id = c.customer_id
LEFT JOIN reservation r ON r.vehicle_id = v.vehicle_id
GROUP BY c.customer_id, c.name
HAVING COUNT(r.reservation_id) = 0
ORDER BY c.customer_id;

SELECT '--- Q3 SUBQUERY (IN): vehicles that used a reservation' AS '';
SELECT reg_number, vehicle_id FROM vehicle
WHERE vehicle_id IN (SELECT vehicle_id FROM parking_session WHERE reservation_id IS NOT NULL);

SELECT '--- Q4 NESTED / CORRELATED: bills above the average bill of the same vehicle type' AS '';
SELECT b.bill_id, v.reg_number, vt.type_name, b.amount
FROM bill b
JOIN parking_session ps ON ps.session_id = b.session_id
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
JOIN vehicle_type vt ON vt.type_id = v.type_id
WHERE b.amount > (SELECT AVG(b2.amount)
                  FROM bill b2
                  JOIN parking_session p2 ON p2.session_id = b2.session_id
                  JOIN vehicle v2 ON v2.vehicle_id = p2.vehicle_id
                  WHERE v2.type_id = v.type_id)
ORDER BY vt.type_name, b.amount DESC
LIMIT 8;

SELECT '--- Q5 NOT EXISTS: car slots never used so far' AS '';
SELECT l.facility, l.floor_no, l.zone_name, l.slot_no
FROM v_slot_location l
WHERE l.type_name = 'Car' AND l.status <> 'MAINTENANCE'
  AND NOT EXISTS (SELECT 1 FROM parking_session ps WHERE ps.slot_id = l.slot_id)
ORDER BY l.facility, l.floor_no, l.slot_no;

SELECT '--- Q6 AGGREGATE + GROUP BY + HAVING: busiest zones (3 or more visits)' AS '';
SELECT l.facility, l.zone_name, COUNT(*) AS visits,
       ROUND(AVG(TIMESTAMPDIFF(MINUTE, ps.entry_time, ps.exit_time)), 0) AS avg_minutes
FROM parking_session ps
JOIN v_slot_location l ON l.slot_id = ps.slot_id
WHERE ps.exit_time IS NOT NULL
GROUP BY l.facility_id, l.facility, l.zone_id, l.zone_name
HAVING COUNT(*) >= 3
ORDER BY visits DESC;

SELECT '--- Q7 OCCUPANCY (view)' AS '';
SELECT * FROM v_occupancy ORDER BY facility, floor_no;

SELECT '--- Q8 PEAK HOURS (view with window function), top 5' AS '';
SELECT * FROM v_peak_hours WHERE busy_rank <= 5 ORDER BY busy_rank, hour_of_day;

SELECT '--- Q9 DURATION (view): longest 5 stays' AS '';
SELECT session_id, reg_number, facility, state, minutes_parked,
       CONCAT(FLOOR(minutes_parked/60), 'h ', MOD(minutes_parked,60), 'm') AS readable
FROM v_session_duration ORDER BY minutes_parked DESC LIMIT 5;

SELECT '--- Q10 PASS USAGE (view)' AS '';
SELECT * FROM v_pass_usage ORDER BY pass_id;

SELECT '--- Q11 VIOLATIONS (view)' AS '';
SELECT * FROM v_violations ORDER BY violation, session_id;

SELECT '--- Q12 FREE SLOTS (view): count per facility and vehicle type' AS '';
SELECT facility, type_name, COUNT(*) AS free_slots
FROM v_free_slots GROUP BY facility, type_name ORDER BY facility, type_name;

SELECT '--- Q13 REVENUE per facility (collected vs billed)' AS '';
SELECT l.facility,
       SUM(b.amount) AS billed,
       COALESCE(SUM(pay.paid), 0) AS collected,
       SUM(b.amount) - COALESCE(SUM(pay.paid), 0) AS outstanding
FROM bill b
JOIN parking_session ps ON ps.session_id = b.session_id
JOIN v_slot_location l ON l.slot_id = ps.slot_id
LEFT JOIN (SELECT bill_id, SUM(amount_paid) AS paid FROM payment GROUP BY bill_id) pay ON pay.bill_id = b.bill_id
GROUP BY l.facility_id, l.facility;

SELECT '--- Q14 REVENUE by payment method, with share of total (window function)' AS '';
SELECT method, COUNT(*) AS payments, SUM(amount_paid) AS collected,
       ROUND(100 * SUM(amount_paid) / SUM(SUM(amount_paid)) OVER (), 1) AS share_pct
FROM payment GROUP BY method ORDER BY collected DESC;

SELECT '--- Q15 TARIFF CHECK: how a bill was calculated (view)' AS '';
SELECT * FROM v_bill_details ORDER BY amount DESC LIMIT 5;

SELECT '--- Q16 REVENUE per day (view), last 5 days' AS '';
SELECT * FROM v_revenue_daily ORDER BY pay_date DESC, facility LIMIT 10;

SELECT '--- Q17 TOTAL INCOME: parking fees plus pass sales' AS '';
SELECT 'Parking fees collected' AS income, SUM(amount_paid) AS rupees FROM payment
UNION ALL
SELECT 'Pass sales', SUM(fee) FROM pass;
