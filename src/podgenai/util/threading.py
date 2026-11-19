import threading
from collections.abc import Generator
from contextlib import contextmanager
from functools import wraps

from podgenai.util.input import get_confirmation

_CONSOLE_LOCK = threading.RLock()


@contextmanager
def exclusive_prompt(prompt: str, *, confirm: bool = True, enabled: bool = True) -> Generator[None]:
    """Provide an exclusive console prompt context.

    When enabled, it acquires the shared console lock, prints the prompt, and
    optionally waits for the user to press Enter before yielding control to
    the context body. The lock remains held until the context body exits.

    When disabled, it yields immediately without acquiring the lock, printing
    the prompt, or waiting for input.

    Caution:
        Exclusivity is cooperative: output written without acquiring
        the console lock (for example, by calling `print()` directly from
        another thread) can still interleave with this context.

    Args:
        prompt: The prompt text to print.
        confirm: Whether to seek user confirmation.
        enabled: Whether exclusive prompting is enabled.
    """
    if not enabled:
        yield
        return
    with _CONSOLE_LOCK:
        print(">>>PROMPT BEGIN\n" + prompt + "\n<<<PROMPT END")
        if confirm:
            get_confirmation("prompt completion")
        yield


def exclusive_print(*args, **kwargs) -> None:
    """Print while holding the shared console lock.

    It serializes this output with other operations that acquire the shared
    console lock.

    Arguments are forwarded to `print`.
    """
    with _CONSOLE_LOCK:
        print(*args, **kwargs)


def limit_concurrency(n: int):
    """
    Decorator that limits concurrent executions of a function to at most n threads.

    If the concurrency limit is reached, additional callers block until
    an active execution completes and releases a semaphore permit.

    Each application of the decorator creates an independent semaphore,
    so concurrency limits are maintained separately for each decorated
    function.

    Args:
        n (int): Maximum number of concurrent executions. Must be >= 1.

    Returns:
        Callable: A decorator that enforces the specified concurrency limit.

    Raises:
        ValueError: If n is less than 1.

    Notes:
        - Thread-safe; intended for use with multiple threads in one process.
        - Waiting callers are not guaranteed to proceed in FIFO order.
        - Semaphore permits are released even if the function raises an exception.
        - Recursive or reentrant calls may deadlock if all permits are held.
        - Does not enforce concurrency limits across multiple processes.
    """
    if n < 1:
        raise ValueError("n must be at least 1")

    semaphore = threading.BoundedSemaphore(n)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with semaphore:
                return func(*args, **kwargs)

        return wrapper

    return decorator
