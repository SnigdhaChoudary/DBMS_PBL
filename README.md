# Smart Parking Lot Allocation and Billing System

A MySQL database with a Python (Tkinter) desktop application for live parking slot allocation, reservations, gate entry and exit, duration billing, passes, payments and reports.

## What it does

| Job | Where |
|---|---|
| Find free slots by facility and vehicle type | Slot Search tab |
| Allow entry, pick a slot automatically, use a reservation or pass if the vehicle has one | Gate tab |
| Exit, calculate the bill from time and tariff | Gate tab |
| Book a slot for a time window, cancel, expire unused bookings | Reservations tab |
| Take full or part payments | Billing tab |
| Add, change, delete and search customers and vehicles | Customers and Vehicles tabs |
| Sell, renew and delete passes | Passes tab |
| Change prices | Tariffs tab |
| Occupancy, peak hours, durations, pass usage, violations, free slots, revenue (with charts and CSV export) | Reports tab |

## Zoom and clarity

Use **A+ / A-** in the header, **Ctrl +** and **Ctrl -**, or **Ctrl + mouse wheel** to zoom from 80% to 200%. **Ctrl 0** resets. On Windows the program switches on high-DPI mode so text stays sharp on laptops with 125% or 150% display scaling.

## Requirements

- MySQL 8.0.16 or newer (CHECK constraints are enforced from this version)
- Python 3.9 or newer with Tkinter (included with Python on Windows and macOS; on Ubuntu run `sudo apt install python3-tk`)
- `pip install -r requirements.txt`

## Setup in five steps

```bash
# 1. create the database account the program uses (run once, as the MySQL admin)
mysql -u root -p < sql/00_create_app_user.sql
# 2. create tables, rules, triggers and procedures
mysql -u root -p < sql/01_schema.sql
# 3. load the sample data and the report views
mysql -u root -p smart_parking < sql/02_sample_data.sql
mysql -u root -p smart_parking < sql/03_views.sql
# 4. install the connector
pip install -r requirements.txt
# 5. start the program
python main.py
```

`python tools/reset_db.py` repeats steps 1 to 3 in one go. If your MySQL admin account is not `root` without a password, set `PARKING_ADMIN_ARGS`, for example `PARKING_ADMIN_ARGS="-u root -pYourPassword"`.

The app logs in as `parking_app` / `parking123` on `127.0.0.1:3306`. Change this with the environment variables `PARKING_DB_HOST`, `PARKING_DB_PORT`, `PARKING_DB_USER`, `PARKING_DB_PASSWORD`, `PARKING_DB_NAME` or by editing `app/config.py`.

## Folder layout

```
smart_parking_project/
  main.py                  start the application
  app/
    config.py              database settings, pass plans, payment methods
    db.py                  MySQL connection wrapper (parameterised queries, friendly errors)
    errors.py              turns MySQL errors into plain sentences
    validators.py          input checks (registration, phone, email, money, dates)
    services.py            all operations: search, gate, reservations, billing, CRUD, passes, tariffs
    reports.py             report queries and chart definitions
    theme.py               colours, fonts, spacing, zoom scale and ttk styles (the design system)
    settings.py            remembers the zoom level between runs
    widgets.py             reusable themed widgets: buttons, panels, tables, cards, charts
    gui.py                 the Tkinter screen (10 pages)
  sql/                     00 user, 01 schema, 02 data, 03 views, 04 queries, 05 rule tests, 06 SQL demo
  tests/                   23 automated tests (validators and services against MySQL)
  tools/                   reset_db.py, demo_run.py (console walk-through), make_screenshots.py
  docs/                    data dictionary and 3NF, user guide, test cases and results, viva questions
  screenshots/             18 output screens of the running application
```

## Testing

```bash
python -m unittest discover -s tests -v     # 23 tests; rebuilds the database first
python tools/demo_run.py                    # scripted walk-through printed in the console
mysql -u root -p -f smart_parking < sql/05_constraint_tests.sql   # 20 statements that must be refused
```

## Business rules, enforced inside MySQL

| Rule | How |
|---|---|
| One active vehicle per slot | Overlap trigger plus UNIQUE index on a generated column |
| Slot and vehicle type match | Entry and reservation triggers |
| Exit after entry | CHECK constraint plus update trigger |
| Reservation expiry | Entry trigger and `sp_expire_reservations()` |
| Tariff-based charges | `fn_bill_amount()` run by the bill trigger; the amount cannot be typed in |
| Exit and bill succeed together | `sp_vehicle_exit` runs in one transaction with rollback |

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot connect to the database" | Start MySQL; check the user from step 1 exists and the settings above |
| `No module named tkinter` | Install Tkinter (Ubuntu: `sudo apt install python3-tk`) |
| `Check constraint ... is not supported` or syntax errors | MySQL is older than 8.0.16, or this is MariaDB. Use MySQL 8 |
| Step 2 fails with a SUPER privilege message | Run the SQL files as the MySQL root account |

## Submitting on GitHub

```bash
git init
git add .
git commit -m "Smart parking DBMS: schema, Python app, tests, report"
git branch -M main
git remote add origin https://github.com/<your-username>/smart-parking-dbms.git
git push -u origin main
```
