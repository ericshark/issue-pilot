"""Shared mapping from Anthropic SDK exceptions to user-readable messages."""

from anthropic import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)


def describe_api_error(error: APIConnectionError | APIStatusError) -> str:
    """Return a short, safe explanation for an SDK failure.

    Most-specific classes first so a bad key or rate limit reads as such
    instead of a bare HTTP status.
    """

    if isinstance(error, AuthenticationError):
        return "The Claude API rejected the server's API key."
    if isinstance(error, PermissionDeniedError):
        return "The server's API key is not allowed to use this model."
    if isinstance(error, RateLimitError):
        return "The Claude API is rate limiting requests; try again shortly."
    if isinstance(error, APIStatusError):
        if error.status_code >= 500:
            return "The Claude API is having trouble; try again shortly."
        return f"The Claude API returned an error (HTTP {error.status_code})."
    return "Could not reach the Claude API."
