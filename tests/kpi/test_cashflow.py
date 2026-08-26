from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


def test_fcf():
    assert free_cash_flow(100, -40) == 60


def test_negative_fcf():
    assert free_cash_flow(20, -50) == -30


def test_cfo_quality():
    assert cfo_quality_score(120, 100) == 1.2


def test_cfo_quality_zero_pat():
    assert cfo_quality_score(100, 0) is None


def test_high_quality_label():
    assert cfo_quality_label(1.2) == "High Quality"


def test_moderate_quality_label():
    assert cfo_quality_label(0.7) == "Moderate"


def test_accrual_risk_label():
    assert cfo_quality_label(0.3) == "Accrual Risk"


def test_capex_intensity():
    assert capex_intensity(-5, 100) == 5


def test_capex_asset_light():
    assert capex_intensity_label(2) == "Asset Light"


def test_capex_capital_intensive():
    assert capex_intensity_label(10) == "Capital Intensive"


def test_fcf_conversion():
    assert fcf_conversion_rate(50, 100) == 50


def test_fcf_zero_operating_profit():
    assert fcf_conversion_rate(50, 0) is None


def test_reinvestor():
    assert capital_allocation_pattern(
        100, -50, -20, 0.8
    ) == "Reinvestor"


def test_shareholder_returns():
    assert capital_allocation_pattern(
        150, -50, -20, 1.5
    ) == "Shareholder Returns"


def test_liquidating_assets():
    assert capital_allocation_pattern(
        100, 50, -20
    ) == "Liquidating Assets"


def test_distress_signal():
    assert capital_allocation_pattern(
        -100, 50, 20
    ) == "Distress Signal"


def test_growth_funded_by_debt():
    assert capital_allocation_pattern(
        -100, -50, 50
    ) == "Growth Funded by Debt"


def test_cash_accumulator():
    assert capital_allocation_pattern(
        100, 50, 20
    ) == "Cash Accumulator"


def test_pre_revenue():
    assert capital_allocation_pattern(
        -100, -50, -20
    ) == "Pre-Revenue"


def test_mixed():
    assert capital_allocation_pattern(
        100, -50, 50
    ) == "Mixed"