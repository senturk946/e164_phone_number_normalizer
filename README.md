# e164_phone_number_normalizer

Normalizes phone number strings into E.164 format using per-region rules.

```python
from e164_phone_number_normalizer import normalize

normalize("(555) 123-4567", "US")
# '+15551234567'

normalize("020 7946 0958", "GB")
# '+442079460958'

normalize("+33 1 23 45 67 89", "US")
# '+33123456789'  -- the leading '+' overrides the region argument
```

The public API is exactly three names: `normalize(number, region)`, `InvalidNumberError`, and `RegionError`.

## Why this exists

Storing phone numbers as free-form text makes deduplication and dialing unreliable. The usual approach is to pull in a large metadata package such as `phonenumbers`, which carries a full numbering-plan database. That is the right tool when you need carrier routing or number-type detection, but it is a heavy dependency for services that only need a canonical string.

This library takes the opposite trade-off: a small, hand-maintained table of country calling codes, trunk prefixes, and national-number lengths. It validates length and strips formatting, but it does **not** verify area codes, mobile prefixes, or number types. That keeps the dependency count at zero and the code auditable, at the cost of accepting some numbers that a full numbering-plan library would reject.

## The awkward edge

Italy does not use a trunk prefix, and leading zeros are part of the national number. `normalize("02 12345678", "IT")` therefore returns `+390212345678`, not `+39212345678`. The region table encodes this by leaving the trunk prefix unset for Italy. If you are normalizing Italian numbers, do not strip the leading zero yourself.

A second edge: when the input starts with `+`, the `region` argument is ignored entirely. This is intentional — an explicit international prefix is more authoritative than a default region — but it means a typo in the region will not be caught for numbers that already carry a country code.

## Errors

- `InvalidNumberError` is raised for empty input, non-digit characters, wrong national-number length, and out-of-range international lengths (7–15 digits).
- `RegionError` is raised for unknown or non-string region codes.

Both inherit from `ValueError`.
