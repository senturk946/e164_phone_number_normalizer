"""Core normalization logic for E.164 phone numbers.

Design notes:

* The library is deliberately data-driven: each supported region has a
  country calling code and a national-number length (or lengths).  The
  parser strips a single leading national trunk prefix when the region
  defines one, removes punctuation, then validates the remaining digits
  against the region's length set.

* We do not attempt to validate the *semantic* structure of national
  numbers (mobile vs. landline, area codes, etc.).  That would require a
  much larger, frequently-updated dataset.  The trade-off is documented in
  the README: we accept any digit string of the right length, which is
  enough for storage and dialing, but not for carrier routing decisions.

* Inputs are handled as strings only.  Accepting integers would silently
  lose leading zeros (e.g. Italian numbers) and would make the API
  ambiguous about how to interpret the value.
"""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, Optional, Tuple


class InvalidNumberError(ValueError):
    """Raised when a number cannot be normalized to E.164."""


class RegionError(ValueError):
    """Raised when an unknown region code is requested."""


# Region data: ISO 3166-1 alpha-2 -> (country calling code, trunk prefix,
# allowed national-number lengths).
#
# The trunk prefix is the digit(s) stripped from a national-format number
# before the country code is prepended.  ``None`` means the region uses no
# trunk prefix (or it is not consistently used).
#
# Lengths are the *national significant number* lengths, i.e. the digits
# that appear after the country code in E.164.
_REGIONS: Dict[str, Tuple[str, Optional[str], FrozenSet[int]]] = {
    "US": ("1", "1", frozenset({10})),
    "CA": ("1", "1", frozenset({10})),
    "GB": ("44", "0", frozenset({10})),
    "DE": ("49", "0", frozenset({10, 11})),
    "FR": ("33", "0", frozenset({9})),
    "IT": ("39", None, frozenset({9, 10})),
    "ES": ("34", None, frozenset({9})),
    "NL": ("31", "0", frozenset({9})),
    "BE": ("32", "0", frozenset({9})),
    "CH": ("41", "0", frozenset({9})),
    "AT": ("43", "0", frozenset({10, 11})),
    "SE": ("46", "0", frozenset({7, 8, 9})),
    "NO": ("47", None, frozenset({8})),
    "DK": ("45", None, frozenset({8})),
    "FI": ("358", "0", frozenset({9, 10})),
    "PL": ("48", None, frozenset({9})),
    "PT": ("351", None, frozenset({9})),
    "IE": ("353", "0", frozenset({9})),
    "AU": ("61", "0", frozenset({9})),
    "NZ": ("64", "0", frozenset({8, 9})),
    "JP": ("81", "0", frozenset({10})),
    "KR": ("82", "0", frozenset({9, 10})),
    "CN": ("86", "0", frozenset({11})),
    "IN": ("91", "0", frozenset({10})),
    "BR": ("55", "0", frozenset({10, 11})),
    "MX": ("52", None, frozenset({10})),
    "ZA": ("27", "0", frozenset({9})),
}


# Characters that are commonly used as visual separators in phone numbers.
# We strip them before digit extraction so that "(555) 123-4567" and
# "555.123.4567" behave identically.
_SEPARATOR_RE = re.compile(r"[\s\-()./]+")

# A single leading plus is the only non-digit we keep; it signals that the
# caller is already providing an international-format number.
_LEADING_PLUS_RE = re.compile(r"^\+\s*")


def _clean(number: str) -> str:
    """Return the digits of *number*, preserving a single leading '+'.

    We deliberately do not use ``str.isdigit`` here because it accepts
    non-ASCII digits (e.g. Arabic-Indic numerals) that are not valid in
    E.164.  ``[0-9]`` is the only character class we accept.
    """
    if not isinstance(number, str):
        raise InvalidNumberError("number must be a string")
    number = number.strip()
    if not number:
        raise InvalidNumberError("number is empty")
    has_plus = bool(_LEADING_PLUS_RE.match(number))
    if has_plus:
        number = _LEADING_PLUS_RE.sub("", number, count=1)
    # Remove separators, then reject anything that is not a digit.
    number = _SEPARATOR_RE.sub("", number)
    if not number:
        raise InvalidNumberError("number contains no digits")
    if not all("0" <= ch <= "9" for ch in number):
        raise InvalidNumberError("number contains non-digit characters")
    return ("+" if has_plus else "") + number


def normalize(number: str, region: str) -> str:
    """Normalize *number* to E.164 format using the rules for *region*.

    Parameters
    ----------
    number:
        The phone number to normalize.  May include a leading ``+`` and
        common visual separators (spaces, hyphens, parentheses, dots,
        slashes).  Must contain at least one digit.
    region:
        ISO 3166-1 alpha-2 region code (case-insensitive) used to interpret
        national-format numbers.  Ignored when *number* already starts with
        ``+``.

    Returns
    -------
    str
        The number in E.164 format, e.g. ``"+15551234567"``.

    Raises
    ------
    InvalidNumberError
        If the number is empty, contains non-digit characters, or does not
        match the expected length for the region.
    RegionError
        If *region* is not a known region code.
    """
    if not isinstance(region, str):
        raise RegionError("region must be a string")
    region = region.strip().upper()
    if region not in _REGIONS:
        raise RegionError("unknown region: {!r}".format(region))

    cleaned = _clean(number)

    if cleaned.startswith("+"):
        digits = cleaned[1:]
        # International input: we trust the country code but still enforce
        # a sane length.  E.164 allows up to 15 digits total.
        if not (7 <= len(digits) <= 15):
            raise InvalidNumberError(
                "international number must have 7-15 digits, got {}".format(
                    len(digits)
                )
            )
        return "+" + digits

    country_code, trunk_prefix, lengths = _REGIONS[region]
    digits = cleaned
    if trunk_prefix is not None and digits.startswith(trunk_prefix):
        digits = digits[len(trunk_prefix):]
    if len(digits) not in lengths:
        raise InvalidNumberError(
            "national number for {} must have length {}, got {}".format(
                region, sorted(lengths), len(digits)
            )
        )
    # The country code itself is not length-checked here; the region table
    # is the authority on that and is validated at import time by the tests.
    return "+" + country_code + digits
