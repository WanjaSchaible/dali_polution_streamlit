"""Gemeinsame Hilfsfunktionen für alle Seiten: gecachtes Laden, Seitenkopf."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from koeln_luft import config, data_loader, processing


@dataclass
class Data:
    air: pd.DataFrame  # stündlich
    weather: pd.DataFrame  # täglich
    daily: pd.DataFrame  # Tagesmittel Luft
    merged: pd.DataFrame  # Tagesmittel Luft + Wetter


@st.cache_data(show_spinner="Daten werden geladen …")
def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    return data_loader.load_air_quality(), data_loader.load_weather()


def load_data() -> Data:
    air, weather = _load()
    daily = processing.daily_air(air)
    return Data(air=air, weather=weather, daily=daily, merged=processing.merge_daily(daily, weather))


def page_header(title: str, question: str) -> None:
    st.set_page_config(page_title=f"{title} · Luft Köln 2025", page_icon="🌫️", layout="wide")
    st.title(title)
    st.caption(question)
    with st.sidebar:
        st.markdown(
            "**Datenbasis**  \n"
            "Luftqualität: Messstation DENW211, Stundenwerte 2025  \n"
            "Wetter: Köln, Tageswerte 2025"
        )


def pollutant_select(label: str = "Schadstoff", key: str | None = None) -> str:
    return st.selectbox(
        label, list(config.POLLUTANTS), format_func=config.POLLUTANTS.get, key=key
    )


def fmt(value: float, digits: int = 1) -> str:
    """Zahl im deutschen Format."""
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
