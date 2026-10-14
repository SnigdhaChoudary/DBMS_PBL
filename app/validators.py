"""Input validation done in Python BEFORE the database is touched.
(The database repeats the important checks, so bad data cannot get in by any route.)"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .errors import ValidationError

REG_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$")
PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,79}$")


def clean_name(value):
    v = " ".join((value or "").split())
    if not NAME_RE.match(v):
        raise ValidationError("Name must be 2 to 80 letters (spaces, dots and hyphens allowed).")
    return v


def clean_phone(value):
    v = re.sub(r"[\s\-]", "", value or "")
    if v.startswith("+91"):
        v = v[3:]
    if not PHONE_RE.match(v):
        raise ValidationError("Phone must be a 10-digit mobile number starting with 6, 7, 8 or 9.")
    return v


def clean_email(value):
    v = (value or "").strip().lower()
    if not EMAIL_RE.match(v) or len(v) > 100:
        raise ValidationError("Enter a valid email address, for example name@example.com.")
    return v


def clean_reg(value):
    v = re.sub(r"[\s\-]", "", (value or "").upper())
    if not REG_RE.match(v):
        raise ValidationError("Registration number must look like TS09EA1234 "
                              "(2 letters, 2 digits, 1 to 3 letters, 4 digits).")
    return v


def positive_money(value, maximum=100000):
    try:
        v = Decimal(str(value).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValidationError("Enter the amount as a number, for example 120 or 120.50.")
    if v <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if v > maximum:
        raise ValidationError(f"Amount cannot be more than {maximum}.")
    return v


def positive_int(value, low, high, label="Value"):
    try:
        v = int(str(value).strip())
    except ValueError:
        raise ValidationError(f"{label} must be a whole number.")
    if not low <= v <= high:
        raise ValidationError(f"{label} must be between {low} and {high}.")
    return v


def parse_datetime(value, label="Date and time"):
    text = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValidationError(f"{label} must look like 2026-10-12 14:30.")


def parse_date(value, label="Date"):
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"{label} must look like 2026-10-12.")


def clean_choice(value, allowed, label="Value"):
    v = (value or "").strip().upper()
    if v not in allowed:
        raise ValidationError(f"{label} must be one of: {', '.join(allowed)}.")
    return v


def require_id(value, label="record"):
    if value is None or value == "":
        raise ValidationError(f"Select a {label} first.")
    return int(value)
