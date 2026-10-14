-- =====================================================================
-- File 5: Proof that the business rules and constraints work.
-- Every statement below is SUPPOSED TO FAIL with a clear message.
-- Run:  mysql -u root -p -f smart_parking < 05_constraint_tests.sql
-- (-f keeps going after each error). Assumes 01, 02, 03 were loaded today.
-- =====================================================================
USE smart_parking;

-- TEST 1: one active vehicle per slot (slot 9 already holds a bike)
INSERT INTO parking_session (vehicle_id, slot_id) VALUES (6, 9);

-- TEST 2: the same vehicle cannot be parked twice (vehicle 2 is already inside)
INSERT INTO parking_session (vehicle_id, slot_id) VALUES (2, 12);

-- TEST 3: slot / vehicle type match (a car into a bike slot)
INSERT INTO parking_session (vehicle_id, slot_id) VALUES (13, 12);

-- TEST 4: exit after entry
INSERT INTO parking_session (vehicle_id, slot_id, entry_time, exit_time)
VALUES (6, 13, NOW(), NOW() - INTERVAL 1 HOUR);

-- TEST 5: reservation expiry (reservation 4 expired days ago)
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id) VALUES (11, 30, 4);

-- TEST 6: reservation not yet started (reservation 6 is for tomorrow)
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id) VALUES (5, 31, 6);

-- TEST 7: overlapping reservations on the same slot
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time)
VALUES (13, 31, CURDATE() + INTERVAL 1 DAY + INTERVAL 660 MINUTE, CURDATE() + INTERVAL 1 DAY + INTERVAL 840 MINUTE);  -- overlaps 10:00-12:00 tomorrow

-- TEST 8: walk-in into a slot that is reserved right now (slot 32)
INSERT INTO parking_session (vehicle_id, slot_id) VALUES (13, 32);

-- TEST 9: parking in a slot under maintenance (slot 8)
INSERT INTO parking_session (vehicle_id, slot_id) VALUES (13, 8);

-- TEST 10: using an expired pass (pass 3)
INSERT INTO parking_session (vehicle_id, slot_id, pass_id) VALUES (10, 3, 3);

-- TEST 11: using someone else's pass (pass 1 belongs to customer 1, vehicle 13 is not theirs)
INSERT INTO parking_session (vehicle_id, slot_id, pass_id) VALUES (13, 3, 1);

-- TEST 12: billing a vehicle that has not exited yet
INSERT INTO bill (session_id, tariff_id)
SELECT session_id, fn_pick_tariff(session_id) FROM parking_session WHERE exit_time IS NULL LIMIT 1;

-- TEST 13: overpaying a bill
INSERT INTO payment (bill_id, amount_paid, method) VALUES (1, 99999, 'CASH');

-- TEST 14: invalid phone number
INSERT INTO customer (name, phone, email) VALUES ('Test User', '12345', 'test@example.com');

-- TEST 15: invalid registration number format
INSERT INTO vehicle (customer_id, type_id, reg_number) VALUES (1, 2, 'BAD-123');

-- TEST 16: duplicate registration number
INSERT INTO vehicle (customer_id, type_id, reg_number) VALUES (2, 2, 'TS09EA1234');

-- TEST 17: negative tariff rate
INSERT INTO tariff (facility_id, type_id, effective_from, rate_per_hour) VALUES (1, 1, CURDATE(), -5);

-- TEST 18: foreign key (vehicle for a customer that does not exist)
INSERT INTO vehicle (customer_id, type_id, reg_number) VALUES (999, 2, 'TS01AA0001');

-- TEST 19: reservation window must be valid (expiry before start)
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time)
VALUES (13, 33, NOW() + INTERVAL 2 DAY, NOW() + INTERVAL 1 DAY);

-- TEST 20: a recorded exit time cannot be rewritten
UPDATE parking_session SET exit_time = exit_time + INTERVAL 1 HOUR WHERE session_id = 1;
