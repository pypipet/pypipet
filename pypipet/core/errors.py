"""Base Error classes."""
import functools
import io
import logging

def error(error_cls):
    class Error(error_cls):
        """Aggregate multiple sub-exceptions."""

        def __init__(self, exceptions):
            self.exceptions = exceptions

        def __str__(self):
            return "\n".join(str(e) for e in self.exceptions)

    if error_cls != Exception:
        error_cls.Aggregate = Error

    return error_cls


CustomerizedError = error(Exception)

class DialectNotSupportedError(Exception):
    def exit_code(self):
        return 1