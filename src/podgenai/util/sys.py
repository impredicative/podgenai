import sys

from podgenai.util.threading import exclusive_print


def current_function_name() -> str:
    """Return the name of the calling function."""
    return sys._getframe(1).f_code.co_qualname


def parent_function_name() -> str:
    """Return the name of the parent function."""
    return sys._getframe(2).f_code.co_name


def print_error(error: str) -> None:
    """Print error message to stderr and return False."""
    exclusive_print(f"Error: {error}", file=sys.stderr)


def print_warning(warning: str) -> None:
    """Print warning message to stderr."""
    exclusive_print(f"Warning: {warning}", file=sys.stderr)
