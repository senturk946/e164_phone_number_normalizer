import unittest

from e164_phone_number_normalizer import (
    InvalidNumberError,
    RegionError,
    normalize,
)


class NormalizeTests(unittest.TestCase):
    def test_us_national_with_separators(self):
        self.assertEqual(normalize("(555) 123-4567", "US"), "+15551234567")

    def test_us_national_with_trunk_prefix(self):
        # US numbers are often written with a leading 1.
        self.assertEqual(normalize("1 555 123 4567", "US"), "+15551234567")

    def test_us_already_international(self):
        self.assertEqual(normalize("+1 555 123 4567", "US"), "+15551234567")

    def test_gb_national(self):
        self.assertEqual(normalize("020 7946 0958", "GB"), "+442079460958")

    def test_gb_without_trunk_prefix(self):
        self.assertEqual(normalize("2079460958", "GB"), "+442079460958")

    def test_de_eleven_digit_national(self):
        # German numbers can be 10 or 11 digits after the country code.
        self.assertEqual(normalize("030 12345678", "DE"), "+493012345678")
        self.assertEqual(normalize("0151 23456789", "DE"), "+4915123456789")

    def test_it_no_trunk_prefix(self):
        # Italy does not use a trunk prefix; leading zeros are significant.
        self.assertEqual(normalize("02 12345678", "IT"), "+390212345678")

    def test_region_is_case_insensitive(self):
        self.assertEqual(normalize("020 7946 0958", "gb"), "+442079460958")

    def test_plus_overrides_region(self):
        # A leading plus means the region argument is not used for parsing.
        self.assertEqual(normalize("+33 1 23 45 67 89", "US"), "+33123456789")

    def test_empty_number(self):
        with self.assertRaises(InvalidNumberError):
            normalize("", "US")

    def test_number_with_no_digits(self):
        with self.assertRaises(InvalidNumberError):
            normalize("---", "US")

    def test_number_with_letters(self):
        with self.assertRaises(InvalidNumberError):
            normalize("555-CALL-NOW", "US")

    def test_wrong_length_for_region(self):
        with self.assertRaises(InvalidNumberError):
            normalize("12345", "US")

    def test_unknown_region(self):
        with self.assertRaises(RegionError):
            normalize("5551234567", "XX")

    def test_non_string_number(self):
        with self.assertRaises(InvalidNumberError):
            normalize(5551234567, "US")  # type: ignore[arg-type]

    def test_non_string_region(self):
        with self.assertRaises(RegionError):
            normalize("5551234567", None)  # type: ignore[arg-type]

    def test_international_too_short(self):
        with self.assertRaises(InvalidNumberError):
            normalize("+123456", "US")

    def test_international_too_long(self):
        with self.assertRaises(InvalidNumberError):
            normalize("+1234567890123456", "US")

    def test_leading_plus_with_separators(self):
        self.assertEqual(normalize("+ 1 (555) 123-4567", "US"), "+15551234567")

    def test_whitespace_only_number(self):
        with self.assertRaises(InvalidNumberError):
            normalize("   ", "US")


if __name__ == "__main__":
    unittest.main()
