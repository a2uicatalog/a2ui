"""Typed errors. Everything the client raises derives from A2UIError."""
from __future__ import annotations


class A2UIError(Exception):
    """Base class for every error this package raises."""


class NetworkError(A2UIError):
    """The request never produced an HTTP response (DNS, connection, timeout)."""


class HTTPError(A2UIError):
    """The server answered with a non-2xx status."""

    def __init__(self, status: int, message: str, body: str = "", retry_after: float | None = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message
        self.body = body
        self.retry_after = retry_after


class RateLimitError(HTTPError):
    """HTTP 429. `retry_after` is the server's Retry-After in seconds when it sent one."""


class UnknownAtomError(A2UIError):
    """The named atom type is not in the published vocabulary."""

    def __init__(self, atom: str, suggestions: list[str] | None = None):
        hint = f" (did you mean {', '.join(suggestions)}?)" if suggestions else ""
        super().__init__(f"unknown atom type {atom!r}{hint}")
        self.atom = atom
        self.suggestions = suggestions or []


class ValidationError(A2UIError):
    """A payload failed the local check. `problems` lists one string per problem."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems
