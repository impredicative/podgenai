# Background

The `src/podgenai/podgenai.py` file prints token usage metrics via the following code within it:
```python
token_metrics_summary_table, token_metrics_summary_extras = summarize_token_metrics(token_metrics_collector.records())
if not token_metrics_summary_table:
    print("\nTOKENS: (none)\n")
else:
    print(f"\nTOKENS: (hit={token_metrics_summary_extras['cache_read_hit_rate']:.0%}, utilization={token_metrics_summary_extras['cache_read_utilization_rate']:.0%})\n{token_metrics_summary_table}\n")
```

The implementation of the `summarize_token_metrics` function and an example of the printed output are contained in `src/podgenai/metrics.py`.

Currently, the printed metrics include `sum_duration_ds` and `sum_output_tokens`, but the output token speed (in tokens per second) is not computed or printed.

# Task

The high-level task is to compute and print the output token speed (in tokens per second). Both the mean and median are to be reported as explained below. The task involves adding the new columns named `avg_output_speed` and `med_output_speed` (in tokens per second) to the printed `token_metrics_summary_table` table, reflecting the mean and median output token speeds. It also involves including the overall output token speed in `token_metrics_summary_extras` via the new keys `avg_output_speed` and `med_output_speed`, reflecting the mean and median output token speeds, respectively.

Below are thoughts, organized by file, reflecting a partial understanding of what this work will entail.

## src/podgenai/util/openai.py
Metrics is recorded as an instance of `TokenMetric` in the `get_completion` function. No change presumably needs to be made to this file since the token speed is a derived metric. Note that `output_tokens` is permitted to be missing (as `None`), whereas the time used (`duration_ds` (in deciseconds)) is always present.

## src/podgenai/types.py
The `TokenMetricsSummaryExtras` class is to be updated to add output speed attributes for the overall output token speed, specifically `avg_output_speed` and `med_output_speed`, reflecting the mean and median output token speeds, respectively.

## src/podgenai/podgenai.py
3. In `src/podgenai/podgenai.py`, the printed output is to be updated to include the output token speed column in the table (implicitly) and in the overall summary (explicitly).

## src/podgenai/metrics.py
This file will contain the bulk of the work.

For each aggregate row, i.e. for each unique value of `prompt_cache_key`, the output speed can perhaps be computed by using the weighted average of the output speeds of the group's records. A record's weight would be its value of `output_tokens`. This should be done only for records where `output_tokens` is not `None`, disregarding records where `output_tokens` is `None`.

The cumulative output speed is conceptually computed similarly over all records that have a non-missing value of `output_tokens` using the weighted average approach.

### Aggregate End-to-End LLM Output Speed

For each completed record, let:

- `L` = output length in tokens
- `D` = end-to-end duration
- `S = L / D` = end-to-end output speed
- `W = sqrt(L * D)` = record weight

Across all eligible records, compute and report:

1. **Weighted mean speed** — the weighted arithmetic mean of `S`, using `W` as the weight:

   `sum(W * S) / sum(W)`

2. **Weighted median speed** — the weighted median of `S`, using the same `W`.

The `sqrt(L * D)` weighting deliberately gives greater influence to records with larger outputs and/or longer durations while scaling that influence sublinearly.

The weighted mean captures overall weighted performance and remains sensitive to unusually fast or slow records. The weighted median represents typical weighted performance and is more robust to extremes. A weighted mean materially below the weighted median indicates a slow-performance tail; the reverse indicates a fast-performance tail.

Use a consistent duration unit across records. Changing that unit uniformly does not affect relative weights or which record constitutes the weighted median; reported speed should be expressed in the corresponding token/time unit.

Exclude records for which `L <= 0`, `D <= 0`, or either value is missing or non-finite.