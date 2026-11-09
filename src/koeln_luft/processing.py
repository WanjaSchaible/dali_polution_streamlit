"""Auswertungen auf Basis der bereinigten Daten (ohne Streamlit-Abhängigkeit)."""

from __future__ import annotations

import pandas as pd

from koeln_luft import config
from koeln_luft.config import Limit

POLLUTANT_COLS = list(config.POLLUTANTS)


# Aggregation ----------------------------------------------------------------
def daily_air(air: pd.DataFrame) -> pd.DataFrame:
    """Tagesmittel je Schadstoff; ungültig (NaN) bei weniger als 18 Stundenwerten."""
    grouped = air.groupby("datum")
    means = grouped[POLLUTANT_COLS].mean()
    counts = grouped[POLLUTANT_COLS].count()
    means = means.where(counts >= config.MIN_HOURS_PER_DAY)

    result = means.join(counts.add_prefix("n_"))
    result = result.join(grouped[POLLUTANT_COLS].max().add_suffix("_max"))
    result["aqi_schlechteste"] = grouped["aqi"].max()
    result.index.name = "datum"
    return result


def merge_daily(daily: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    return daily.join(weather, how="left")


def resample(air: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Mittelwerte der Schadstoffe in der gewünschten Auflösung ('h', 'D', 'W', 'MS')."""
    if rule == "h":
        return air[POLLUTANT_COLS]
    return air[POLLUTANT_COLS].resample(rule).mean()


def annual_means(air: pd.DataFrame) -> pd.Series:
    return air[POLLUTANT_COLS].mean()


# Grenzwerte -----------------------------------------------------------------
def evaluate_limit(limit: Limit, air: pd.DataFrame, daily: pd.DataFrame) -> dict:
    """Bewertet einen Grenz-/Richtwert und gibt eine Tabellenzeile zurück."""
    if limit.period == "jahr":
        value = air[limit.pollutant].mean()
        ok = value <= limit.value
        exceedances = None
        measured = f"{value:.1f} {config.UNIT}"
    else:
        series = air[limit.pollutant] if limit.period == "stunde" else daily[limit.pollutant]
        exceedances = int((series > limit.value).sum())
        ok = exceedances <= (limit.allowed_exceedances or 0)
        unit = "Stunden" if limit.period == "stunde" else "Tage"
        measured = f"{exceedances} {unit} über {limit.value:g}"
    return {
        "Quelle": limit.source,
        "Schadstoff": config.POLLUTANTS[limit.pollutant],
        "Mittelung": {"stunde": "Stunde", "tag": "Tag", "jahr": "Jahr"}[limit.period],
        f"Wert ({config.UNIT})": limit.value,
        "Erlaubte Überschreitungen": limit.allowed_exceedances,
        "Messung 2025": measured,
        "Überschreitungen": exceedances,
        "Eingehalten": ok,
    }


def limit_table(air: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    table = pd.DataFrame([evaluate_limit(lim, air, daily) for lim in config.LIMITS])
    for col in ("Erlaubte Überschreitungen", "Überschreitungen"):
        table[col] = table[col].astype("Int64")
    return table


def exceedances_per_month(series: pd.Series, threshold: float) -> pd.Series:
    """Anzahl der Werte über dem Schwellenwert je Monat (1-12)."""
    over = (series > threshold).groupby(series.index.month).sum()
    return over.reindex(range(1, 13), fill_value=0).astype(int)


# Muster ---------------------------------------------------------------------
def hour_weekday_matrix(air: pd.DataFrame, pollutant: str) -> pd.DataFrame:
    """Mittelwert je Wochentag (Zeilen) und Stunde (Spalten)."""
    return air.pivot_table(index="wochentag", columns="stunde", values=pollutant, aggfunc="mean")


def diurnal_profile(air: pd.DataFrame, pollutant: str) -> pd.DataFrame:
    """Tagesgang getrennt nach Werktag und Wochenende."""
    profile = air.pivot_table(
        index="stunde", columns="wochenende", values=pollutant, aggfunc="mean"
    )
    return profile.rename(columns={False: "Werktag", True: "Wochenende"})


def monthly_means(air: pd.DataFrame) -> pd.DataFrame:
    return air.groupby("monat")[POLLUTANT_COLS].mean()


def aqi_distribution(air: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Anteil (%) der Stunden je Indexstufe, optional gruppiert (z. B. nach 'monat')."""
    valid = air.dropna(subset=["aqi"])
    if by is None:
        share = valid["aqi"].value_counts(normalize=True).reindex(config.AQI_LEVELS) * 100
        return share.to_frame("anteil")
    table = pd.crosstab(valid[by], valid["aqi"], normalize="index") * 100
    return table.reindex(columns=config.AQI_LEVELS, fill_value=0)


# Wetter ---------------------------------------------------------------------
def weather_correlations(merged: pd.DataFrame, method: str = "spearman") -> pd.DataFrame:
    """Korrelation Schadstoff (Zeilen) × Wettergröße (Spalten) auf Tagesbasis."""
    weather_cols = [c for c in config.WEATHER_COLUMNS if c in merged.columns]
    corr = merged[POLLUTANT_COLS + weather_cols].corr(method=method)
    return corr.loc[POLLUTANT_COLS, weather_cols]


def binned_means(
    merged: pd.DataFrame, column: str, bins: list[float], labels: list[str]
) -> pd.DataFrame:
    """Mittlere Schadstoffwerte je Klasse einer Wettergröße, inkl. Anzahl Tage."""
    classes = pd.cut(merged[column], bins=bins, labels=labels, include_lowest=True)
    grouped = merged.groupby(classes, observed=False)
    result = grouped[POLLUTANT_COLS].mean()
    result["tage"] = grouped.size()
    return result


def linear_fit(x: pd.Series, y: pd.Series) -> tuple[float, float] | None:
    """Steigung und Achsenabschnitt einer einfachen linearen Regression."""
    data = pd.concat([x, y], axis=1).dropna()
    if len(data) < 3:
        return None
    xs, ys = data.iloc[:, 0], data.iloc[:, 1]
    slope = ((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum()
    return float(slope), float(ys.mean() - slope * xs.mean())


# Extremereignisse ----------------------------------------------------------
def top_days(merged: pd.DataFrame, pollutant: str, n: int = 10) -> pd.DataFrame:
    weather_cols = [c for c in config.WEATHER_COLUMNS if c in merged.columns]
    cols = [pollutant, f"{pollutant}_max", "aqi_schlechteste", *weather_cols]
    return merged.nlargest(n, pollutant)[cols]


# Datenqualität -------------------------------------------------------------
def completeness_by_month(air: pd.DataFrame) -> pd.DataFrame:
    """Anteil vorhandener Stundenwerte (%) je Monat und Schadstoff."""
    cols = POLLUTANT_COLS + ["aqi"]
    present = air[cols].notna().groupby(air["monat"]).mean() * 100
    return present


def missing_runs(series: pd.Series) -> pd.DataFrame:
    """Zusammenhängende Lücken: Beginn, Ende und Dauer in Stunden."""
    missing = series.isna()
    run_id = (missing != missing.shift()).cumsum()
    runs = series.index.to_series()[missing].groupby(run_id[missing]).agg(["first", "last", "size"])
    runs.columns = ["beginn", "ende", "stunden"]
    return runs.sort_values("stunden", ascending=False).reset_index(drop=True)
