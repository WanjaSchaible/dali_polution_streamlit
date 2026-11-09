import datetime as dt

import streamlit as st

from koeln_luft import charts, config, processing
from shared import load_data, page_header

page_header("Zeitverlauf", "Wie haben sich die Schadstoffwerte im Laufe des Jahres entwickelt?")

data = load_data()

RESOLUTIONS = {"Stunde": "h", "Tag": "D", "Woche": "W", "Monat": "MS"}

c1, c2, c3 = st.columns([2, 3, 2])
period = c1.date_input(
    "Zeitraum",
    value=(dt.date(config.YEAR, 1, 1), dt.date(config.YEAR, 12, 31)),
    min_value=dt.date(config.YEAR, 1, 1),
    max_value=dt.date(config.YEAR, 12, 31),
    format="DD.MM.YYYY",
)
# Während der Auswahl liefert das Widget nur ein Datum.
start, end = (period[0], period[-1]) if isinstance(period, tuple) and period else (period, period)
pollutants = c2.multiselect(
    "Schadstoffe",
    list(config.POLLUTANTS),
    default=list(config.POLLUTANTS),
    format_func=config.POLLUTANTS.get,
)
resolution = c3.segmented_control(
    "Auflösung", list(RESOLUTIONS), default="Tag", selection_mode="single"
) or "Tag"

if not pollutants:
    st.info("Bitte mindestens einen Schadstoff auswählen.")
    st.stop()

air = data.air[(data.air["datum"].dt.date >= start) & (data.air["datum"].dt.date <= end)]
series = processing.resample(air, RESOLUTIONS[resolution])

show_limits = st.toggle("WHO-Richtwerte (Tagesmittel) einblenden", value=False)
reference = []
if show_limits:
    reference = [
        (lim.value, f"WHO {config.POLLUTANTS[lim.pollutant]}")
        for lim in config.LIMITS
        if lim.source == "WHO" and lim.period == "tag" and lim.pollutant in pollutants
    ]

st.plotly_chart(charts.pollutant_lines(series, pollutants, reference), use_container_width=True)
st.caption(
    f"{resolution}smittelwerte. Lücken in der Linie sind fehlende Messwerte. "
    "Die Stundenauflösung zeigt kurzfristige Spitzen wie die Silvesternacht."
)

st.subheader("Wetter im selben Zeitraum")
weather = data.weather.loc[str(start):str(end)]
w1, w2 = st.columns(2)
w1.plotly_chart(
    charts.single_line(weather["tavg"], config.WEATHER_COLUMNS["tavg"]), use_container_width=True
)
w2.plotly_chart(
    charts.single_line(weather["wspd"], config.WEATHER_COLUMNS["wspd"]), use_container_width=True
)
st.plotly_chart(
    charts.single_line(weather["prcp"], config.WEATHER_COLUMNS["prcp"], bar=True),
    use_container_width=True,
)
