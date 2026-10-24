import pandas as pd

from vogelring_analytics.maps import _merged_date, _merged_value


def test_merged_value_single_and_many():
    assert _merged_value(pd.Series(["E1", "E1", None])) == "E1"
    assert _merged_value(pd.Series(["E1", "E2", "E3"])) == "E1, E2, E3"
    assert _merged_value(pd.Series(["E1", "E2", "E3", "E4", "E5", "E6"])) == "E1, E2, … (6 verschiedene)"
    assert _merged_value(pd.Series([None, None])) is None


def test_merged_date_range():
    assert _merged_date(pd.Series(["2026-05-06", "2026-05-06"])) == "2026-05-06"
    assert _merged_date(pd.Series(["2026-05-06", "2025-01-02", "2026-03-01"])) == "02.01.2025 – 06.05.2026"
    assert _merged_date(pd.Series(pd.to_datetime(["2026-05-06", "2026-05-07"]))) == "06.05.2026 – 07.05.2026"
