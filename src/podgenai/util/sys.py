import sys


def print_error(error: str) -> None:
    """Print error message to stderr."""
    print(f"Error: {error}", file=sys.stderr)


def print_warning(warning: str) -> None:
    """Print warning message to stderr."""
    print(f"Warning: {warning}", file=sys.stderr)
