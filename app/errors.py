"""Friendly error messages: turns raw MySQL errors into sentences a gate operator understands."""
import re


class ParkingError(Exception):
    """An error whose text can be shown directly to the user."""


class ValidationError(ParkingError):
    """Input rejected by the application before it reaches the database."""


UNIQUE_MESSAGES = {
    "uq_vehicle_reg": "A vehicle with this registration number already exists.",
    "uq_customer_phone": "A customer with this phone number already exists.",
    "uq_customer_email": "A customer with this email already exists.",
    "uq_facility_name": "A facility with this name already exists.",
    "uq_tariff": "A tariff for this facility, vehicle type and date already exists.",
    "uq_bill_session": "This stay has already been billed.",
    "uq_session_reservation": "This reservation has already been used.",
    "uq_vehicle_active_once": "This vehicle is already parked inside.",
    "uq_one_active_vehicle_per_slot": "That slot already holds a vehicle.",
}
CHECK_MESSAGES = {
    "chk_customer_phone": "Phone must be a 10-digit Indian mobile number.",
    "chk_customer_email": "Email address is not valid.",
    "chk_vehicle_reg": "Registration number format is not valid (example: TS09EA1234).",
    "chk_tariff_rate": "Hourly rate must be greater than zero.",
    "chk_tariff_cap": "Daily cap cannot be lower than the hourly rate.",
    "chk_exit_after_entry": "Exit time must be after entry time.",
    "chk_reservation_window": "Reservation expiry must be after its start.",
    "chk_pass_dates": "Pass end date cannot be before its start date.",
    "chk_payment_amount": "Payment amount must be greater than zero.",
}


RULE_WORDING = {
    "vehicle is already parked in that period": "This vehicle is already parked inside.",
    "slot already holds a vehicle in that period": "That slot already holds a vehicle.",
}


def friendly_message(err) -> str:
    code = getattr(err, "errno", None)
    text = getattr(err, "msg", str(err)) or str(err)
    if code == 1644:  # SIGNAL raised by our triggers / procedures
        msg = text.replace("RULE: ", "").strip().rstrip(".")
        for raw, nice in RULE_WORDING.items():
            if msg == raw:
                return nice
        return msg[:1].upper() + msg[1:] + "."
    if code == 1062:
        m = re.search(r"for key '([^']+)'", text)
        key = m.group(1).split(".")[-1] if m else ""
        return UNIQUE_MESSAGES.get(key, "That value already exists.")
    if code == 3819:
        m = re.search(r"'([^']+)'", text)
        return CHECK_MESSAGES.get(m.group(1) if m else "", "A value breaks a database rule.")
    if code == 1451:
        m = re.search(r"`\w+`\.`(\w+)`", text)
        used = m.group(1).replace("_", " ") if m else "other"
        return f"Cannot delete: this record is still used by {used} records."
    if code == 1452:
        return "Cannot save: a related record does not exist."
    if code in (1406, 1264):
        return "A value is too long or out of range."
    if code in (1048, 1364):
        return "A required field is empty."
    if code in (2002, 2003, 2013, 1045, 1049, 1044):
        return ("Cannot connect to the database. Check that MySQL is running and that the "
                "settings in app/config.py (or PARKING_DB_* variables) are correct.")
    return f"Database error: {text}"
