"""Einlesen und Bereinigen der Rohdaten.

Besonderheiten der Luftqualitätsdatei:
- Semikolon als Trennzeichen, UTF-8 mit BOM, Sonderzeichen in den Spaltennamen.
- Zeitstempel sind Stunden-*Ende* in deutscher Ortszeit. Das zeigt die Zeitumstellung:
  am 30.03. fehlt 03:00, am 26.10. kommt 03:00 doppelt vor. Wir rechnen daher auf
  den Stunden-*Beginn* um und hängen die Zeitzone an. Der erste Wert (01.01. 00:00)
  beschreibt so die Stunde 31.12.2024 23-24 Uhr und fällt aus dem Auswertungsjahr.
- Einzelne Zeitstempel liegen im deutschen Format vor (TT.MM.JJJJ HH:MM).
- Ozon und Schwefeldioxid sind vollständig leer und werden entfernt.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from koeln_luft import config


def _rename_air_columns(columns: pd.Index) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for col in columns:
        for keyword, short in config.AIR_COLUMN_KEYWORDS.items():
            if keyword in col:
                mapping[col] = short
                break
    missing = set(config.AIR_COLUMN_KEYWORDS.values()) - set(mapping.values())
    if missing:
        raise ValueError(f"Spalten nicht gefunden: {sorted(missing)}")
    return mapping


def _hour_end_to_start(labels: pd.Series) -> pd.DatetimeIndex:
    """Wandelt lokale Stunden-Ende-Zeitstempel in zeitzonenbewusste Stunden-Anfänge um."""
    iso = pd.to_datetime(labels, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    # Einzelne Zeilen liegen im deutschen Format vor (z. B. "10.01.2025 04:00").
    german = pd.to_datetime(labels, format="%d.%m.%Y %H:%M", errors="coerce")
    parsed = iso.fillna(german)
    if parsed.isna().any():
        bad = labels[parsed.isna()].tolist()[:5]
        raise ValueError(f"Unbekanntes Datumsformat: {bad}")
    start = parsed - pd.Timedelta(hours=1)
    return pd.DatetimeIndex(start).tz_localize(
        config.TIMEZONE, ambiguous="infer", nonexistent="raise"
    )


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    return df.assign(
        datum=idx.tz_localize(None).normalize(),
        stunde=idx.hour,
        wochentag=idx.day_of_week,
        monat=idx.month,
        wochenende=idx.day_of_week >= 5,
    )


def load_air_quality(path: Path = config.AIR_FILE, year: int | None = config.YEAR) -> pd.DataFrame:
    """Lädt die stündlichen Luftqualitätsdaten.

    Rückgabe: DataFrame mit Index ``zeit`` (Stundenbeginn, Europe/Berlin) und den
    Spalten ``station``, ``pm10``, ``pm25``, ``no2``, ``aqi`` (geordnete Kategorie)
    sowie Zeitmerkmalen (``datum``, ``stunde``, ``wochentag``, ``monat``, ``wochenende``).
    """
    raw = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df = raw.rename(columns=_rename_air_columns(raw.columns))

    df.index = _hour_end_to_start(df.pop("datum"))
    df.index.name = "zeit"

    empty = [c for c in df.columns if df[c].isna().all()]
    df = df.drop(columns=empty)
    df.attrs["leere_spalten"] = empty

    for col in config.POLLUTANTS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["aqi"] = pd.Categorical(df["aqi"], categories=config.AQI_LEVELS, ordered=True)

    if year is not None:
        attrs = df.attrs
        df = df[df.index.year == year].copy()
        df.attrs = attrs

    return add_time_features(df)


def load_weather(path: Path = config.WEATHER_FILE) -> pd.DataFrame:
    """Lädt die täglichen Wetterdaten. Index ``datum`` (naiv, Tagesbeginn)."""
    df = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["date"])
    df = df.rename(columns={"date": "datum"}).set_index("datum").sort_index()
    empty = [c for c in df.columns if df[c].isna().all()]
    df = df.drop(columns=empty)
    df.attrs["leere_spalten"] = empty
    return df
