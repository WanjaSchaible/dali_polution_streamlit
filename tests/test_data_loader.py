import pandas as pd
import pytest

from koeln_luft import config, data_loader


@pytest.fixture(scope="module")
def air() -> pd.DataFrame:
    return data_loader.load_air_quality()


@pytest.fixture(scope="module")
def weather() -> pd.DataFrame:
    return data_loader.load_weather()


def test_air_columns_and_types(air):
    for col in config.POLLUTANTS:
        assert air[col].dtype == "float64"
    assert list(air["aqi"].cat.categories) == config.AQI_LEVELS
    assert air["aqi"].cat.ordered
    assert {"o3", "so2"}.isdisjoint(air.columns)
    assert air.attrs["leere_spalten"] == ["o3", "so2"]


def test_air_time_index_is_continuous(air):
    assert air.index.tz is not None
    assert air.index.is_unique
    assert air.index.is_monotonic_increasing
    # Ein Jahr hat 8760 Stunden; die Stunde 31.12.2024 23-24 Uhr wird ausgefiltert.
    assert len(air) == 8759
    gaps = air.index.tz_convert("UTC").to_series().diff().dropna()
    assert (gaps == pd.Timedelta(hours=1)).all()


def test_dst_switch_handled(air):
    oct_day = air[air["datum"] == pd.Timestamp("2025-10-26")]
    mar_day = air[air["datum"] == pd.Timestamp("2025-03-30")]
    assert len(oct_day) == 25
    assert len(mar_day) == 23


def test_german_date_row_parsed(air):
    ts = pd.Timestamp("2025-01-10 03:00", tz=config.TIMEZONE)
    assert air.loc[ts, "pm10"] == 13


def test_new_year_spike(air):
    first = air.iloc[0]
    assert first.name == pd.Timestamp("2025-01-01 00:00", tz=config.TIMEZONE)
    assert first["pm10"] == 214


def test_weather(weather):
    assert len(weather) == 365
    assert {"snow", "wdir", "wpgt", "tsun"}.isdisjoint(weather.columns)
    assert set(config.WEATHER_COLUMNS) <= set(weather.columns)
    assert weather.isna().all(axis=1).sum() == 7


def test_rename_raises_on_missing_columns():
    with pytest.raises(ValueError):
        data_loader._rename_air_columns(pd.Index(["Stationscode", "Datum"]))
