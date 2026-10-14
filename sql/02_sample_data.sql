-- =====================================================================
-- File 2: Sample data (realistic, relative to today so the demo always works)
-- Run after 01_schema.sql:  mysql -u root -p smart_parking < 02_sample_data.sql
-- Rows go through the triggers, so every business rule is applied to this data.
-- =====================================================================
USE smart_parking;

INSERT INTO vehicle_type (type_name) VALUES ('Bike'),('Car'),('Truck');

INSERT INTO facility (name, address) VALUES
 ('Lakeview Mall Parking','Plot 12, Lakeview Road'),
 ('Tech Park Parking','Block C, Knowledge Avenue');

INSERT INTO floor (facility_id, floor_no) VALUES (1,-1),(1,0),(1,1),(2,0),(2,1);

INSERT INTO zone (floor_id, zone_name) VALUES (1,'B1-CAR'),(1,'B1-BIKE'),(2,'G-CAR'),(2,'G-TRK'),(3,'L1-CAR'),(4,'G-CAR'),(4,'G-BIKE'),(4,'G-TRK'),(5,'L1-CAR');

INSERT INTO slot (zone_id, type_id, slot_no) VALUES
 (1,2,'C01'),
 (1,2,'C02'),
 (1,2,'C03'),
 (1,2,'C04'),
 (1,2,'C05'),
 (1,2,'C06'),
 (1,2,'C07'),
 (1,2,'C08'),
 (2,1,'B01'),
 (2,1,'B02'),
 (2,1,'B03'),
 (2,1,'B04'),
 (2,1,'B05'),
 (2,1,'B06'),
 (2,1,'B07'),
 (2,1,'B08'),
 (3,2,'C01'),
 (3,2,'C02'),
 (3,2,'C03'),
 (3,2,'C04'),
 (3,2,'C05'),
 (3,2,'C06'),
 (3,2,'C07'),
 (3,2,'C08'),
 (4,3,'T01'),
 (4,3,'T02'),
 (4,3,'T03'),
 (5,2,'C01'),
 (5,2,'C02'),
 (5,2,'C03'),
 (5,2,'C04'),
 (5,2,'C05'),
 (5,2,'C06'),
 (5,2,'C07'),
 (5,2,'C08'),
 (6,2,'C01'),
 (6,2,'C02'),
 (6,2,'C03'),
 (6,2,'C04'),
 (6,2,'C05'),
 (6,2,'C06'),
 (7,1,'B01'),
 (7,1,'B02'),
 (7,1,'B03'),
 (7,1,'B04'),
 (7,1,'B05'),
 (8,3,'T01'),
 (8,3,'T02'),
 (8,3,'T03'),
 (9,2,'C01'),
 (9,2,'C02'),
 (9,2,'C03'),
 (9,2,'C04'),
 (9,2,'C05'),
 (9,2,'C06');
UPDATE slot SET status='MAINTENANCE' WHERE slot_id IN (8,55);

INSERT INTO tariff (facility_id, type_id, effective_from, rate_per_hour, daily_cap) VALUES
 (1,1,CURDATE() - INTERVAL 90 DAY,10,60),(1,2,CURDATE() - INTERVAL 90 DAY,25,200),(1,3,CURDATE() - INTERVAL 90 DAY,60,500),
 (1,2,CURDATE() - INTERVAL 5 DAY,30,250),
 (2,1,CURDATE() - INTERVAL 90 DAY,8,50),(2,2,CURDATE() - INTERVAL 90 DAY,25,200),(2,3,CURDATE() - INTERVAL 90 DAY,50,400);

INSERT INTO customer (name, phone, email) VALUES
 ('Ravi Kumar','9848012345','ravi.kumar@example.com'),
 ('Anita Sharma','9701123456','anita.sharma@example.com'),
 ('Suresh Reddy','9912345678','suresh.reddy@example.com'),
 ('Priya Nair','9885011223','priya.nair@example.com'),
 ('Mohammed Irfan','9440099887','irfan.m@example.com'),
 ('Kavya Rao','9390123890','kavya.rao@example.com'),
 ('Arjun Verma','9246677889','arjun.verma@example.com'),
 ('Divya Menon','9000112233','divya.menon@example.com'),
 ('Vikram Singh','9666001122','vikram.singh@example.com'),
 ('Neha Gupta','9123456780','neha.gupta@example.com'),
 ('Sandeep Patil','9505050505','sandeep.patil@example.com'),
 ('Lakshmi Iyer','9703030303','lakshmi.iyer@example.com');

INSERT INTO vehicle (customer_id, type_id, reg_number) VALUES
 (1,2,'TS09EA1234'),
 (1,1,'TS09FB4421'),
 (2,2,'TS08GH7788'),
 (3,2,'AP28CD5521'),
 (3,2,'TS10JK9012'),
 (4,1,'TS07MN3345'),
 (5,3,'TS11TR2468'),
 (6,2,'KA05MP6789'),
 (6,1,'KA05NQ1357'),
 (7,2,'TS09PQ8642'),
 (8,2,'TS12RS1111'),
 (9,3,'AP29TT7070'),
 (10,2,'MH12AB3030'),
 (11,1,'TS09ZX5050'),
 (12,2,'TS13LM2020');

INSERT INTO pass (customer_id, pass_type, valid_from, valid_to, fee) VALUES
 (1,'MONTHLY',CURDATE() - INTERVAL 20 DAY, CURDATE() + INTERVAL 10 DAY, 1500),
 (4,'MONTHLY',CURDATE() - INTERVAL 15 DAY, CURDATE() + INTERVAL 15 DAY, 600),
 (7,'MONTHLY',CURDATE() - INTERVAL 40 DAY, CURDATE() - INTERVAL 3 DAY, 1500),
 (6,'ANNUAL',CURDATE() - INTERVAL 100 DAY, CURDATE() + INTERVAL 265 DAY, 12000);

-- Reservations (inserted ACTIVE; triggers mark them USED when the vehicle arrives)
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (3,28,(CURDATE() - INTERVAL 2 DAY + INTERVAL 540 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 660 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (4,36,(CURDATE() - INTERVAL 4 DAY + INTERVAL 840 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 900 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (8,29,(CURDATE() - INTERVAL 3 DAY + INTERVAL 1080 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1140 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (11,30,(CURDATE() - INTERVAL 4 DAY + INTERVAL 600 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 660 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (13,37,(CURDATE() - INTERVAL 1 DAY + INTERVAL 900 MINUTE),(CURDATE() - INTERVAL 1 DAY + INTERVAL 960 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (5,31,(CURDATE() + INTERVAL 1 DAY + INTERVAL 600 MINUTE),(CURDATE() + INTERVAL 1 DAY + INTERVAL 720 MINUTE));
INSERT INTO reservation (vehicle_id, slot_id, start_time, expiry_time) VALUES (15,32,NOW() - INTERVAL 30 MINUTE, NOW() + INTERVAL 90 MINUTE);

-- Parking sessions: walk-ins, reservation holders, pass holders, a few open (vehicles inside now)
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (13,17,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 435 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 615 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (5,54,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 600 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 655 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,53,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 615 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 735 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,22,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 765 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 1065 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,35,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 795 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 850 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,5,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 1065 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 1605 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (13,51,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 1085 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 1180 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,19,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 1120 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 1360 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,41,NULL,NULL,(CURDATE() - INTERVAL 8 DAY + INTERVAL 1185 MINUTE),(CURDATE() - INTERVAL 8 DAY + INTERVAL 1605 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,4,NULL,NULL,(CURDATE() - INTERVAL 7 DAY + INTERVAL 510 MINUTE),(CURDATE() - INTERVAL 7 DAY + INTERVAL 1050 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,50,NULL,NULL,(CURDATE() - INTERVAL 7 DAY + INTERVAL 675 MINUTE),(CURDATE() - INTERVAL 7 DAY + INTERVAL 975 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,41,NULL,NULL,(CURDATE() - INTERVAL 7 DAY + INTERVAL 945 MINUTE),(CURDATE() - INTERVAL 7 DAY + INTERVAL 1095 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,50,NULL,NULL,(CURDATE() - INTERVAL 7 DAY + INTERVAL 1070 MINUTE),(CURDATE() - INTERVAL 7 DAY + INTERVAL 1490 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,40,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 530 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 625 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,50,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 540 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 595 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (1,17,NULL,1,(CURDATE() - INTERVAL 6 DAY + INTERVAL 545 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1080 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (13,54,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 640 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1060 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (5,21,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 645 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 795 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,19,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 920 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1100 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,52,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 965 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1115 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,53,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 1010 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1550 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,1,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 1085 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1160 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (13,41,NULL,NULL,(CURDATE() - INTERVAL 6 DAY + INTERVAL 1180 MINUTE),(CURDATE() - INTERVAL 6 DAY + INTERVAL 1720 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (6,10,NULL,2,(CURDATE() - INTERVAL 5 DAY + INTERVAL 500 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1030 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (10,18,NULL,3,(CURDATE() - INTERVAL 5 DAY + INTERVAL 540 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1020 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (1,17,NULL,1,(CURDATE() - INTERVAL 5 DAY + INTERVAL 545 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1080 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,23,NULL,NULL,(CURDATE() - INTERVAL 5 DAY + INTERVAL 1010 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1105 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,1,NULL,NULL,(CURDATE() - INTERVAL 5 DAY + INTERVAL 1060 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1300 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (5,53,NULL,NULL,(CURDATE() - INTERVAL 5 DAY + INTERVAL 1145 MINUTE),(CURDATE() - INTERVAL 5 DAY + INTERVAL 1325 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (6,10,NULL,2,(CURDATE() - INTERVAL 4 DAY + INTERVAL 500 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1030 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (5,38,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 520 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 615 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (1,17,NULL,1,(CURDATE() - INTERVAL 4 DAY + INTERVAL 545 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1080 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,40,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 605 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 700 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,50,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 645 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 825 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,38,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 710 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1250 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,20,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 750 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 900 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,36,2,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 850 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 890 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,35,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 1065 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1605 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,17,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 1125 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1365 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,53,NULL,NULL,(CURDATE() - INTERVAL 4 DAY + INTERVAL 1160 MINUTE),(CURDATE() - INTERVAL 4 DAY + INTERVAL 1700 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (1,17,NULL,1,(CURDATE() - INTERVAL 3 DAY + INTERVAL 545 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1080 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,52,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 600 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 695 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,34,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 705 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 885 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,53,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 915 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 955 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,4,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 915 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1065 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,29,3,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 1085 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1290 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (15,23,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 1130 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1550 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (10,18,NULL,3,(CURDATE() - INTERVAL 3 DAY + INTERVAL 1200 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 540 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (13,52,NULL,NULL,(CURDATE() - INTERVAL 3 DAY + INTERVAL 1220 MINUTE),(CURDATE() - INTERVAL 3 DAY + INTERVAL 1460 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (6,10,NULL,2,(CURDATE() - INTERVAL 2 DAY + INTERVAL 500 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 1030 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,28,1,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 560 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 760 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (8,24,NULL,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 610 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 635 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (5,38,NULL,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 640 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 695 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (3,17,NULL,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 890 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 930 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (11,4,NULL,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 930 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 1005 MINUTE));
INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time) VALUES (4,24,NULL,NULL,(CURDATE() - INTERVAL 2 DAY + INTERVAL 965 MINUTE),(CURDATE() - INTERVAL 2 DAY + INTERVAL 1060 MINUTE));

-- Vehicles inside the facility right now (no exit_time)
INSERT INTO parking_session (vehicle_id, slot_id, entry_time) VALUES (2,9,NOW() - INTERVAL 95 MINUTE);
INSERT INTO parking_session (vehicle_id, slot_id, entry_time) VALUES (9,11,NOW() - INTERVAL 40 MINUTE);
INSERT INTO parking_session (vehicle_id, slot_id, entry_time) VALUES (12,25,NOW() - INTERVAL 30 HOUR);
INSERT INTO parking_session (vehicle_id, slot_id, entry_time) VALUES (14,42,NOW() - INTERVAL 3 HOUR);
INSERT INTO parking_session (vehicle_id, slot_id, entry_time) VALUES (7,47,NOW() - INTERVAL 5 HOUR);

-- Housekeeping: one reservation was never used and one was cancelled
UPDATE reservation SET status='CANCELLED' WHERE reservation_id=5;
CALL sp_expire_reservations();

-- Bills for every closed session (amount is computed by the trigger from the tariff)
INSERT INTO bill (session_id, tariff_id, generated_at)
SELECT session_id, fn_pick_tariff(session_id), exit_time FROM parking_session WHERE exit_time IS NOT NULL ORDER BY session_id;

-- Payments: most paid in full, some in two instalments, some partly paid, some unpaid
-- (a temporary copy of the bills is read, because the payment trigger updates bill)
CREATE TEMPORARY TABLE tmp_bill AS SELECT bill_id, amount, generated_at FROM bill;
INSERT INTO payment (bill_id, amount_paid, method, paid_at)
SELECT bill_id, amount, ELT(1+MOD(bill_id,4),'CASH','CARD','UPI','WALLET'), generated_at + INTERVAL 2 MINUTE
FROM tmp_bill WHERE amount > 0 AND MOD(bill_id,9) NOT IN (0,4,2);
INSERT INTO payment (bill_id, amount_paid, method, paid_at)
SELECT bill_id, ROUND(amount/2,2), 'UPI', generated_at + INTERVAL 3 MINUTE FROM tmp_bill WHERE amount > 1 AND MOD(bill_id,9) IN (4,2);
INSERT INTO payment (bill_id, amount_paid, method, paid_at)
SELECT bill_id, amount - ROUND(amount/2,2), 'CASH', generated_at + INTERVAL 20 MINUTE FROM tmp_bill WHERE amount > 1 AND MOD(bill_id,9) = 2;
DROP TEMPORARY TABLE tmp_bill;
