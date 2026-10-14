import unittest

from app import validators as v
from app.errors import ValidationError


class ValidatorTests(unittest.TestCase):
    def test_registration_is_cleaned_and_checked(self):
        self.assertEqual(v.clean_reg(" ts09 ea-1234 "), "TS09EA1234")
        for bad in ("", "BAD-123", "1234TS09EA", "TS9EA1234", "TS09EA12345"):
            with self.assertRaises(ValidationError):
                v.clean_reg(bad)

    def test_phone(self):
        self.assertEqual(v.clean_phone("+91 98480-12345"), "9848012345")
        for bad in ("12345", "5848012345", "98480123456", "abcdefghij"):
            with self.assertRaises(ValidationError):
                v.clean_phone(bad)

    def test_email(self):
        self.assertEqual(v.clean_email(" Ravi@Example.com "), "ravi@example.com")
        for bad in ("", "no-at-sign", "a@b", "a b@c.com"):
            with self.assertRaises(ValidationError):
                v.clean_email(bad)

    def test_name(self):
        self.assertEqual(v.clean_name("  Anita   Sharma "), "Anita Sharma")
        for bad in ("", "A", "R2D2", "x" * 100):
            with self.assertRaises(ValidationError):
                v.clean_name(bad)

    def test_money(self):
        self.assertEqual(str(v.positive_money("120")), "120.00")
        for bad in ("abc", "0", "-5", "999999999"):
            with self.assertRaises(ValidationError):
                v.positive_money(bad)

    def test_dates(self):
        self.assertEqual(v.parse_datetime("2026-10-12 14:30").hour, 14)
        self.assertEqual(v.parse_date("2026-10-12").day, 12)
        with self.assertRaises(ValidationError):
            v.parse_datetime("12/10/2026 2pm")
        with self.assertRaises(ValidationError):
            v.parse_date("tomorrow")

    def test_integers_and_choices(self):
        self.assertEqual(v.positive_int("30", 1, 100), 30)
        with self.assertRaises(ValidationError):
            v.positive_int("0", 1, 100)
        self.assertEqual(v.clean_choice("upi", ("CASH", "UPI")), "UPI")
        with self.assertRaises(ValidationError):
            v.clean_choice("cheque", ("CASH", "UPI"))


if __name__ == "__main__":
    unittest.main()
