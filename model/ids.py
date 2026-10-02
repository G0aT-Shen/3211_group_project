"""Shared ID limits for model records, persistence and CLI representation."""
from .exceptions import ValidationError

MAX_ID_DIGITS = 100
MAX_RECORD_ID = 10 ** MAX_ID_DIGITS - 1
# Retain this high-water mark after allocating/deleting the last usable ID.
EXHAUSTED_NEXT_ID = MAX_RECORD_ID + 1


def validate_record_id(value: int) -> None:
    if type(value) is not int or not 1 <= value <= MAX_RECORD_ID:
        raise ValidationError(f"ID must be a positive integer (up to {MAX_ID_DIGITS} digits)")


def validate_next_id(value: int) -> None:
    if type(value) is not int or not 1 <= value <= EXHAUSTED_NEXT_ID:
        raise ValidationError("next_id must be a positive integer no greater than the exhausted ID marker")
