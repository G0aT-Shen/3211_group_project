"""Domain exceptions exposed by the PIM application."""


class PIMException(Exception):
    """Base class for expected, user-facing application errors."""


class InvalidCommandError(PIMException):
    """A command or command argument is invalid."""


class SearchParseError(PIMException):
    """A search expression cannot be parsed or evaluated."""


class PIRNotFoundError(PIMException):
    """The requested personal information record does not exist."""


class ValidationError(PIMException):
    """A model field has an invalid value."""


class StorageError(PIMException):
    """A .pim file cannot be read, written, or validated."""
