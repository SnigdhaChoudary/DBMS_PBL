"""Settings. Override with environment variables instead of editing the code."""
import os

DB_CONFIG = {
    "host": os.getenv("PARKING_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("PARKING_DB_PORT", "3306")),
    "user": os.getenv("PARKING_DB_USER", "parking_app"),
    "password": os.getenv("PARKING_DB_PASSWORD", "parking123"),
    "database": os.getenv("PARKING_DB_NAME", "smart_parking"),
}

# plan name -> (days of validity, price in rupees)
PASS_PLANS = {
    "MONTHLY": (30, 1500),
    "QUARTERLY": (90, 4000),
    "ANNUAL": (365, 12000),
}
PAYMENT_METHODS = ("CASH", "CARD", "UPI", "WALLET")
