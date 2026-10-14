-- =====================================================================
-- File 6: Prototype demonstration of the full parking flow using the
-- stored procedures (these are the calls the Review 3 front end will make).
-- Run:  mysql -u root -p -t smart_parking < 06_prototype_demo.sql
-- =====================================================================
USE smart_parking;

SELECT 'STEP 1: free car slots in facility 1 before the visit' AS step;
SELECT COUNT(*) AS free_car_slots_lakeview FROM v_free_slots WHERE facility = 'Lakeview Mall Parking' AND type_name = 'Car';

SELECT 'STEP 2: gate entry, vehicle 13 (a car), system allocates a slot' AS step;
CALL sp_vehicle_entry(13, 1, NULL, NULL);
SET @sid = (SELECT MAX(session_id) FROM parking_session);

SELECT 'STEP 3: the slot is now OCCUPIED and free car slots dropped by one' AS step;
SELECT l.facility, l.floor_no, l.zone_name, l.slot_no, l.status
FROM parking_session ps JOIN v_slot_location l ON l.slot_id = ps.slot_id WHERE ps.session_id = @sid;
SELECT COUNT(*) AS free_car_slots_lakeview FROM v_free_slots WHERE facility = 'Lakeview Mall Parking' AND type_name = 'Car';

SELECT 'STEP 4: gate exit after a simulated 3 h 20 min stay; the bill is generated' AS step;
CALL sp_vehicle_exit(@sid, NOW() + INTERVAL 200 MINUTE);

SELECT 'STEP 5: bill details (200 min rounds up to 4 hours x tariff rate)' AS step;
SELECT * FROM v_bill_details WHERE bill_id = (SELECT bill_id FROM bill WHERE session_id = @sid);

SELECT 'STEP 6: part payment, then the balance' AS step;
SET @bid = (SELECT bill_id FROM bill WHERE session_id = @sid);
CALL sp_make_payment(@bid, 50.00, 'UPI');
CALL sp_make_payment(@bid, (SELECT amount - 50 FROM bill WHERE bill_id = @bid), 'CASH');

SELECT 'STEP 7: the slot is free again; occupancy report' AS step;
SELECT * FROM v_occupancy ORDER BY facility, floor_no;

SELECT 'STEP 8: the bill amount cannot be typed in by hand (the trigger recomputes it)' AS step;
CALL sp_vehicle_entry(6, 1, NULL, NULL);   -- a bike this time
SET @sid2 = (SELECT MAX(session_id) FROM parking_session);
UPDATE parking_session SET exit_time = NOW() + INTERVAL 125 MINUTE WHERE session_id = @sid2;
INSERT INTO bill (session_id, tariff_id, amount) VALUES (@sid2, fn_pick_tariff(@sid2), 1.00);
SELECT bill_id, amount AS stored_amount, 'tried to store 1.00; 125 min = 3 h x Rs 10' AS note
FROM bill WHERE session_id = @sid2;
