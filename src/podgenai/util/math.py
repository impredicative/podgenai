from collections.abc import Iterable
from math import fsum, isclose, nan
from typing import NamedTuple


class WeightedValue(NamedTuple):
    """A numeric value and its positive statistical weight."""

    value: float
    weight: float


def weighted_mean(weighted_values: Iterable[WeightedValue]) -> float:
    """Return the weighted arithmetic mean of values with positive weights.

    Consume the iterable once and calculate sum(weight * value) / sum(weight).
    Empty input produces NaN.
    """
    samples: list[WeightedValue] = list(weighted_values)
    if not samples:
        return nan

    total_weight: float = fsum(sample.weight for sample in samples)
    return fsum(sample.value * sample.weight for sample in samples) / total_weight


def weighted_median(weighted_values: Iterable[WeightedValue]) -> float:
    """Return the midpoint weighted median of values with positive weights.

    Consume the iterable once and sort by value. Select the value crossing
    half the total weight. If cumulative weight reaches exactly half, return
    the arithmetic midpoint of that value and the next value. Boundary
    comparisons use a relative tolerance of 1e-12. Empty input produces NaN.
    """
    sorted_values: list[WeightedValue] = sorted(weighted_values, key=lambda sample: sample.value)
    if not sorted_values:
        return nan

    half_weight: float = fsum(sample.weight for sample in sorted_values) / 2
    cumulative_weight: float = 0.0
    for index, sample in enumerate(sorted_values):
        cumulative_weight += sample.weight
        if isclose(cumulative_weight, half_weight, rel_tol=1e-12):
            return (sample.value + sorted_values[index + 1].value) / 2
        if cumulative_weight > half_weight:
            return sample.value

    return sorted_values[-1].value
