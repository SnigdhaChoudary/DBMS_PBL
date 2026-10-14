# Viva-Voce Preparation

Short answers you can speak in 20 to 30 seconds. Each answer points to the file where it is shown.

## Project and design

1. **What problem does your project solve?** Manual tickets cause two vehicles to be sent to the same slot and some stays to go unbilled. The database allocates slots live, records every entry and exit, and bills by tariff.
2. **Who are the users?** Customers, gate operators and administrators.
3. **Name the main entities.** Facility, floor, zone, slot, vehicle type, customer, vehicle, reservation, pass, parking session, tariff, bill, payment (13 tables).
4. **Explain the facility to slot hierarchy.** A facility has floors, a floor has zones, a zone has slots. Each is a one-to-many relationship with a foreign key to its parent.
5. **Why is there a vehicle type table?** So slots and tariffs can be matched to bikes, cars and trucks without repeating text.
6. **Which relationships are optional?** A session may have no reservation and no pass (walk-in), so those foreign keys can be NULL.

## Normalization

7. **What is normalization?** Organising tables so each fact is stored once, which avoids update, insert and delete problems.
8. **Define 1NF, 2NF, 3NF.** 1NF: atomic values. 2NF: no partial dependence on part of a composite key. 3NF: no non-key attribute depends on another non-key attribute.
9. **What did you change to reach 3NF?** Removed `customer_id` from reservation, because reservation determines vehicle and vehicle determines customer (a transitive dependency).
10. **Which values are stored although derived, and why?** `bill.amount` (a snapshot, because tariffs change), `bill.bill_status` and `slot.status` (fast search). Triggers keep them correct.
11. **What is a functional dependency? Give an example.** X determines Y. `vehicle_id` determines `reg_number`, `type_id` and `customer_id`.
12. **What is a candidate key? Give one.** A minimal set of columns that identifies a row. `reg_number` in vehicle, besides `vehicle_id`.

## Integrity and SQL

13. **How do you enforce one active vehicle per slot?** A trigger refuses overlapping stays, and a UNIQUE index on the generated column `active_slot_id`, which is NULL once the vehicle exits.
14. **What is a generated column?** A column whose value is computed from other columns by the database.
15. **How do you check slot and vehicle type match?** A BEFORE INSERT trigger compares the two type ids and raises an error if they differ.
16. **Why a trigger and not a CHECK?** CHECK can only look at the row itself. The type match needs data from two other tables.
17. **How is exit after entry enforced?** `CHECK (exit_time IS NULL OR exit_time > entry_time)` plus an update trigger.
18. **Difference between PRIMARY KEY and UNIQUE?** A table has one primary key which cannot be NULL. It can have many UNIQUE keys.
19. **What do ON DELETE RESTRICT and ON UPDATE CASCADE mean?** Deleting a parent that has children is refused. Changing a parent key updates the children.
20. **Explain INNER JOIN and LEFT JOIN with an example.** INNER keeps matching rows only. LEFT keeps all left rows. Q2 uses LEFT JOIN to find customers with no reservation.
21. **Show a nested or correlated subquery.** Q4: bills above the average bill of the same vehicle type.
22. **What is a view and why use one?** A stored query. The reports (occupancy, peak hours, violations) are views, so the front end only selects from them.
23. **What window function did you use?** `RANK() OVER (ORDER BY COUNT(*) DESC)` for peak hours.
24. **How is the bill amount calculated?** `fn_bill_amount` rounds hours up (minimum 1), charges the daily cap for each full day, and the rest at the hourly rate up to the cap. Pass holders pay 0.
25. **What is a stored procedure and which ones do you have?** Saved SQL called by name: `sp_vehicle_entry`, `sp_vehicle_exit`, `sp_make_payment`, `sp_allocate_slot`, `sp_expire_reservations`.

## Transactions and performance

26. **What is a transaction? ACID?** A group of steps that succeeds or fails together. Atomicity, Consistency, Isolation, Durability.
27. **Where does transaction awareness appear?** `sp_vehicle_exit` runs inside START TRANSACTION with a rollback handler. If the bill cannot be created (for example no tariff exists), the exit time is undone too, so a vehicle is never left exited but unbilled. Test T16 proves it. A single INSERT, with the triggers it fires, is also atomic.
28. **Which indexes did you add and why?** `slot(status, type_id)` for free-slot search, `parking_session(entry_time)` for peak hours, slot and time windows for overlap checks.
29. **What stops two gates allocating the same slot at the same moment?** The overlap trigger and the UNIQUE index: the second insert fails and the user sees "slot already holds a vehicle".

## Front end and testing

30. **How does the Python program talk to MySQL?** `mysql-connector-python`. The `Database` class runs queries, the `ParkingService` class holds the operations, and `gui.py` is the Tkinter screen.
31. **How do you prevent SQL injection?** Every query uses `%s` placeholders, so values are never pasted into the SQL text.
32. **How do you validate input?** Python checks the format first (registration, phone, email, dates, amounts). The database checks again, so no route can store bad data.
33. **How are errors shown?** `errors.py` converts MySQL error codes into plain sentences, and the screen shows them in red.
34. **How did you test?** 23 automated tests, 20 database rule tests, and 13 manual screen tests with screenshots.
35. **A bug your tests found?** The slot allocator could pick a slot that was still blocked by a stay with a future exit time. It was fixed by skipping such slots in `sp_allocate_slot`.
36. **What would you improve next?** Gate-camera number plate reading, online payment, a web or mobile front end, and per-facility user logins.
