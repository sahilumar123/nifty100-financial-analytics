def safe_divide(numerator, denominator):
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


def net_profit_margin(net_profit, sales):
    if sales is None or sales == 0:
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit, sales):
    if sales is None or sales == 0:
        return None
    return operating_profit / sales * 100


def roe(net_profit, equity_capital, reserves):
    equity = (equity_capital or 0) + (reserves or 0)

    if equity <= 0:
        return None

    return net_profit / equity * 100


def roce(ebit, equity_capital, reserves, borrowings):
    capital = (
        (equity_capital or 0)
        + (reserves or 0)
        + (borrowings or 0)
    )

    if capital <= 0:
        return None

    return ebit / capital * 100


def roa(net_profit, total_assets):
    if total_assets is None or total_assets == 0:
        return None

    return net_profit / total_assets * 100


def debt_to_equity(borrowings, equity_capital, reserves):
    borrowings = borrowings or 0
    equity = (equity_capital or 0) + (reserves or 0)

    if borrowings == 0:
        return 0

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(debt_equity, broad_sector):
    if debt_equity is None:
        return False

    if broad_sector == "Financials":
        return False

    return debt_equity > 5


def interest_coverage(operating_profit, other_income, interest):
    if interest is None or interest == 0:
        return None

    return ((operating_profit or 0) + (other_income or 0)) / interest


def icr_label(icr):
    if icr is None:
        return "Debt Free"

    return None


def icr_warning(icr):
    if icr is None:
        return False

    return icr < 1.5


def net_debt(borrowings, investments):
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales, total_assets):
    if total_assets is None or total_assets == 0:
        return None

    return sales / total_assets