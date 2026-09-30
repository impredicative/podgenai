# Background

The current `podgenai` package makes very light use of Pandas. The intent is to replace this use with native Python logic, and remove the Pandas dependency entirely.

# Task

Your task is to replace the use of Pandas with native Python logic, ensuring that the existing functionality is approximately preserved. At minimum, these subtasks apply:

1. Pandas is used in `src/podgenai/util/contextvars.py` in the `RecordCollector.to_dataframe`. I believe this method can be removed. Usage of the `RecordCollector` can then fallback to its `records` method.

2. The corresponding dataframe as above is used in `src/podgenai/podgenai.py` in the following code:

```python
df_token_metrics = token_metrics_collector.to_dataframe()
if df_token_metrics.empty:
    print("\nTOKENS: (none)\n")
else:
    df_token_metrics_agg = df_token_metrics.groupby("prompt_cache_key", dropna=False).agg(
        calls=("prompt_cache_key", "size"),
        sum_input_tokens=("input_tokens", "sum"),
        avg_input_tokens=("input_tokens", "mean"),
        sum_cache_read_tokens=("cache_read_tokens", "sum"),
        calls_with_cache_read=("cache_read_tokens", lambda token_counts: (token_counts > 0).sum()),
        sum_cache_write_tokens=("cache_write_tokens", "sum"),
        calls_with_cache_write=("cache_write_tokens", lambda token_counts: (token_counts > 0).sum()),
        sum_output_tokens=("output_tokens", "sum"),
        avg_output_tokens=("output_tokens", "mean"),
    )
    for token_column in ("input_tokens", "output_tokens"):
        avg_column = f"avg_{token_column}"
        df_token_metrics_agg[avg_column] = df_token_metrics_agg[avg_column].round().astype(df_token_metrics[token_column].dtype)
    cache_read_hit_rate = df_token_metrics_agg["calls_with_cache_read"].sum() / df_token_metrics_agg["calls"].sum()
    cache_read_utilization_rate = df_token_metrics_agg["sum_cache_read_tokens"].sum() / df_token_metrics_agg["sum_input_tokens"].sum()
    print(f"\nTOKENS: (hit={cache_read_hit_rate:.0%}, utilization={cache_read_utilization_rate:.0%})\n{df_token_metrics_agg.to_string()}\n")
```

This is the logic that would need to be replaced with native Python logic, using `token_metrics_collector.records()`instead. A table with the aggregated token metrics would need to be constructed manually using Python data structures and operations. Perhaps the required logic can be implemented in a new module `src/podgenai/metrics.py`. Thereafter, `src/podgenai/podgenai.py` would then be responsible only for printing the computed metrics and rates.

For your reference, a sample printed result using Pandas was:
```
TOKENS (hit=98%, utilization=38%):
                                      calls  sum_input_tokens  avg_input_tokens  sum_cache_read_tokens  calls_with_cache_read  sum_cache_write_tokens  calls_with_cache_write  sum_output_tokens  avg_output_tokens
prompt_cache_key                                                                                                                                                                                                   
podgenai:dedup_subtopic_monologue        95            445335              4688                 116250                     93                    2500                       2              96483               1016
podgenai:generate_subtopic_duologue      36            109081              3030                  65135                     35                    1861                       1              61566               1710
podgenai:generate_subtopic_monologue     36             45896              1275                  44030                     35                    1258                       1              43901               1219
```
The replacement output doesn't have to look exactly like this, but close to it. Ensure correctness.

As for the data type of what a record is in this context, refer to the `TokenMetric` class in `src/podgenai/types.py`. If you need to define any data types that are used in more than one module, `src/podgenai/types.py` should be the appropriate place to define them.

3. Update `pyproject.toml` to remove Pandas. Regenerate `uv.lock`.

# Considerations

## Handling None values

The optionally `None` values of the attributes in the `TokenMetric` records must be handled appropriately when performing aggregations and calculations.

With regard to `prompt_cache_key`, a `None` value should be treated as a distinct key when aggregating token metrics.

With regard to the numerical attributes of `TokenMetric`, for simplicity, `None` values may make sense to treat as zero when performing aggregations and calculations.

For divisions, if a denominator is zero, the result can be `nan`, not zero.