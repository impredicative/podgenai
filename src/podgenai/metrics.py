"""Aggregate and format token usage."""

from collections.abc import Iterable
from math import nan

from podgenai.types import TokenMetric, TokenMetricsSummaryExtras

_METRIC_COLUMNS: tuple[str, ...] = (
    "calls",
    "sum_input_tokens",
    "avg_input_tokens",
    "sum_cache_read_tokens",
    "calls_with_cache_read",
    "sum_cache_write_tokens",
    "calls_with_cache_write",
    "sum_output_tokens",
    "avg_output_tokens",
)

type _TokenMetricsRow = dict[str, int]
type _TokenMetricsTable = dict[str | None, _TokenMetricsRow]


def summarize_token_metrics(records: Iterable[TokenMetric]) -> tuple[str, TokenMetricsSummaryExtras]:
    """Return (table, extras) with token usage by cache key and overall cache rates.

    None is a distinct cache key. Missing counts contribute zero, and every
    record contributes to the call count and average denominators. Averages
    are rounded to integers, with ties rounded to the nearest even integer.
    Rates use totals across all groups and are NaN for zero denominators.
    An empty iterable produces an empty table and NaN rates.
    """
    table: _TokenMetricsTable = {}
    for record in records:
        prompt_cache_key = record["prompt_cache_key"]
        if prompt_cache_key not in table:
            table[prompt_cache_key] = dict.fromkeys(_METRIC_COLUMNS, 0)
        group = table[prompt_cache_key]
        input_tokens = record["input_tokens"] or 0
        cache_read_tokens = record["cache_read_tokens"] or 0
        cache_write_tokens = record["cache_write_tokens"] or 0
        output_tokens = record["output_tokens"] or 0

        group["calls"] += 1
        group["sum_input_tokens"] += input_tokens
        group["sum_cache_read_tokens"] += cache_read_tokens
        group["calls_with_cache_read"] += int(cache_read_tokens > 0)
        group["sum_cache_write_tokens"] += cache_write_tokens
        group["calls_with_cache_write"] += int(cache_write_tokens > 0)
        group["sum_output_tokens"] += output_tokens

    for group in table.values():
        group["avg_input_tokens"] = round(group["sum_input_tokens"] / group["calls"])
        group["avg_output_tokens"] = round(group["sum_output_tokens"] / group["calls"])

    total_calls = sum(group["calls"] for group in table.values())
    total_input_tokens = sum(group["sum_input_tokens"] for group in table.values())
    total_cache_read_tokens = sum(group["sum_cache_read_tokens"] for group in table.values())
    total_calls_with_cache_read = sum(group["calls_with_cache_read"] for group in table.values())
    extras: TokenMetricsSummaryExtras = {
        "cache_read_hit_rate": total_calls_with_cache_read / total_calls if total_calls else nan,
        "cache_read_utilization_rate": total_cache_read_tokens / total_input_tokens if total_input_tokens else nan,
    }
    return _format_token_metrics_table(table), extras


def _format_token_metrics_table(table: _TokenMetricsTable) -> str:
    """Return an aligned table, sorting string keys alphabetically and None last."""
    if not table:
        return ""

    headers: tuple[str, ...] = ("prompt_cache_key", *_METRIC_COLUMNS)
    rows: list[tuple[str, ...]] = [headers]
    for prompt_cache_key in sorted(table, key=lambda key: (key is None, key or "")):
        group = table[prompt_cache_key]
        label = prompt_cache_key if prompt_cache_key is not None else "(none)"
        rows.append((label, *(str(group[column]) for column in _METRIC_COLUMNS)))

    widths: list[int] = [max(len(row[index]) for row in rows) for index in range(len(headers))]
    return "\n".join("  ".join(value.ljust(widths[index]) if index == 0 else value.rjust(widths[index]) for index, value in enumerate(row)) for row in rows)


"""
Sample output:

TOKENS: (hit=25%, utilization=10%)
prompt_cache_key                      calls  sum_input_tokens  avg_input_tokens  sum_cache_read_tokens  calls_with_cache_read  sum_cache_write_tokens  calls_with_cache_write  sum_output_tokens  avg_output_tokens
podgenai:dedup_subtopic_monologue        36            218113              6059                      0                      0                       0                       0              27644                768
podgenai:generate_subtopic_duologue      20             67205              3360                  30875                     19                    1625                       1              51105               2555
podgenai:generate_subtopic_monologue     20             20777              1039                      0                      0                       0                       0              36233               1812
"""
