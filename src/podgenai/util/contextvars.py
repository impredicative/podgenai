"""Collect records in a context-local scope and propagate context to worker threads."""

from collections.abc import Callable, Generator, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from threading import Lock

import pandas as pd


class RecordCollector[T]:
    """Store records shared by workers belonging to one collection scope."""

    def __init__(self) -> None:
        self._records: list[T] = []
        self._lock = Lock()

    def record(self, value: T) -> None:
        """Append a record under the collector's lock."""
        with self._lock:
            self._records.append(value)

    def records(self) -> list[T]:
        """Return a synchronized list snapshot containing the original record objects.

        Ordering follows append order, which can vary between concurrent workers.
        The lock protects the list, not subsequent mutations to individual records.
        """
        with self._lock:
            return list(self._records)

    def to_dataframe[R: Mapping[str, object]](self: RecordCollector[R]) -> pd.DataFrame:
        """Return string-keyed mapping records as a DataFrame with keys as columns.

        This method requires mapping records; other record types can use records().
        Conversion uses a synchronized list snapshot and runs outside the lock.
        An empty collector produces an empty DataFrame.
        """
        return pd.DataFrame.from_records(self.records()).convert_dtypes()


@contextmanager
def collect_records[T](variable: ContextVar[RecordCollector[T] | None]) -> Generator[RecordCollector[T]]:
    """Collect into a fresh collector and restore the previous context on exit.

    Declare the supplied ContextVar at module level, normally with default=None.
    Nested scopes collect independently, restoring the outer collector even if
    an exception occurs. Wait for all submitted work before leaving the scope
    or taking the final snapshot; this context manager does not join workers.
    """
    collector = RecordCollector[T]()
    with variable.set(collector):
        yield collector


def record[T](variable: ContextVar[RecordCollector[T] | None], value: T) -> None:
    """Record a value in the active collector, or silently discard it if absent."""
    collector = variable.get(None)
    if collector is not None:
        collector.record(value)


class ContextThreadPoolExecutor(ThreadPoolExecutor):
    """Run each submitted callable in a separate copy of its caller's context.

    Context copies retain references to the same collectors. Each task receives
    its own Context so concurrent workers never try to enter the same Context.
    Nested submissions propagate the submitting worker's current context.

    Inherited map() routes tasks through submit(), including buffered submissions
    in Python 3.14. Consume map() iterators and join workers within the intended
    collection scope so every submission captures that scope's context.
    """

    def submit[**P, R](self, fn: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs) -> Future[R]:
        """Capture the current context separately for this submission."""
        context = copy_context()
        return super().submit(context.run, fn, *args, **kwargs)  # ty: ignore[invalid-return-type]
