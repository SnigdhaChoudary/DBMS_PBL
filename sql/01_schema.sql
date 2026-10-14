-- =====================================================================
-- Smart Parking Lot Allocation and Billing System  |  MySQL 8.0+
-- File 1: DDL (tables, constraints, indexes, triggers, functions, procedures)
-- Run first:  mysql -u root -p < 01_schema.sql
-- =====================================================================
DROP DATABASE IF EXISTS smart_parking;
CREATE DATABASE smart_parking CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE smart_parking;

-- ---------------------------------------------------------------------
-- 1. MASTER DATA
-- ---------------------------------------------------------------------
CREATE TABLE facility (
  facility_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  name         VARCHAR(80)   NOT NULL,
  address      VARCHAR(150)  NOT NULL,
  CONSTRAINT pk_facility PRIMARY KEY (facility_id),
  CONSTRAINT uq_facility_name UNIQUE (name)
) ENGINE=InnoDB;

CREATE TABLE floor (
  floor_id     INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  facility_id  INT UNSIGNED  NOT NULL,
  floor_no     SMALLINT      NOT NULL,                -- -1 = basement, 0 = ground
  CONSTRAINT pk_floor PRIMARY KEY (floor_id),
  CONSTRAINT uq_floor UNIQUE (facility_id, floor_no),
  CONSTRAINT chk_floor_no CHECK (floor_no BETWEEN -5 AND 50),
  CONSTRAINT fk_floor_facility FOREIGN KEY (facility_id) REFERENCES facility (facility_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE zone (
  zone_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  floor_id     INT UNSIGNED  NOT NULL,
  zone_name    VARCHAR(30)   NOT NULL,
  CONSTRAINT pk_zone PRIMARY KEY (zone_id),
  CONSTRAINT uq_zone UNIQUE (floor_id, zone_name),
  CONSTRAINT fk_zone_floor FOREIGN KEY (floor_id) REFERENCES floor (floor_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE vehicle_type (
  type_id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  type_name    VARCHAR(20)      NOT NULL,
  CONSTRAINT pk_vehicle_type PRIMARY KEY (type_id),
  CONSTRAINT uq_vehicle_type_name UNIQUE (type_name)
) ENGINE=InnoDB;

CREATE TABLE slot (
  slot_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  zone_id      INT UNSIGNED  NOT NULL,
  type_id      TINYINT UNSIGNED NOT NULL,
  slot_no      VARCHAR(10)   NOT NULL,
  status       ENUM('AVAILABLE','OCCUPIED','MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE',
  CONSTRAINT pk_slot PRIMARY KEY (slot_id),
  CONSTRAINT uq_slot_no UNIQUE (zone_id, slot_no),
  CONSTRAINT fk_slot_zone FOREIGN KEY (zone_id) REFERENCES zone (zone_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_slot_type FOREIGN KEY (type_id) REFERENCES vehicle_type (type_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX idx_slot_status_type (status, type_id)           -- fast free-slot search
) ENGINE=InnoDB;

CREATE TABLE tariff (
  tariff_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  facility_id    INT UNSIGNED  NOT NULL,
  type_id        TINYINT UNSIGNED NOT NULL,
  effective_from DATE          NOT NULL,
  rate_per_hour  DECIMAL(8,2)  NOT NULL,
  daily_cap      DECIMAL(8,2)  NULL,                      -- NULL = no daily cap
  CONSTRAINT pk_tariff PRIMARY KEY (tariff_id),
  CONSTRAINT uq_tariff UNIQUE (facility_id, type_id, effective_from),
  CONSTRAINT chk_tariff_rate CHECK (rate_per_hour > 0),
  CONSTRAINT chk_tariff_cap  CHECK (daily_cap IS NULL OR daily_cap >= rate_per_hour),
  CONSTRAINT fk_tariff_facility FOREIGN KEY (facility_id) REFERENCES facility (facility_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_tariff_type FOREIGN KEY (type_id) REFERENCES vehicle_type (type_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. CUSTOMERS AND VEHICLES
-- ---------------------------------------------------------------------
CREATE TABLE customer (
  customer_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  name         VARCHAR(80)   NOT NULL,
  phone        CHAR(10)      NOT NULL,
  email        VARCHAR(100)  NOT NULL,
  CONSTRAINT pk_customer PRIMARY KEY (customer_id),
  CONSTRAINT uq_customer_phone UNIQUE (phone),
  CONSTRAINT uq_customer_email UNIQUE (email),
  CONSTRAINT chk_customer_phone CHECK (phone REGEXP '^[6-9][0-9]{9}$'),
  CONSTRAINT chk_customer_email CHECK (email LIKE '_%@_%.__%')
) ENGINE=InnoDB;

CREATE TABLE vehicle (
  vehicle_id   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  customer_id  INT UNSIGNED  NOT NULL,
  type_id      TINYINT UNSIGNED NOT NULL,
  reg_number   VARCHAR(12)   NOT NULL,
  CONSTRAINT pk_vehicle PRIMARY KEY (vehicle_id),
  CONSTRAINT uq_vehicle_reg UNIQUE (reg_number),
  CONSTRAINT chk_vehicle_reg CHECK (reg_number REGEXP '^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$'),
  CONSTRAINT fk_vehicle_customer FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_vehicle_type FOREIGN KEY (type_id) REFERENCES vehicle_type (type_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. RESERVATIONS AND PASSES
--    (customer is reached through vehicle: reservation has no customer_id,
--     removing the transitive dependency reservation -> vehicle -> customer)
-- ---------------------------------------------------------------------
CREATE TABLE reservation (
  reservation_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id     INT UNSIGNED NOT NULL,
  slot_id        INT UNSIGNED NOT NULL,
  start_time     DATETIME     NOT NULL,
  expiry_time    DATETIME     NOT NULL,
  status         ENUM('ACTIVE','USED','EXPIRED','CANCELLED') NOT NULL DEFAULT 'ACTIVE',
  CONSTRAINT pk_reservation PRIMARY KEY (reservation_id),
  CONSTRAINT chk_reservation_window CHECK (expiry_time > start_time),
  CONSTRAINT fk_reservation_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle (vehicle_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_reservation_slot FOREIGN KEY (slot_id) REFERENCES slot (slot_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX idx_reservation_slot_time (slot_id, start_time, expiry_time),
  INDEX idx_reservation_status (status)
) ENGINE=InnoDB;

CREATE TABLE pass (
  pass_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  customer_id  INT UNSIGNED  NOT NULL,
  pass_type    ENUM('MONTHLY','QUARTERLY','ANNUAL') NOT NULL,
  valid_from   DATE          NOT NULL,
  valid_to     DATE          NOT NULL,
  fee          DECIMAL(10,2) NOT NULL,
  CONSTRAINT pk_pass PRIMARY KEY (pass_id),
  CONSTRAINT chk_pass_dates CHECK (valid_to >= valid_from),
  CONSTRAINT chk_pass_fee   CHECK (fee >= 0),
  CONSTRAINT fk_pass_customer FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX idx_pass_validity (valid_from, valid_to)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. PARKING SESSION (entry / exit)
--    active_slot_id / active_vehicle_id are generated columns that are
--    NULL once the vehicle exits. UNIQUE on them gives:
--      * ONE ACTIVE VEHICLE PER SLOT
--      * a vehicle cannot be parked in two slots at once
-- ---------------------------------------------------------------------
CREATE TABLE parking_session (
  session_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id      INT UNSIGNED NOT NULL,
  slot_id         INT UNSIGNED NOT NULL,
  reservation_id  INT UNSIGNED NULL,
  pass_id         INT UNSIGNED NULL,
  entry_time      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  exit_time       DATETIME     NULL,
  active_slot_id    INT UNSIGNED GENERATED ALWAYS AS (IF(exit_time IS NULL, slot_id, NULL)) STORED,
  active_vehicle_id INT UNSIGNED GENERATED ALWAYS AS (IF(exit_time IS NULL, vehicle_id, NULL)) STORED,
  CONSTRAINT pk_session PRIMARY KEY (session_id),
  CONSTRAINT uq_one_active_vehicle_per_slot UNIQUE (active_slot_id),
  CONSTRAINT uq_vehicle_active_once         UNIQUE (active_vehicle_id),
  CONSTRAINT uq_session_reservation         UNIQUE (reservation_id),
  CONSTRAINT chk_exit_after_entry CHECK (exit_time IS NULL OR exit_time > entry_time),
  CONSTRAINT fk_session_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle (vehicle_id),
  CONSTRAINT fk_session_slot FOREIGN KEY (slot_id) REFERENCES slot (slot_id),
  CONSTRAINT fk_session_reservation FOREIGN KEY (reservation_id) REFERENCES reservation (reservation_id),
  CONSTRAINT fk_session_pass FOREIGN KEY (pass_id) REFERENCES pass (pass_id),
  INDEX idx_session_entry (entry_time),
  INDEX idx_session_vehicle_exit (vehicle_id, exit_time),
  INDEX idx_session_slot_time (slot_id, entry_time, exit_time),
  INDEX idx_session_pass (pass_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. BILLING
-- ---------------------------------------------------------------------
CREATE TABLE bill (
  bill_id       INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  session_id    INT UNSIGNED  NOT NULL,
  tariff_id     INT UNSIGNED  NOT NULL,
  amount        DECIMAL(10,2) NOT NULL DEFAULT 0.00,     -- always computed by trigger
  bill_status   ENUM('UNPAID','PARTIAL','PAID') NOT NULL DEFAULT 'UNPAID',
  generated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_bill PRIMARY KEY (bill_id),
  CONSTRAINT uq_bill_session UNIQUE (session_id),          -- one bill per session
  CONSTRAINT chk_bill_amount CHECK (amount >= 0),
  CONSTRAINT fk_bill_session FOREIGN KEY (session_id) REFERENCES parking_session (session_id),
  CONSTRAINT fk_bill_tariff FOREIGN KEY (tariff_id) REFERENCES tariff (tariff_id),
  INDEX idx_bill_status (bill_status)
) ENGINE=InnoDB;

CREATE TABLE payment (
  payment_id   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  bill_id      INT UNSIGNED  NOT NULL,
  amount_paid  DECIMAL(10,2) NOT NULL,
  method       ENUM('CASH','CARD','UPI','WALLET') NOT NULL DEFAULT 'CASH',
  paid_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_payment PRIMARY KEY (payment_id),
  CONSTRAINT chk_payment_amount CHECK (amount_paid > 0),
  CONSTRAINT fk_payment_bill FOREIGN KEY (bill_id) REFERENCES bill (bill_id),
  INDEX idx_payment_paid_at (paid_at)
) ENGINE=InnoDB;

-- =====================================================================
-- FUNCTIONS
-- =====================================================================
DELIMITER $$

-- Tariff that applies to a session: facility of its slot + vehicle type,
-- latest effective_from on or before the entry date.
CREATE FUNCTION fn_pick_tariff(p_session_id INT UNSIGNED) RETURNS INT UNSIGNED
READS SQL DATA
BEGIN
  DECLARE v_tariff INT UNSIGNED;
  SELECT t.tariff_id INTO v_tariff
  FROM parking_session ps
  JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
  JOIN slot s    ON s.slot_id    = ps.slot_id
  JOIN zone z    ON z.zone_id    = s.zone_id
  JOIN floor f   ON f.floor_id   = z.floor_id
  JOIN tariff t  ON t.facility_id = f.facility_id
                AND t.type_id     = v.type_id
                AND t.effective_from <= DATE(ps.entry_time)
  WHERE ps.session_id = p_session_id
  ORDER BY t.effective_from DESC
  LIMIT 1;
  RETURN v_tariff;
END$$

-- Tariff-based charge: hours are rounded UP (minimum 1 hour); each full
-- 24 hours costs the daily cap; remaining hours cost rate*hours up to the cap.
-- Pass holders pay nothing per stay (the pass fee was paid up front).
CREATE FUNCTION fn_bill_amount(p_session_id INT UNSIGNED, p_tariff_id INT UNSIGNED)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
  DECLARE v_min INT; DECLARE v_pass INT UNSIGNED;
  DECLARE v_rate DECIMAL(8,2); DECLARE v_cap DECIMAL(8,2);
  DECLARE v_hours INT; DECLARE v_days INT; DECLARE v_rem INT;
  SELECT TIMESTAMPDIFF(MINUTE, entry_time, exit_time), pass_id INTO v_min, v_pass
    FROM parking_session WHERE session_id = p_session_id;
  SELECT rate_per_hour, daily_cap INTO v_rate, v_cap FROM tariff WHERE tariff_id = p_tariff_id;
  IF v_pass IS NOT NULL THEN RETURN 0.00; END IF;
  SET v_hours = GREATEST(1, CEILING(v_min / 60));
  IF v_cap IS NULL THEN RETURN v_hours * v_rate; END IF;
  SET v_days = FLOOR(v_hours / 24);
  SET v_rem  = v_hours - v_days * 24;
  RETURN v_days * v_cap + LEAST(v_rem * v_rate, v_cap);
END$$

-- =====================================================================
-- TRIGGERS  (business rules that CHECK / UNIQUE alone cannot express)
-- =====================================================================

-- Reservation rules: type match, slot usable, no overlapping reservation
CREATE TRIGGER trg_reservation_bi BEFORE INSERT ON reservation
FOR EACH ROW
BEGIN
  DECLARE v_vtype TINYINT UNSIGNED; DECLARE v_stype TINYINT UNSIGNED; DECLARE v_status VARCHAR(20);
  SELECT type_id INTO v_vtype FROM vehicle WHERE vehicle_id = NEW.vehicle_id;
  SELECT type_id, status INTO v_stype, v_status FROM slot WHERE slot_id = NEW.slot_id;
  IF v_vtype <> v_stype THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot type does not match vehicle type';
  END IF;
  IF v_status = 'MAINTENANCE' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot is under maintenance';
  END IF;
  IF EXISTS (SELECT 1 FROM reservation r
             WHERE r.slot_id = NEW.slot_id AND r.status = 'ACTIVE'
               AND NEW.start_time < r.expiry_time AND NEW.expiry_time > r.start_time) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot already reserved for an overlapping period';
  END IF;
END$$

-- Entry rules
CREATE TRIGGER trg_session_bi BEFORE INSERT ON parking_session
FOR EACH ROW
BEGIN
  DECLARE v_vtype TINYINT UNSIGNED; DECLARE v_cust INT UNSIGNED;
  DECLARE v_stype TINYINT UNSIGNED; DECLARE v_status VARCHAR(20);
  DECLARE v_end DATETIME;
  SET v_end = COALESCE(NEW.exit_time, '9999-12-31 00:00:00');
  SELECT type_id, customer_id INTO v_vtype, v_cust FROM vehicle WHERE vehicle_id = NEW.vehicle_id;
  SELECT type_id, status INTO v_stype, v_status FROM slot WHERE slot_id = NEW.slot_id;

  -- RULE: slot / vehicle type match
  IF v_vtype <> v_stype THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot type does not match vehicle type';
  END IF;
  IF v_status = 'MAINTENANCE' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot is under maintenance';
  END IF;

  -- RULE: one active vehicle per slot (also covers overlapping history)
  IF EXISTS (SELECT 1 FROM parking_session p WHERE p.slot_id = NEW.slot_id
             AND p.entry_time < v_end AND COALESCE(p.exit_time, '9999-12-31') > NEW.entry_time) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot already holds a vehicle in that period';
  END IF;
  IF EXISTS (SELECT 1 FROM parking_session p WHERE p.vehicle_id = NEW.vehicle_id
             AND p.entry_time < v_end AND COALESCE(p.exit_time, '9999-12-31') > NEW.entry_time) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: vehicle is already parked in that period';
  END IF;

  -- RULE: reservation expiry (must be ACTIVE, same vehicle and slot, entry inside the window)
  IF NEW.reservation_id IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM reservation r
                   WHERE r.reservation_id = NEW.reservation_id AND r.status = 'ACTIVE'
                     AND r.vehicle_id = NEW.vehicle_id AND r.slot_id = NEW.slot_id
                     AND NEW.entry_time BETWEEN r.start_time AND r.expiry_time) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: reservation expired, not active, or does not match vehicle/slot';
    END IF;
  ELSE
    IF EXISTS (SELECT 1 FROM reservation r
               WHERE r.slot_id = NEW.slot_id AND r.status = 'ACTIVE'
                 AND NEW.entry_time BETWEEN r.start_time AND r.expiry_time) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: slot is reserved by another customer at this time';
    END IF;
  END IF;

  -- RULE: pass must belong to the vehicle owner and be valid on entry date
  IF NEW.pass_id IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pass ps WHERE ps.pass_id = NEW.pass_id AND ps.customer_id = v_cust
                   AND DATE(NEW.entry_time) BETWEEN ps.valid_from AND ps.valid_to) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: pass is invalid, expired, or belongs to another customer';
    END IF;
  END IF;
END$$

-- Exit rules: a closed session's vehicle / slot / entry cannot be rewritten
CREATE TRIGGER trg_session_bu BEFORE UPDATE ON parking_session
FOR EACH ROW
BEGIN
  IF NEW.vehicle_id <> OLD.vehicle_id OR NEW.slot_id <> OLD.slot_id OR NEW.entry_time <> OLD.entry_time THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: vehicle, slot and entry time of a session cannot be changed';
  END IF;
  IF OLD.exit_time IS NOT NULL AND NEW.exit_time <> OLD.exit_time THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: exit time already recorded';
  END IF;
  IF NEW.exit_time IS NOT NULL AND NEW.exit_time <= NEW.entry_time THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: exit must be after entry';
  END IF;
END$$

CREATE TRIGGER trg_session_ai AFTER INSERT ON parking_session
FOR EACH ROW
BEGIN
  IF NEW.exit_time IS NULL THEN
    UPDATE slot SET status = 'OCCUPIED' WHERE slot_id = NEW.slot_id;
  END IF;
  IF NEW.reservation_id IS NOT NULL THEN
    UPDATE reservation SET status = 'USED' WHERE reservation_id = NEW.reservation_id;
  END IF;
END$$

CREATE TRIGGER trg_session_au AFTER UPDATE ON parking_session
FOR EACH ROW
BEGIN
  IF OLD.exit_time IS NULL AND NEW.exit_time IS NOT NULL THEN
    UPDATE slot SET status = 'AVAILABLE' WHERE slot_id = NEW.slot_id AND status = 'OCCUPIED';
  END IF;
END$$

-- Billing rules: only closed sessions are billed; tariff must fit facility + vehicle type;
-- amount is always computed from the tariff (cannot be typed in by hand)
CREATE TRIGGER trg_bill_bi BEFORE INSERT ON bill
FOR EACH ROW
BEGIN
  DECLARE v_exit DATETIME;
  SELECT exit_time INTO v_exit FROM parking_session WHERE session_id = NEW.session_id;
  IF v_exit IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: cannot bill a session with no exit recorded';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM parking_session ps
                 JOIN vehicle v ON v.vehicle_id = ps.vehicle_id
                 JOIN slot s ON s.slot_id = ps.slot_id
                 JOIN zone z ON z.zone_id = s.zone_id
                 JOIN floor f ON f.floor_id = z.floor_id
                 JOIN tariff t ON t.tariff_id = NEW.tariff_id
                              AND t.facility_id = f.facility_id AND t.type_id = v.type_id
                 WHERE ps.session_id = NEW.session_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: tariff does not match the facility and vehicle type';
  END IF;
  SET NEW.amount = fn_bill_amount(NEW.session_id, NEW.tariff_id);
  IF NEW.amount = 0 THEN SET NEW.bill_status = 'PAID'; END IF;
END$$

-- Payment rules: no overpayment; keep bill_status in step
CREATE TRIGGER trg_payment_bi BEFORE INSERT ON payment
FOR EACH ROW
BEGIN
  DECLARE v_amount DECIMAL(10,2); DECLARE v_paid DECIMAL(10,2);
  SELECT amount INTO v_amount FROM bill WHERE bill_id = NEW.bill_id;
  SELECT COALESCE(SUM(amount_paid), 0) INTO v_paid FROM payment WHERE bill_id = NEW.bill_id;
  IF v_paid + NEW.amount_paid > v_amount THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'RULE: payment exceeds the outstanding bill amount';
  END IF;
END$$

CREATE TRIGGER trg_payment_ai AFTER INSERT ON payment
FOR EACH ROW
BEGIN
  DECLARE v_amount DECIMAL(10,2); DECLARE v_paid DECIMAL(10,2);
  SELECT amount INTO v_amount FROM bill WHERE bill_id = NEW.bill_id;
  SELECT SUM(amount_paid) INTO v_paid FROM payment WHERE bill_id = NEW.bill_id;
  UPDATE bill SET bill_status = IF(v_paid >= v_amount, 'PAID', 'PARTIAL') WHERE bill_id = NEW.bill_id;
END$$

-- =====================================================================
-- STORED PROCEDURES  (the operations the front end will call)
-- =====================================================================

-- Mark unused reservations as EXPIRED
CREATE PROCEDURE sp_expire_reservations()
BEGIN
  UPDATE reservation SET status = 'EXPIRED' WHERE status = 'ACTIVE' AND expiry_time < NOW();
  SELECT ROW_COUNT() AS reservations_expired;
END$$

-- Slot allocation: first free slot of the right type in the facility
-- (lowest floor first), skipping slots reserved for the next 2 hours.
CREATE PROCEDURE sp_allocate_slot(IN p_vehicle_id INT UNSIGNED, IN p_facility_id INT UNSIGNED,
                                  OUT p_slot_id INT UNSIGNED)
BEGIN
  SET p_slot_id = NULL;
  SELECT s.slot_id INTO p_slot_id
  FROM slot s
  JOIN zone z  ON z.zone_id = s.zone_id
  JOIN floor f ON f.floor_id = z.floor_id
  JOIN vehicle v ON v.type_id = s.type_id AND v.vehicle_id = p_vehicle_id
  WHERE f.facility_id = p_facility_id
    AND s.status = 'AVAILABLE'
    AND NOT EXISTS (SELECT 1 FROM reservation r
                    WHERE r.slot_id = s.slot_id AND r.status = 'ACTIVE'
                      AND r.start_time < NOW() + INTERVAL 2 HOUR AND r.expiry_time > NOW())
    AND NOT EXISTS (SELECT 1 FROM parking_session p      -- skip slots whose last stay has not ended yet
                    WHERE p.slot_id = s.slot_id AND COALESCE(p.exit_time, '9999-12-31') > NOW())
  ORDER BY f.floor_no, s.slot_id
  LIMIT 1;
END$$

-- Gate entry (with optional reservation / pass)
CREATE PROCEDURE sp_vehicle_entry(IN p_vehicle_id INT UNSIGNED, IN p_facility_id INT UNSIGNED,
                                  IN p_reservation_id INT UNSIGNED, IN p_pass_id INT UNSIGNED)
BEGIN
  DECLARE v_slot INT UNSIGNED;
  IF p_reservation_id IS NOT NULL THEN
    SELECT slot_id INTO v_slot FROM reservation WHERE reservation_id = p_reservation_id;
  ELSE
    CALL sp_allocate_slot(p_vehicle_id, p_facility_id, v_slot);
  END IF;
  IF v_slot IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No free slot of the required type in this facility';
  END IF;
  INSERT INTO parking_session (vehicle_id, slot_id, reservation_id, pass_id, entry_time)
  VALUES (p_vehicle_id, v_slot, p_reservation_id, p_pass_id, NOW());
  SELECT LAST_INSERT_ID() AS session_id, v_slot AS allotted_slot_id;
END$$

-- Gate exit: close the session and generate the bill.
-- Runs as ONE transaction: if the bill cannot be created (for example no tariff exists),
-- the exit time is rolled back too, so a vehicle is never left "exited but unbilled".
CREATE PROCEDURE sp_vehicle_exit(IN p_session_id INT UNSIGNED, IN p_exit_time DATETIME)
BEGIN
  DECLARE v_tariff INT UNSIGNED;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  UPDATE parking_session SET exit_time = COALESCE(p_exit_time, NOW())
   WHERE session_id = p_session_id AND exit_time IS NULL;
  IF ROW_COUNT() = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Session not found or already closed';
  END IF;
  SET v_tariff = fn_pick_tariff(p_session_id);
  IF v_tariff IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No tariff is defined for this facility and vehicle type';
  END IF;
  INSERT INTO bill (session_id, tariff_id) VALUES (p_session_id, v_tariff);
  COMMIT;
  SELECT b.bill_id, b.session_id, b.amount, b.bill_status,
         TIMESTAMPDIFF(MINUTE, ps.entry_time, ps.exit_time) AS minutes_parked
  FROM bill b JOIN parking_session ps ON ps.session_id = b.session_id
  WHERE b.session_id = p_session_id;
END$$

CREATE PROCEDURE sp_make_payment(IN p_bill_id INT UNSIGNED, IN p_amount DECIMAL(10,2), IN p_method VARCHAR(10))
BEGIN
  INSERT INTO payment (bill_id, amount_paid, method) VALUES (p_bill_id, p_amount, p_method);
  SELECT bill_id, amount, bill_status FROM bill WHERE bill_id = p_bill_id;
END$$

DELIMITER ;
