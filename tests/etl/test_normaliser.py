import pytest
from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Dec 2012", "2012-12"),
        ("Mar 2014", "2014-03"),
        ("Mar-15", "2015-03"),
        ("Mar-20", "2020-03"),
        ("2021", "2021-03"),
        (2022, "2022-03"),
        ("FY 2023", "2023-03"),
        ("2024-25", "2024-03"),
        ("Mar/2018", "2018-03"),
        ("June 2019", None),
        ("Dec-2016", "2016-12"),
        ("FY2020", "2020-03"),
        ("2017", "2017-03"),
        (" 2022 ", "2022-03"),
        ("Mar 2023", "2023-03"),
        ("Dec 2024", "2024-12"),
        ("Sep 2021", "2021-09"),
        ("Jan 2020", "2020-01"),
        (None, None),
        ("", None),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected