def free_cash_flow(operating_activity, investing_activity):
    return (
        (operating_activity or 0)
        + (investing_activity or 0)
    )


def cfo_quality_score(cfo, pat):
    if pat is None or pat == 0:
        return None

    return cfo / pat


def cfo_quality_label(score):
    if score is None:
        return None

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_intensity(investing_activity, sales):
    if sales is None or sales == 0:
        return None

    return abs(investing_activity or 0) / sales * 100


def capex_intensity_label(value):
    if value is None:
        return None

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


def fcf_conversion_rate(fcf, operating_profit):
    if operating_profit is None or operating_profit == 0:
        return None

    return fcf / operating_profit * 100


def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    cfo_sign = "+" if cfo > 0 else "-"
    cfi_sign = "+" if cfi > 0 else "-"
    cff_sign = "+" if cff > 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1:
            return "Shareholder Returns"
        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return "Mixed"