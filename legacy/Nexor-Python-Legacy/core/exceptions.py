class NexorError(Exception):
    """Base exception for Nexor."""
    pass


class LogParseError(NexorError):
    """Raised when a log cannot be parsed."""
    pass


class LogValidationError(NexorError):
    """Raised when parsed data is invalid or incomplete."""
    pass