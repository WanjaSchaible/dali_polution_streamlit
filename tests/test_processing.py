import numpy as np
import pandas as pd
import pytest

from koeln_luft import config, data_loader, processing


def _synthetic_air(values: dict[str, list[float]], start: str = "2025-01-06") -> pd.DataFrame:
    n = len(next(iter(values.values())))
    idx = pd.date_range(start, periods=n, freq="h", tz=config.TIMEZONE, name="zeit")
    df = pd.DataFrame(values, index=idx)
    for col in config.POLLUTANTS:
        if col not in df:
            df[col] = np.nan
    df["aqi"] = pd.Categorical(["gut"] * n, categories=config.AQI_LEVELS, ordered=True)
    return data_loader.add_time_features(df)


def test_daily_mean_requires_18_hours():
    values = [10.0] * 24 + [20.0] * 17 + [np.nan] * 7
    air = _synthetic_air({"pm10": values})
    daily = processing.daily_air(air)
    assert daily.loc["2025-01-06", "pm10"] == 10
    assert np.isnan(daily.loc["2025-01-07", "pm10"])
    assert daily.loc["2025-01-07", "n_pm10"] == 17


def test_evaluate_daily_limit_counts_exceedances():
    air = _synthetic_air({"pm10": [60.0] * 24 + [40.0] * 24 + [55.0] * 24})
    daily = processing.daily_air(air)
    limit = config.Limit("pm10", "tag", 50, 1, "Test")
    row = processing.evaluate_limit(limit, air, daily)
    assert row["Überschreitungen"] == 2
    assert not row["Eingehalten"]


def test_evaluate_annual_limit():
    air = _synthetic_air({"no2": [30.0] * 48})
    limit = config.Limit("no2", "jahr", 40, None, "Test")
    row = processing.evaluate_limit(limit, air, processing.daily_air(air))
    assert row["Eingehalten"]
    assert row["Überschreitungen"] is None


def test_exceedances_per_month_has_12_months():
    idx = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    series = pd.Series(0.0, index=idx)
    series["2025-03-05"] = 100
    result = processing.exceedances_per_month(series, 50)
    assert list(result.index) == list(range(1, 13))
    assert result[3] == 1 and result.sum() == 1


def test_missing_runs():
    air = _synthetic_air({"no2": [1.0, np.nan, np.nan, 2.0, np.nan, 3.0]})
    runs = processing.missing_runs(air["no2"])
    assert list(runs["stunden"]) == [2, 1]


def test_linear_fit():
    x = pd.Series([1.0, 2.0, 3.0, 4.0])
    slope, intercept = processing.linear_fit(x, 2 * x + 1)
    assert slope == pytest.approx(2)
    assert intercept == pytest.approx(1)


def test_aqi_distribution_sums_to_100():
    air = data_loader.load_air_quality()
    assert processing.aqi_distribution(air)["anteil"].sum() == pytest.approx(100)
    by_month = processing.aqi_distribution(air, by="monat")
    assert np.allclose(by_month.sum(axis=1), 100)


def test_limit_table_real_data():
    air = data_loader.load_air_quality()
    table = processing.limit_table(air, processing.daily_air(air))
    assert len(table) == len(config.LIMITS)
    eu = table[table["Quelle"] == "EU"]
    assert eu["Eingehalten"].all()
