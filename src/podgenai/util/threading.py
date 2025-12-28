import threading

_PRINT_LOCK = threading.Lock()


def safe_print(*args, **kwargs) -> None:
    with _PRINT_LOCK:
        print(*args, **kwargs)
