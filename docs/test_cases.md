# Test Cases and Results

## 1. Automated tests (`python -m unittest discover -s tests -v`)

23 tests, all passing. Full output: `docs/test_results.txt`. They rebuild the database first, so they are repeatable.

| # | Area | What is checked | Expected |
|---|---|---|---|
| T1 | Dashboard, search | 5 vehicles inside; car search returns only car slots | Pass |
| T2 | Slot status | Free slot can be closed and reopened; an occupied slot cannot be closed | Pass |
| T3 | Gate and billing | Entry allots a car slot; second entry refused; 200 min at Rs 25 = Rs 100; part payment gives PARTIAL; overpayment refused; full payment gives PAID; second exit refused | Pass |
| T4 | Reservation entry | A vehicle with a live reservation uses it; a 20 min stay costs the one-hour minimum Rs 30 | Pass |
| T5 | Daily cap | 10 hours at Rs 30 = 300 is capped at Rs 250 | Pass |
| T6 | Pass holder | Valid pass is applied automatically; bill Rs 0 and PAID | Pass |
| T7 | Input validation | Unknown vehicle, bad registration, non-numeric amount, wrong payment method are refused | Pass |
| T8 | Reservations | Same-time bookings get different slots; cancel works; past and reversed windows refused | Pass |
| T9 | Expiry | `sp_expire_reservations` runs | Pass |
| T10 | Customer CRUD | Create, duplicate phone refused, invalid phone refused, update, delete, delete-in-use refused | Pass |
| T11 | Vehicle CRUD | Create (number cleaned to upper case), duplicate refused, invalid refused, update type, delete | Pass |
| T12 | Passes | Buy, renew starts after the old pass, delete, unknown plan refused | Pass |
| T13 | Tariffs | Add, update, duplicate refused, negative rate refused | Pass |
| T14 | Reports | All 10 reports run | Pass |
| T15 | Error wording | A raw CHECK-constraint error becomes a plain sentence | Pass |
| T16 | Transaction | Billing fails (no tariff for the vehicle type), so the exit time is rolled back and the vehicle stays inside | Pass |
| V1-V7 | Validators | Registration, phone, email, name, money, dates, integers and choices | Pass |

## 2. Database rule tests (`sql/05_constraint_tests.sql`)

20 statements that must fail. All 20 are refused by the database with a clear message (see Review 2 slides).

## 3. Manual screen tests (screenshots in `screenshots/`)

| # | Action on screen | Expected | Screenshot |
|---|---|---|---|
| M1 | Open Dashboard | Counts and occupancy table shown | 01 |
| M2 | Search free Car slots, Lakeview | 22 free slots listed | 02 |
| M3 | Enter MH12AB3030 | Slot C01, floor -1 allotted | 03 |
| M4 | Exit with simulated stay of 200 min | Bill Rs 120.00 | 04 |
| M5 | Pay Rs 50 by UPI | Status PARTIAL | 05 |
| M6 | Reserve for TS08GH7788 | Slot found, reservation listed | 06 |
| M7 | Add customer Kiran Kumar | Appears in table | 07 |
| M8 | Add customer with phone 12345 | Red message, nothing saved | 08 |
| M9 | Delete customer 1 (owns vehicles) | "Cannot delete" message | 09 |
| M10 | Enter a vehicle already inside | "Already parked inside" message | 10 |
| M11 | Reserve an unregistered vehicle | "No vehicle with that registration number" | 11 |
| M12 | Sell a quarterly pass | New row in Passes | 13 |
| M13 | Run Peak hours, Violations, Revenue, Occupancy | Table and chart shown | 15 to 18 |

## 4. Zoom and display checks

| # | Check | Result |
|---|---|---|
| Z1 | All 10 pages open at 80%, 100%, 125%, 160% and 200% | Pass |
| Z2 | Gate, billing, reservation, customer, pass and report workflows run at 100%, 150% and 200% (58 checks) | Pass |
| Z3 | Zoom keys, A+/A- buttons and Ctrl + mouse wheel change the zoom and keep the current tab | Pass |
