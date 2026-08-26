from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    roe,
    debt_to_equity,
    interest_coverage,
    high_leverage_flag,
)


def test_npm():
    assert net_profit_margin(20, 100) == 20


def test_npm_zero_sales():
    assert net_profit_margin(20, 0) is None


def test_opm():
    assert operating_profit_margin(30, 100) == 30


def test_opm_zero_sales():
    assert operating_profit_margin(30, 0) is None


def test_roe():
    assert roe(20, 50, 50) == 20


def test_roe_negative_equity():
    assert roe(20, -100, 20) is None


def test_debt_free():
    assert debt_to_equity(0, 100, 50) == 0


def test_debt_equity():
    assert debt_to_equity(50, 100, 100) == 0.25


def test_icr():
    assert interest_coverage(100, 20, 10) == 12


def test_icr_zero_interest():
    assert interest_coverage(100, 20, 0) is None


def test_high_leverage():
    assert high_leverage_flag(6, "Industrials") is True


def test_financials_leverage():
    assert high_leverage_flag(6, "Financials") is False