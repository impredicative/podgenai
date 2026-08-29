import sys

from podgenai.util.threading import exclusive_print


def print_error(error: str) -> bool:
    """Print error message to stderr and return False."""
    exclusive_print(f"Error: {error}", file=sys.stderr)
    return False


def print_warning(warning: str) -> None:
    """Print warning message to stderr."""
    exclusive_print(f"Warning: {warning}", file=sys.stderr)
