import sys


def print_error(error: str) -> None:
    print(f"Error: {error}", file=sys.stderr)


def print_warning(warning: str) -> None:
    print(f"Warning: {warning}", file=sys.stderr)
