# Review 2: Normalization and Data Dictionary

Smart Parking Lot Allocation and Billing System (MySQL 8.0)

## 1. From the Review 1 ER diagram to 3NF

The Review 1 ER diagram is the starting point. Normalization was applied to check every table, and it produced **one change**:

- **`reservation.customer_id` was removed.** A reservation already names a vehicle, and every vehicle has exactly one owner, so `reservation_id -> vehicle_id -> customer_id` was a transitive dependency (a 3NF violation). The customer is now reached through `vehicle`.

### 1.1 Worked example: one flat parking record

A paper-style record that holds everything about a visit in one row:

`PARKING_RECORD(ticket_no, reg_number, owner_name, owner_phone, vehicle_type, facility_name, facility_address, floor_no, zone_name, slot_no, reservation_start, reservation_expiry, pass_type, pass_valid_to, entry_time, exit_time, rate_per_hour, bill_amount, payment_methods, amounts_paid)`

| Step | Problem found | Fix |
|---|---|---|
| **UNF -> 1NF** | `payment_methods` and `amounts_paid` hold several values in one cell (for example UPI and Cash) | One row per payment: the **payment** table |
| **1NF -> 2NF** | With key (ticket_no, payment_no), bill data depends on ticket_no alone (a partial dependency) | Split into **parking_session**, **bill** and **payment** |
| **2NF -> 3NF** | `reg_number -> owner_name, owner_phone, vehicle_type`; `slot_no -> zone_name -> floor_no -> facility_name, facility_address`; `(facility, vehicle_type) -> rate_per_hour`; `reservation -> start, expiry`; `pass -> type, valid_to` (all transitive dependencies) | Extract **customer, vehicle, vehicle_type, facility, floor, zone, slot, tariff, reservation, pass** |

## 2. Functional dependencies (final schema)

Every non-key attribute depends on the key, the whole key, and nothing but the key.

| Table | Primary key dependency | Candidate-key dependencies |
|---|---|---|
| facility | facility_id -> name, address | name -> facility_id, address |
| floor | floor_id -> facility_id, floor_no | (facility_id, floor_no) -> floor_id |
| zone | zone_id -> floor_id, zone_name | (floor_id, zone_name) -> zone_id |
| vehicle_type | type_id -> type_name | type_name -> type_id |
| slot | slot_id -> zone_id, type_id, slot_no, status | (zone_id, slot_no) -> slot_id |
| tariff | tariff_id -> facility_id, type_id, effective_from, rate_per_hour, daily_cap | (facility_id, type_id, effective_from) -> tariff_id, rate_per_hour, daily_cap |
| customer | customer_id -> name, phone, email | phone -> customer_id; email -> customer_id |
| vehicle | vehicle_id -> customer_id, type_id, reg_number | reg_number -> vehicle_id |
| reservation | reservation_id -> vehicle_id, slot_id, start_time, expiry_time, status | none other |
| pass | pass_id -> customer_id, pass_type, valid_from, valid_to, fee | none other |
| parking_session | session_id -> vehicle_id, slot_id, reservation_id, pass_id, entry_time, exit_time | reservation_id -> session_id (when not NULL) |
| bill | bill_id -> session_id, tariff_id, amount, bill_status, generated_at | session_id -> bill_id |
| payment | payment_id -> bill_id, amount_paid, method, paid_at | none other |

Note on `parking_session`: when `reservation_id` is present the trigger forces the same vehicle and slot as the reservation, but walk-ins have no reservation, so `vehicle_id` and `slot_id` are facts about the actual stay and not derived values.

## 3. Deliberate controlled redundancy

Three stored values are derived, and they are kept on purpose. Triggers keep them correct, so the user can never type a wrong value:

| Column | Why it is stored | How it stays correct |
|---|---|---|
| `bill.amount` | A historical snapshot: tariffs change later but old bills must not | `trg_bill_bi` computes it with `fn_bill_amount()` |
| `bill.bill_status` | Fast filtering of unpaid bills | `trg_payment_ai` recalculates after each payment |
| `slot.status` | Instant free-slot search (MAINTENANCE cannot be derived anyway) | `trg_session_ai` / `trg_session_au` |

## 4. Business rules and where they are enforced

| Rule | Enforced by |
|---|---|
| One active vehicle per slot | `trg_session_bi` (no overlapping stays) plus UNIQUE on generated column `active_slot_id` |
| A vehicle cannot be in two places | `trg_session_bi` plus UNIQUE on `active_vehicle_id` |
| Slot and vehicle type match | `trg_session_bi`, `trg_reservation_bi` |
| Exit after entry | `CHECK chk_exit_after_entry` and `trg_session_bu` |
| Reservation expiry | `trg_session_bi` (status ACTIVE, entry inside window); `sp_expire_reservations()` |
| No double booking of a slot | `trg_reservation_bi` |
| Tariff-based charges | `fn_pick_tariff()`, `fn_bill_amount()`, `trg_bill_bi` |
| No overpayment | `trg_payment_bi` |
| Valid pass use | `trg_session_bi` (owner matches, valid on entry date) |
| Input validation | CHECK on phone, email, registration format, rates, dates, amounts |

## 5. Indexes

| Index | Purpose |
|---|---|
| `slot(status, type_id)` | Free-slot search and allocation |
| `parking_session(entry_time)` | Peak-hour and daily reports |
| `parking_session(vehicle_id, exit_time)` | Is this vehicle inside right now? |
| `parking_session(slot_id, entry_time, exit_time)` | Overlap checks per slot |
| `reservation(slot_id, start_time, expiry_time)` | Double-booking and reserved-slot checks |
| `reservation(status)`, `bill(bill_status)`, `payment(paid_at)`, `pass(valid_from, valid_to)` | Status filters and date ranges |
| UNIQUE keys on `reg_number`, `phone`, `email`, `facility.name` | Fast lookup and duplicate protection |

## 6. Data dictionary

### facility

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| facility_id | int unsigned | NO | PK; auto-increment | Unique id of the parking facility |
| name | varchar(80) | NO | UNIQUE | Facility name |
| address | varchar(150) | NO |  | Postal address |

### floor

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| floor_id | int unsigned | NO | PK; auto-increment | Unique id of the floor |
| facility_id | int unsigned | NO | FK -> facility.facility_id | Facility the floor belongs to |
| floor_no | smallint | NO |  | Floor number (-1 basement, 0 ground) |

CHECK: `(floor_no between -(5) and 50)`

### zone

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| zone_id | int unsigned | NO | PK; auto-increment | Unique id of the zone |
| floor_id | int unsigned | NO | FK -> floor.floor_id | Floor containing the zone |
| zone_name | varchar(30) | NO |  | Zone label, e.g. G-CAR |

### vehicle_type

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| type_id | tinyint unsigned | NO | PK; auto-increment | Unique id of the vehicle type |
| type_name | varchar(20) | NO | UNIQUE | Bike, Car or Truck |

### slot

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| slot_id | int unsigned | NO | PK; auto-increment | Unique id of the slot |
| zone_id | int unsigned | NO | FK -> zone.zone_id | Zone containing the slot |
| type_id | tinyint unsigned | NO | FK -> vehicle_type.type_id | Vehicle type the slot is built for |
| slot_no | varchar(10) | NO |  | Slot label within the zone |
| status | enum('AVAILABLE','OCCUPIED','MAINTENANCE') | NO | default AVAILABLE | AVAILABLE, OCCUPIED or MAINTENANCE (kept in step by triggers) |

### tariff

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| tariff_id | int unsigned | NO | PK; auto-increment | Unique id of the tariff row |
| facility_id | int unsigned | NO | FK -> facility.facility_id | Facility the rate applies to |
| type_id | tinyint unsigned | NO | FK -> vehicle_type.type_id | Vehicle type the rate applies to |
| effective_from | date | NO |  | First date the rate applies |
| rate_per_hour | decimal(8,2) | NO |  | Charge per hour (rounded up) |
| daily_cap | decimal(8,2) | YES |  | Maximum charge per 24 hours, NULL means no cap |

CHECK: `(rate_per_hour > 0)`; `((daily_cap is null) or (daily_cap >= rate_per_hour))`

### customer

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| customer_id | int unsigned | NO | PK; auto-increment | Unique id of the customer |
| name | varchar(80) | NO |  | Full name |
| phone | char(10) | NO | UNIQUE | 10-digit mobile number (starts 6-9) |
| email | varchar(100) | NO | UNIQUE | Email address |

CHECK: `regexp_like(phone,'^[6-9][0-9]{9}$')`; `(email like '_%@_%.__%')`

### vehicle

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| vehicle_id | int unsigned | NO | PK; auto-increment | Unique id of the vehicle |
| customer_id | int unsigned | NO | FK -> customer.customer_id | Owner |
| type_id | tinyint unsigned | NO | FK -> vehicle_type.type_id | Vehicle type |
| reg_number | varchar(12) | NO | UNIQUE | Registration number, e.g. TS09EA1234 |

CHECK: `regexp_like(reg_number,'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$')`

### reservation

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| reservation_id | int unsigned | NO | PK; auto-increment | Unique id of the reservation |
| vehicle_id | int unsigned | NO | FK -> vehicle.vehicle_id | Vehicle the slot is reserved for |
| slot_id | int unsigned | NO | FK -> slot.slot_id | Reserved slot |
| start_time | datetime | NO |  | Start of the reserved window |
| expiry_time | datetime | NO |  | End of the window; after this the reservation cannot be used |
| status | enum('ACTIVE','USED','EXPIRED','CANCELLED') | NO | default ACTIVE | ACTIVE, USED, EXPIRED or CANCELLED |

CHECK: `(expiry_time > start_time)`

### pass

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| pass_id | int unsigned | NO | PK; auto-increment | Unique id of the pass |
| customer_id | int unsigned | NO | FK -> customer.customer_id | Pass holder |
| pass_type | enum('MONTHLY','QUARTERLY','ANNUAL') | NO |  | MONTHLY, QUARTERLY or ANNUAL |
| valid_from | date | NO |  | First valid date |
| valid_to | date | NO |  | Last valid date |
| fee | decimal(10,2) | NO |  | Price paid for the pass |

CHECK: `(valid_to >= valid_from)`; `(fee >= 0)`

### parking_session

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| session_id | int unsigned | NO | PK; auto-increment | Unique id of the stay |
| vehicle_id | int unsigned | NO | FK -> vehicle.vehicle_id | Vehicle that parked |
| slot_id | int unsigned | NO | FK -> slot.slot_id | Slot used |
| reservation_id | int unsigned | YES | FK -> reservation.reservation_id; UNIQUE | Reservation honoured, NULL for walk-ins |
| pass_id | int unsigned | YES | FK -> pass.pass_id | Pass used, NULL if none |
| entry_time | datetime | NO | default CURRENT_TIMESTAMP | Gate entry time |
| exit_time | datetime | YES |  | Gate exit time, NULL while the vehicle is inside |
| active_slot_id | int unsigned | YES | generated, UNIQUE | Generated: slot_id while open, else NULL (powers one-active-vehicle-per-slot) |
| active_vehicle_id | int unsigned | YES | generated, UNIQUE | Generated: vehicle_id while open, else NULL |

CHECK: `((exit_time is null) or (exit_time > entry_time))`

### bill

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| bill_id | int unsigned | NO | PK; auto-increment | Unique id of the bill |
| session_id | int unsigned | NO | FK -> parking_session.session_id; UNIQUE | Stay being billed (one bill per stay) |
| tariff_id | int unsigned | NO | FK -> tariff.tariff_id | Tariff used to compute the charge |
| amount | decimal(10,2) | NO | default 0.00 | Charge computed by trigger from duration and tariff |
| bill_status | enum('UNPAID','PARTIAL','PAID') | NO | default UNPAID | UNPAID, PARTIAL or PAID (kept in step by triggers) |
| generated_at | datetime | NO | default CURRENT_TIMESTAMP | When the bill was created |

CHECK: `(amount >= 0)`

### payment

| Column | Type | Null | Key / constraint | Description |
|---|---|---|---|---|
| payment_id | int unsigned | NO | PK; auto-increment | Unique id of the payment |
| bill_id | int unsigned | NO | FK -> bill.bill_id | Bill being paid |
| amount_paid | decimal(10,2) | NO |  | Amount of this payment (> 0) |
| method | enum('CASH','CARD','UPI','WALLET') | NO | default CASH | CASH, CARD, UPI or WALLET |
| paid_at | datetime | NO | default CURRENT_TIMESTAMP | Payment time |

CHECK: `(amount_paid > 0)`
