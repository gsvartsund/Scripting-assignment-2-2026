import re
# Import the specific exceptions.
from .exceptions import InvalidIdentifierError, InvalidRecordError

# These are the allowed IDs.
PARTICIPANT_ID_PATTERN = r"P\d{3}"
SESSION_ID_PATTERN = r"FIT-\d{4}-\d{3}"

# This def checks if an identifier has the correct format
def check_identifier(value, pattern, field):
    if re.fullmatch(pattern, value) is None:
        raise InvalidIdentifierError(
            f"'{value}' is not a valid {field} (expected pattern {pattern})",
            field,
        )
    return value

# This def converts a text value from a CSV file into a number
def to_number(text, field, whole_number=False):
    if text.strip() == "":
        raise InvalidRecordError("missing value", field)

    try:
        if whole_number:
            return int(text)
        return float(text)
    except ValueError:
        kind = "whole number" if whole_number else "number"
        raise InvalidRecordError(f"'{text}' is not a valid {kind}", field) from None

# This def verifies that a number is inside a valid minimum and maximum range.
def check_range(value, field, low, high):
    if not (low <= value <= high):
        raise InvalidRecordError(
            f"{field} {value} is outside the allowed range {low} to {high}",
            field,
        )
    return value
# THis def checks if the identifier matches the pattern.
def is_valid_identifier(value, pattern):
    return re.fullmatch(pattern, value) is not None
