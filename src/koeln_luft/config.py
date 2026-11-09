"""Zentrale Konfiguration: Pfade, Spaltennamen, Grenzwerte und Farben."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("KOELN_LUFT_DATA_DIR", PROJECT_ROOT / "data"))

AIR_FILE = DATA_DIR / "Luftqualitaet_Koeln_2025.csv"
WEATHER_FILE = DATA_DIR / "Wetterdaten_Koeln_2025.csv"

TIMEZONE = "Europe/Berlin"
YEAR = 2025

# Ein Tagesmittel gilt als gültig, wenn mindestens 75 % der Stundenwerte vorliegen
# (18 von 24 Stunden, entsprechend der EU-Luftqualitätsrichtlinie).
MIN_HOURS_PER_DAY = 18

# Schlüsselwörter im Originalspaltennamen -> kurzer Spaltenname
AIR_COLUMN_KEYWORDS: dict[str, str] = {
    "Stationscode": "station",
    "Datum": "datum",
    "PM₁₀": "pm10",
    "Ozon": "o3",
    "NO₂": "no2",
    "PM₂,₅": "pm25",
    "SO₂": "so2",
    "Luftqualitätsindex": "aqi",
}

POLLUTANTS: dict[str, str] = {
    "pm10": "Feinstaub PM10",
    "pm25": "Feinstaub PM2,5",
    "no2": "Stickstoffdioxid NO₂",
}
POLLUTANTS_SHORT: dict[str, str] = {"pm10": "PM10", "pm25": "PM2,5", "no2": "NO₂"}
UNIT = "µg/m³"

WEATHER_COLUMNS: dict[str, str] = {
    "tavg": "Temperatur Mittel (°C)",
    "tmin": "Temperatur Min (°C)",
    "tmax": "Temperatur Max (°C)",
    "prcp": "Niederschlag (mm)",
    "wspd": "Windgeschwindigkeit (km/h)",
    "pres": "Luftdruck (hPa)",
}

AQI_LEVELS: list[str] = ["sehr gut", "gut", "mäßig", "schlecht", "sehr schlecht"]

# Farben ------------------------------------------------------------------
# Schadstoffe: feste Reihenfolge der kategorialen Palette (blau, orange, aqua).
POLLUTANT_COLORS: dict[str, str] = {
    "pm10": "#2a78d6",
    "pm25": "#eb6834",
    "no2": "#1baf7a",
}
# Index-Stufen: geordnete, divergierende Skala (blau = gut, grau = Mitte, rot = schlecht).
AQI_COLORS: dict[str, str] = {
    "sehr gut": "#256abf",
    "gut": "#86b6ef",
    "mäßig": "#b5b3aa",
    "schlecht": "#ee8a87",
    "sehr schlecht": "#c62f2f",
}
SEQUENTIAL_BLUE: list[str] = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
]
SINGLE_SERIES_COLOR = "#2a78d6"
REFERENCE_LINE_COLOR = "#898781"


# Grenz- und Richtwerte ---------------------------------------------------
@dataclass(frozen=True)
class Limit:
    pollutant: str
    period: str  # "stunde", "tag" oder "jahr"
    value: float
    allowed_exceedances: int | None
    source: str

    @property
    def label(self) -> str:
        period = {"stunde": "Stundenwert", "tag": "Tagesmittel", "jahr": "Jahresmittel"}[self.period]
        return f"{self.source}: {period} {self.value:g} {UNIT}"


LIMITS: list[Limit] = [
    # EU-Grenzwerte (39. BImSchV, gültig 2025)
    Limit("pm10", "tag", 50, 35, "EU"),
    Limit("pm10", "jahr", 40, None, "EU"),
    Limit("pm25", "jahr", 25, None, "EU"),
    Limit("no2", "stunde", 200, 18, "EU"),
    Limit("no2", "jahr", 40, None, "EU"),
    # EU-Grenzwerte ab 2030 (Richtlinie (EU) 2024/2881)
    Limit("pm10", "tag", 45, 18, "EU 2030"),
    Limit("pm10", "jahr", 20, None, "EU 2030"),
    Limit("pm25", "tag", 25, 18, "EU 2030"),
    Limit("pm25", "jahr", 10, None, "EU 2030"),
    Limit("no2", "stunde", 200, 3, "EU 2030"),
    Limit("no2", "tag", 50, 18, "EU 2030"),
    Limit("no2", "jahr", 20, None, "EU 2030"),
    # WHO-Richtwerte 2021 (Tageswerte als 99. Perzentil: ca. 3-4 Tage/Jahr)
    Limit("pm10", "tag", 45, 4, "WHO"),
    Limit("pm10", "jahr", 15, None, "WHO"),
    Limit("pm25", "tag", 15, 4, "WHO"),
    Limit("pm25", "jahr", 5, None, "WHO"),
    Limit("no2", "tag", 25, 4, "WHO"),
    Limit("no2", "jahr", 10, None, "WHO"),
]

WEEKDAYS: list[str] = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTHS: list[str] = [
    "Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]
