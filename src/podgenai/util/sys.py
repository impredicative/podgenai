import sys


def print_error(error: str) -> bool:
    """Print error message to stderr and return False."""
    print(f"Error: {error}", file=sys.stderr)
    return False


def print_warning(warning: str) -> None:
    """Print warning message to stderr."""
    print(f"Warning: {warning}", file=sys.stderr)
