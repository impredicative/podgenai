"""Aggregate and format token usage and request durations."""

from collections.abc import Iterable
from math import nan, sqrt
from typing import NamedTuple

from podgenai.types import TokenMetric, TokenMetricsSummaryExtras
from podgenai.util.math import WeightedValue, weighted_mean, weighted_median

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
    "avg_output_speed",
    "med_output_speed",
    "sum_reasoning_tokens",
    "calls_missing_reasoning_tokens",
    "avg_reasoning_tokens",
)

type _TokenMetricsRow = dict[str, int | float]
type _TokenMetricsTable = dict[str | None, _TokenMetricsRow]


class _WeightedOutputSpeed(NamedTuple):
    """One record's speed in tokens per second and weight."""

    speed: float
    weight: float


class _OutputSpeedSummary(NamedTuple):
    """Weighted mean and weighted median output speeds in tokens per second."""

    avg_output_speed: float
    med_output_speed: float


def summarize_token_metrics(records: Iterable[TokenMetric]) -> tuple[str, TokenMetricsSummaryExtras]:
    """Return (table, extras) with usage, duration, and output speed by cache key and overall metrics.

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

    Output speeds use only records with positive output counts and durations.
    For output length L and duration D = duration_ds / 10 in seconds, each
    speed L / D is weighted by sqrt(L * D). The weighted arithmetic mean and
    midpoint weighted median are calculated by cache key and over all eligible
    records. Table speeds are rounded to integers, with ties rounded to the
    nearest even integer; extras retain unrounded floats. Speeds are NaN when
    no records qualify.

    An empty iterable produces an empty table and NaN rates and speeds.

    Reasoning token counts are already included in output token counts.

    Durations are always available and their average includes every recorded call.
    Duration sums use the recorded integer deciseconds (ds). Duration averages
    are rounded to integers, with ties rounded to the nearest even integer.
    Sums accumulate request time and can exceed the overall elapsed time when
    requests run concurrently.
    """
    table: _TokenMetricsTable = {}
    output_speeds_by_key: dict[str | None, list[_WeightedOutputSpeed]] = {}
    output_speeds: list[_WeightedOutputSpeed] = []
    utilization_input_tokens: int = 0
    utilization_cache_read_tokens: int = 0
    for record in records:
        prompt_cache_key = record["prompt_cache_key"]
        if prompt_cache_key not in table:
            table[prompt_cache_key] = dict.fromkeys(_METRIC_COLUMNS, 0)
            output_speeds_by_key[prompt_cache_key] = []
        group = table[prompt_cache_key]
        input_tokens = record["input_tokens"] or 0
        cache_read_tokens = record["cache_read_tokens"] or 0
        cache_write_tokens = record["cache_write_tokens"] or 0
        output_tokens = record["output_tokens"] or 0
        reasoning_tokens = record["reasoning_tokens"] or 0

        if output_tokens > 0 and record["duration_ds"] > 0:
            duration_seconds: float = record["duration_ds"] / 10
            weighted_speed: _WeightedOutputSpeed = _WeightedOutputSpeed(speed=output_tokens / duration_seconds, weight=sqrt(output_tokens * duration_seconds))
            output_speeds_by_key[prompt_cache_key].append(weighted_speed)
            output_speeds.append(weighted_speed)

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

    for prompt_cache_key, group in table.items():
        group["avg_duration_ds"] = round(group["sum_duration_ds"] / group["calls"])
        for metric in ("input_tokens", "output_tokens", "reasoning_tokens"):
            available_calls: int | float = group["calls"] - group[f"calls_missing_{metric}"]
            group[f"avg_{metric}"] = round(group[f"sum_{metric}"] / available_calls) if available_calls else nan

        group_output_speeds: _OutputSpeedSummary = _summarize_output_speeds(output_speeds_by_key[prompt_cache_key])
        group["avg_output_speed"] = round(group_output_speeds.avg_output_speed) if output_speeds_by_key[prompt_cache_key] else nan
        group["med_output_speed"] = round(group_output_speeds.med_output_speed) if output_speeds_by_key[prompt_cache_key] else nan

    total_calls_with_available_cache_read: int | float = sum(group["calls"] - group["calls_missing_cache_read_tokens"] for group in table.values())
    total_calls_with_cache_read: int | float = sum(group["calls_with_cache_read"] for group in table.values())
    overall_output_speeds: _OutputSpeedSummary = _summarize_output_speeds(output_speeds)
    extras: TokenMetricsSummaryExtras = {
        "cache_read_hit_rate": total_calls_with_cache_read / total_calls_with_available_cache_read if total_calls_with_available_cache_read else nan,
        "cache_read_utilization_rate": utilization_cache_read_tokens / utilization_input_tokens if utilization_input_tokens else nan,
        "avg_output_speed": overall_output_speeds.avg_output_speed,
        "med_output_speed": overall_output_speeds.med_output_speed,
    }
    return _format_token_metrics_table(table), extras


def _summarize_output_speeds(weighted_speeds: list[_WeightedOutputSpeed]) -> _OutputSpeedSummary:
    """Return the weighted mean and midpoint weighted median of speeds with positive weights.

    An empty list produces NaN for both statistics.
    """
    weighted_values: list[WeightedValue] = [WeightedValue(value=sample.speed, weight=sample.weight) for sample in weighted_speeds]
    return _OutputSpeedSummary(
        avg_output_speed=weighted_mean(weighted_values),
        med_output_speed=weighted_median(weighted_values),
    )


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

TOKENS: (hit=96%, utilization=67%, avg_speed=43, med_speed=45)
prompt_cache_key                                    calls  sum_duration_ds  avg_duration_ds  sum_input_tokens  avg_input_tokens  sum_cache_read_tokens  calls_with_cache_read  sum_cache_write_tokens  calls_with_cache_write  sum_output_tokens  avg_output_tokens  avg_output_speed  med_output_speed  sum_reasoning_tokens  avg_reasoning_tokens
podgenai:list_subtopics:from_document                   1              174              174             12437             12437                      0                      0                       0                       0                613                613                35                35                    75                    75
podgenai:select_voice                                   1               19               19               117               117                      0                      0                       0                       0                 10                 10                 5                 5                     0                     0
podgenai:generate_subtopic_monologue:from_document     43            17801              414            563228             13098                 522520                     40                   39189                       3              46883               1090                26                26                     0                     0
podgenai:dedup_subtopic_monologue                      82             6740               82            350622              4276                 100764                     81                    1244                       1              38244                466                61                68                  2960                    36
podgenai:generate_subtopic_duologue                    43            14372              334            124261              2890                  77910                     42                    1855                       1              68827               1601                48                48                     0                     0
"""
