"""Aggregate and format token usage and request durations."""

from collections.abc import Iterable
from math import nan

from podgenai.types import TokenMetric, TokenMetricsSummaryExtras

_METRIC_COLUMNS: tuple[str, ...] = (
    "calls",
    "sum_duration_ds",
    "avg_duration_ds",
    "sum_input_tokens",
    "calls_missing_input_tokens",
    "avg_input_tokens",
    "sum_cache_read_tokens",
    "calls_missing_cache_read_tokens",
    "calls_with_cache_read",
    "sum_cache_write_tokens",
    "calls_missing_cache_write_tokens",
    "calls_with_cache_write",
    "sum_output_tokens",
    "calls_missing_output_tokens",
    "avg_output_tokens",
    "sum_reasoning_tokens",
    "calls_missing_reasoning_tokens",
    "avg_reasoning_tokens",
)

type _TokenMetricsRow = dict[str, int | float]
type _TokenMetricsTable = dict[str | None, _TokenMetricsRow]


def summarize_token_metrics(records: Iterable[TokenMetric]) -> tuple[str, TokenMetricsSummaryExtras]:
    """Return (table, extras) with usage and duration by cache key and overall cache rates.

    None is a distinct cache key. Missing counts contribute zero to sums, and
    every record contributes to the call count. Each token average includes only
    available counts for that metric, including reported zeros, and is NaN
    if all counts are missing. Available averages are rounded to integers,
    with ties rounded to the nearest even integer.

    Each calls_missing_* column counts records where that token count is None;
    a reported zero is available. A None cache key is not an unavailable count.

    Rates use totals across all groups. Cache hit rate includes only calls with
    an available cache-read count. Cache utilization is the ratio of summed
    cache-read tokens to summed input tokens, using only calls where both counts
    are available. Reported zeros are included. Rates are NaN for zero denominators.

    An empty iterable produces an empty table and NaN rates.

    Reasoning token counts are already included in output token counts.

    Durations are always available and their average includes every recorded call.
    Duration sums use the recorded integer deciseconds (ds). Duration averages
    are rounded to integers, with ties rounded to the nearest even integer.
    Sums accumulate request time and can exceed the overall elapsed time when
    requests run concurrently.
    """
    table: _TokenMetricsTable = {}
    utilization_input_tokens: int = 0
    utilization_cache_read_tokens: int = 0
    for record in records:
        prompt_cache_key = record["prompt_cache_key"]
        if prompt_cache_key not in table:
            table[prompt_cache_key] = dict.fromkeys(_METRIC_COLUMNS, 0)
        group = table[prompt_cache_key]
        input_tokens = record["input_tokens"] or 0
        cache_read_tokens = record["cache_read_tokens"] or 0
        cache_write_tokens = record["cache_write_tokens"] or 0
        output_tokens = record["output_tokens"] or 0
        reasoning_tokens = record["reasoning_tokens"] or 0

        if record["input_tokens"] is not None and record["cache_read_tokens"] is not None:
            utilization_input_tokens += input_tokens
            utilization_cache_read_tokens += cache_read_tokens

        group["calls"] += 1
        group["sum_duration_ds"] += record["duration_ds"]
        group["calls_missing_input_tokens"] += int(record["input_tokens"] is None)
        group["calls_missing_cache_read_tokens"] += int(record["cache_read_tokens"] is None)
        group["calls_missing_cache_write_tokens"] += int(record["cache_write_tokens"] is None)
        group["calls_missing_output_tokens"] += int(record["output_tokens"] is None)
        group["calls_missing_reasoning_tokens"] += int(record["reasoning_tokens"] is None)
        group["sum_input_tokens"] += input_tokens
        group["sum_cache_read_tokens"] += cache_read_tokens
        group["calls_with_cache_read"] += int(cache_read_tokens > 0)
        group["sum_cache_write_tokens"] += cache_write_tokens
        group["calls_with_cache_write"] += int(cache_write_tokens > 0)
        group["sum_output_tokens"] += output_tokens
        group["sum_reasoning_tokens"] += reasoning_tokens

    for group in table.values():
        group["avg_duration_ds"] = round(group["sum_duration_ds"] / group["calls"])
        for metric in ("input_tokens", "output_tokens", "reasoning_tokens"):
            available_calls: int | float = group["calls"] - group[f"calls_missing_{metric}"]
            group[f"avg_{metric}"] = round(group[f"sum_{metric}"] / available_calls) if available_calls else nan

    total_calls_with_available_cache_read: int | float = sum(group["calls"] - group["calls_missing_cache_read_tokens"] for group in table.values())
    total_calls_with_cache_read: int | float = sum(group["calls_with_cache_read"] for group in table.values())
    extras: TokenMetricsSummaryExtras = {
        "cache_read_hit_rate": total_calls_with_cache_read / total_calls_with_available_cache_read if total_calls_with_available_cache_read else nan,
        "cache_read_utilization_rate": utilization_cache_read_tokens / utilization_input_tokens if utilization_input_tokens else nan,
    }
    return _format_token_metrics_table(table), extras


def _format_token_metrics_table(table: _TokenMetricsTable, *, skip_calls_missing_columns_if_all_zero: bool = True) -> str:
    """Return an aligned table string.

    Preserve first-seen order for string keys and place None last.

    Params:
    * `skip_calls_missing_columns_if_all_zero`: If true, omit calls_missing_* columns if all values of the column are zeros. Default is true.
    """
    if not table:
        return ""

    columns: tuple[str, ...] = tuple(column for column in _METRIC_COLUMNS if not skip_calls_missing_columns_if_all_zero or not column.startswith("calls_missing_") or any(group[column] != 0 for group in table.values()))
    headers: tuple[str, ...] = ("prompt_cache_key", *columns)
    rows: list[tuple[str, ...]] = [headers]
    for prompt_cache_key in sorted(table, key=lambda key: key is None):
        group = table[prompt_cache_key]
        label = prompt_cache_key if prompt_cache_key is not None else "(none)"
        rows.append((label, *(str(group[column]) for column in columns)))

    widths: list[int] = [max(len(row[index]) for row in rows) for index in range(len(headers))]
    return "\n".join("  ".join(value.ljust(widths[index]) if index == 0 else value.rjust(widths[index]) for index, value in enumerate(row)) for row in rows)


"""
Sample output:

TOKENS: (hit=96%, utilization=30%)
prompt_cache_key                      calls  sum_duration_ds  avg_duration_ds  sum_input_tokens  avg_input_tokens  sum_cache_read_tokens  calls_with_cache_read  sum_cache_write_tokens  calls_with_cache_write  sum_output_tokens  avg_output_tokens  sum_reasoning_tokens  avg_reasoning_tokens
podgenai:select_voice                     1               20               20               136               136                      0                      0                       0                       0                 10                 10                     0                     0
podgenai:list_subtopics                   1               87               87               624               624                      0                      0                       0                       0                398                398                     0                     0
podgenai:generate_subtopic_monologue     34            14781              435             38510              1133                  36366                     33                    1102                       1              61566               1811                  1204                    35
podgenai:dedup_subtopic_monologue        59             6344              108            364848              6184                  64148                     58                    1106                       1              43400                736                  2549                    43
podgenai:generate_subtopic_duologue      34            15563              458            117108              3444                  56661                     33                    1717                       1              86167               2534                   241                     7
"""
