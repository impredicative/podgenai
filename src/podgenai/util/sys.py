import sys


def print_error(error: str) -> None:
    print(f'Error: {error}', file=sys.stderr)
