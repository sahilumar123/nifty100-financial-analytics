import math


def calculate_cagr(start, end, years):
    if years <= 0:
        return None, "INVALID_YEARS"

    if start is None or end is None:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start > 0 and end > 0:
        value = ((end / start) ** (1 / years) - 1) * 100
        return value, None

    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"

    if start < 0 and end > 0:
        return None, "TURNAROUND"

    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"


def get_cagr_value(values, years):
    if len(values) < years + 1:
        return None, "INSUFFICIENT"

    start = values.iloc[-(years + 1)]
    end = values.iloc[-1]

    return calculate_cagr(start, end, years)