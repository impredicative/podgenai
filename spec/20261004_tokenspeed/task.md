# Background

The `src/podgenai/podgenai.py` file prints token usage metrics.

The implementation of the `summarize_token_metrics` function and an example of the printed output are contained in `src/podgenai/metrics.py`.

Currently, the printed metrics include `sum_duration_ds` and `sum_output_tokens`, but the output token speed (in tokens per second) is not computed or printed.

# Task

The high-level task is to compute and print the output token speed (in tokens per second). Both the mean and median are to be calculated and reported as explained below. The task involves calculating and adding the new columns named `avg_output_speed` and `med_output_speed` (in tokens per second) to the printed `token_metrics_summary_table` table, reflecting the mean and median output token speeds. It also involves calculating and provisioning the overall output token speed in `token_metrics_summary_extras` via the new keys `avg_output_speed` and `med_output_speed`, reflecting the mean and median output token speeds, respectively.

Below are thoughts, organized by file, reflecting a partial understanding of what this work will entail.

## src/podgenai/util/openai.py
Metrics are recorded as an instance of `TokenMetric` in the `get_completion` function. No change presumably needs to be made to this file since the token speed is a derived metric. Note that `output_tokens` is permitted to be missing (as `None`), whereas the time used (`duration_ds` in deciseconds) is always present.

## src/podgenai/types.py
The `TokenMetricsSummaryExtras` class is to be updated to add output speed attributes for the overall output token speed, specifically `avg_output_speed` and `med_output_speed`, reflecting the mean and median output token speeds, respectively.

## src/podgenai/podgenai.py
The printed output is to be updated to include the output token speed. This is the portion that is to be updated:

```python
token_metrics_summary_table, token_metrics_summary_extras = summarize_token_metrics(token_metrics_collector.records())
if not token_metrics_summary_table:
    print("\nTOKENS: (none)\n")
else:
    print(f"\nTOKENS: (hit={token_metrics_summary_extras['cache_read_hit_rate']:.0%}, utilization={token_metrics_summary_extras['cache_read_utilization_rate']:.0%})\n{token_metrics_summary_table}\n")
```
In the above code, `token_metrics_summary_table` will automatically include the output token speed column when it is computed in `src/podgenai/metrics.py`.

As for `token_metrics_summary_extras`, its new attributes `avg_output_speed` and `med_output_speed` are to be printed as in the line:

    TOKENS: (hit=96%, utilization=30%, avg_speed=42, med_speed=44)

## src/podgenai/metrics.py
This file will contain the bulk of the work.

For computing the output token speed, use only the rows where `output_tokens` is not `None`. For each aggregate row, i.e. for each unique value of `prompt_cache_key`, the token output speed can be computed by using the weighted averages of the output speeds of the group's records. For each group, use the following approach:

For each non-missing record, let:
- `L` = output length in tokens
- `D` = end-to-end duration in seconds (not in deciseconds!)
- `S = L / D` = end-to-end output speed
- `W = sqrt(L * D)` = record's weight
Ensure `L > 0` and `D > 0` before including a record in the calculations.

For each group, compute and report:
1. **Weighted mean speed** — the weighted arithmetic mean of `S`, using `W` as the weight: `sum(W * S) / sum(W)`
2. **Weighted median speed** — the weighted median (midpoint) of `S`, using the same weight `W`: (*calculation not specified here*)

For your information, the `sqrt(L * D)` weighting deliberately gives greater influence to records with larger outputs and/or longer durations while scaling that influence sublinearly. The weighted mean captures overall weighted performance and remains sensitive to unusually fast or slow records. The weighted median represents typical weighted performance and is more robust to extremes. A weighted mean materially below the weighted median indicates a slow-performance tail; the reverse indicates a fast-performance tail.

As for the calculated `TokenMetricsSummaryExtras`, it should similarly include the new attributes `avg_output_speed` and `med_output_speed` calculated over all applicable records.

Be sure to update the sample output at the bottom of the file with reasonable values.