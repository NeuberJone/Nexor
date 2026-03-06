from __future__ import annotations


class NexorError(Exception):
    """Base exception for Nexor."""


class LogParseError(NexorError):
    """Raised when a production log cannot be parsed."""


class LogValidationError(NexorError):
    """Raised when parsed log data is incomplete or invalid."""