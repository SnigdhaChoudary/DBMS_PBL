-- =====================================================================
-- File 3: Views for the required reports
-- Run after 02_sample_data.sql:  mysql -u root -p smart_parking < 03_views.sql
-- =====================================================================
USE smart_parking;

-- Helper: slot -> zone -> floor -> facility in one place
CREATE OR REPLACE VIEW v_slot_location AS
SELECT s.slot_id, s.slot_no, s.status, vt.type_name,
       z.zone_id, z.zone_name, f.floor_id, f.floor_no, fa.facility_id, fa.name AS facility
FROM slot s
JOIN vehicle_type vt ON vt.type_id = s.type_id
JOIN zone z          ON z.zone_id = s.zone_id
JOIN floor f         ON f.floor_id = z.floor_id
JOIN facility fa     ON fa.facility_id = f.facility_id;

-- OCCUPANCY: per facility and floor
CREATE OR REPLACE VIEW v_occupancy AS
SELECT facility, floor_no,
       COUNT(*)                                   AS total_slots,
       SUM(status = 'OCCUPIED')                   AS occupied,
       SUM(status = 'AVAILABLE')                  AS available,
       SUM(status = 'MAINTENANCE')                AS maintenance,
       ROUND(100 * SUM(status = 'OCCUPIED') / NULLIF(SUM(status <> 'MAINTENANCE'), 0), 1) AS occupancy_pct
FROM v_slot_location
GROUP BY facility_id, facility, floor_id, floor_no;

-- FREE SLOTS: available and not covered by an active reservation right now
CREATE OR REPLACE VIEW v_free_slots AS
SELECT l.facility, l.floor_no, l.zone_name, l.slot_no, l.type_name, l.slot_id
FROM v_slot_location l
WHERE l.status = 'AVAILABLE'
  AND NOT EXISTS (SELECT 1 FROM reservation r
                  WHERE r.slot_id = l.slot_id AND r.status = 'ACTIVE'
                    AND NOW() BETWEEN r.start_time AND r.expiry_time);

-- DURATION: length of each stay (open stays measured up to now)
CREATE OR REPLACE VIEW v_session_duration AS
SELECT ps.session_id, v.reg_number, vt.type_name, l.facility, l.slot_no,
       ps.entry_time, ps.exit_time,
       IF(ps.exit_time IS NULL, 'OPEN', 'CLOSED') AS state,
       TIMESTAMPDIFF(MINUTE, ps.entry_time, COALESCE(ps.exit_time, NOW())) AS minutes_parked
FROM parking_session ps
JOIN vehicle v        ON v.vehicle_id = ps.vehicle_id
JOIN vehicle_type vt  ON vt.type_id = v.type_id
JOIN v_slot_location l ON l.slot_id = ps.slot_id;

-- PEAK HOURS: entries per hour of day
CREATE OR REPLACE VIEW v_peak_hours AS
SELECT HOUR(entry_time) AS hour_of_day,
       COUNT(*)         AS entries,
       RANK() OVER (ORDER BY COUNT(*) DESC) AS busy_rank
FROM parking_session
GROUP BY HOUR(entry_time);

-- PASS USAGE
CREATE OR REPLACE VIEW v_pass_usage AS
SELECT p.pass_id, c.name AS customer, p.pass_type, p.valid_from, p.valid_to,
       IF(CURDATE() BETWEEN p.valid_from AND p.valid_to, 'ACTIVE', 'EXPIRED') AS pass_state,
       COUNT(ps.session_id) AS visits,
       ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, ps.entry_time, COALESCE(ps.exit_time, NOW()))), 0) / 60, 1) AS hours_parked,
       p.fee
FROM pass p
JOIN customer c ON c.customer_id = p.customer_id
LEFT JOIN parking_session ps ON ps.pass_id = p.pass_id
GROUP BY p.pass_id, c.name, p.pass_type, p.valid_from, p.valid_to, p.fee;

-- VIOLATIONS (derived, so no extra table is needed)
CREATE OR REPLACE VIEW v_violations AS
SELECT 'OVERSTAY_PAST_RESERVATION' AS violation, ps.session_id, v.reg_number,
       CONCAT('Left/still inside ', TIMESTAMPDIFF(MINUTE, r.expiry_time, COALESCE(ps.exit_time, NOW())),
              ' min after reservation expiry') AS detail
FROM parking_session ps
JOIN reservation r ON r.reservation_id = ps.reservation_id
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
WHERE COALESCE(ps.exit_time, NOW()) > r.expiry_time
UNION ALL
SELECT 'PASS_EXPIRED_DURING_STAY', ps.session_id, v.reg_number,
       CONCAT('Pass expired on ', p.valid_to, ' but stay continued')
FROM parking_session ps
JOIN pass p ON p.pass_id = ps.pass_id
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
WHERE DATE(COALESCE(ps.exit_time, NOW())) > p.valid_to
UNION ALL
SELECT 'STAY_OVER_24H', ps.session_id, v.reg_number,
       CONCAT('Parked for ', TIMESTAMPDIFF(HOUR, ps.entry_time, COALESCE(ps.exit_time, NOW())), ' hours')
FROM parking_session ps
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
WHERE TIMESTAMPDIFF(HOUR, ps.entry_time, COALESCE(ps.exit_time, NOW())) >= 24
UNION ALL
SELECT 'BILL_UNPAID_OVER_24H', b.session_id, v.reg_number,
       CONCAT('Rs ', b.amount - COALESCE((SELECT SUM(amount_paid) FROM payment WHERE bill_id = b.bill_id), 0), ' outstanding')
FROM bill b
JOIN parking_session ps ON ps.session_id = b.session_id
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
WHERE b.bill_status <> 'PAID' AND b.generated_at < NOW() - INTERVAL 24 HOUR;

-- BILL DETAILS: how each charge was calculated
CREATE OR REPLACE VIEW v_bill_details AS
SELECT b.bill_id, v.reg_number, l.facility, vt.type_name,
       TIMESTAMPDIFF(MINUTE, ps.entry_time, ps.exit_time) AS minutes_parked,
       t.rate_per_hour, t.daily_cap, b.amount,
       COALESCE(SUM(p.amount_paid), 0) AS paid,
       b.amount - COALESCE(SUM(p.amount_paid), 0) AS balance, b.bill_status
FROM bill b
JOIN parking_session ps ON ps.session_id = b.session_id
JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
JOIN vehicle_type vt ON vt.type_id = v.type_id
JOIN v_slot_location l ON l.slot_id = ps.slot_id
JOIN tariff t ON t.tariff_id = b.tariff_id
LEFT JOIN payment p ON p.bill_id = b.bill_id
GROUP BY b.bill_id, v.reg_number, l.facility, vt.type_name, ps.entry_time, ps.exit_time,
         t.rate_per_hour, t.daily_cap, b.amount, b.bill_status;

-- REVENUE: money actually collected, per facility and day
CREATE OR REPLACE VIEW v_revenue_daily AS
SELECT l.facility, DATE(p.paid_at) AS pay_date,
       COUNT(*) AS payments, SUM(p.amount_paid) AS collected
FROM payment p
JOIN bill b ON b.bill_id = p.bill_id
JOIN parking_session ps ON ps.session_id = b.session_id
JOIN v_slot_location l ON l.slot_id = ps.slot_id
GROUP BY l.facility, DATE(p.paid_at);
