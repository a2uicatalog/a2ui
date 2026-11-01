"""a2uicatalog: official Python client for the A2UI Atomic Catalog (https://a2uicatalog.ai)."""
from .client import DEFAULT_BASE_URL, SURFACES, Client
from .errors import (A2UIError, HTTPError, NetworkError, RateLimitError, UnknownAtomError,
                     ValidationError)

__version__ = "0.1.0"
__all__ = ["Client", "DEFAULT_BASE_URL", "SURFACES", "A2UIError", "HTTPError", "NetworkError",
           "RateLimitError", "UnknownAtomError", "ValidationError", "__version__"]
