# User Guide

Start the program with `python main.py`. The window has one tab for each job. Messages appear in the bar at the bottom: green means done, red means something was refused and why.

| Tab | What you do there |
|---|---|
| **Zoom (every page)** | Make everything bigger or smaller: click **A+** or **A-** in the top-right of the header, press **Ctrl and +** or **Ctrl and -**, or hold **Ctrl** and turn the mouse wheel. **Ctrl and 0** (or clicking the percentage) returns to 100%. Levels run from 80% to 200%. The program remembers your choice. When zoomed, a page that no longer fits scrolls with the mouse wheel. |
| **Dashboard** | See vehicles inside, free and occupied slots, unpaid money and violations. Occupancy is shown per floor. "Expire old reservations" marks unused bookings as expired. |
| **Slot Search** | Choose a facility and vehicle type, press Search to list free slots. Switch "Show" to *Under maintenance* to see closed slots. An administrator can close or reopen the selected slot. |
| **Gate** | **Entry:** type the registration number, pick the facility, press *Allow entry*. The system picks the slot. A valid reservation or pass is used automatically. **Exit:** select the vehicle in the table and press *Exit and generate bill*. The optional "Simulate stay" box is only for demonstrations: it pretends the vehicle stayed that many minutes, and the vehicle cannot re-enter until that time has passed. |
| **Reservations** | Type the registration number, pick the facility and a time window (YYYY-MM-DD HH:MM). The system finds a free slot of the right type. Cancel a booking by selecting it. |
| **Billing** | Choose a bill, enter the amount and method, press *Pay*. Part payments are allowed. *Fill full balance* copies the balance. |
| **Customers** | Add, update, delete and search customers. Click a row to edit it. |
| **Vehicles** | Add, update, delete and search vehicles. Each vehicle has an owner and a type (Bike, Car, Truck). |
| **Passes** | Sell a monthly, quarterly or annual pass, renew one, or delete one that was never used. |
| **Tariffs** | Add a new price from a given date, or change the selected one. Old stays keep the price that applied when they began. |
| **Reports** | Pick a report, press Run. Charts are drawn for peak hours, occupancy and revenue. *Export to CSV* saves the table. |

## Billing rules in plain words

- Time is rounded **up** to whole hours, with a minimum of one hour.
- Every full 24 hours costs the daily cap. The remaining hours cost hours x rate, but never more than the cap.
- A vehicle with a valid pass is billed Rs 0.
- The amount is calculated by the database, so it cannot be typed in by hand.

## Common messages

| Message | Meaning |
|---|---|
| This vehicle is already parked inside. | The registration number already has an open stay. |
| No free slot of the required type in this facility. | Every slot for that vehicle type is taken or closed. |
| Slot is reserved by another customer at this time. | A booking protects that slot right now. |
| Payment exceeds the outstanding bill amount. | The amount is more than the balance. |
| Cannot delete: this record is still used by ... | Other records still point to it. |
