import pandas as pd
import streamlit as st

from koeln_luft import charts, config, processing
from shared import fmt, load_data, page_header

page_header(
    "Extremereignisse",
    "An welchen Tagen war die Luft am schlechtesten, und wie war dort das Wetter?",
)

data = load_data()

c1, c2 = st.columns([3, 1])
pollutant = c1.selectbox("Sortieren nach", list(config.POLLUTANTS), format_func=config.POLLUTANTS.get)
n = c2.number_input("Anzahl Tage", min_value=5, max_value=30, value=10, step=5)

top = processing.top_days(data.merged, pollutant, int(n))
display = top.rename(
    columns={
        pollutant: f"Tagesmittel ({config.UNIT})",
        f"{pollutant}_max": f"Max. Stundenwert ({config.UNIT})",
        "aqi_schlechteste": "Schlechteste Indexstufe",
        **config.WEATHER_COLUMNS,
    }
)
display.index = [f"{config.WEEKDAYS[d.dayofweek]} {d:%d.%m.%Y}" for d in display.index]
st.dataframe(display.round(1), use_container_width=True)

means = data.merged[list(config.WEATHER_COLUMNS)].mean()
top_means = top[list(config.WEATHER_COLUMNS)].mean()
st.markdown(
    f"An diesen Tagen lag die mittlere Windgeschwindigkeit bei **{fmt(top_means['wspd'])} km/h** "
    f"(Jahresmittel {fmt(means['wspd'])} km/h), der Niederschlag bei "
    f"**{fmt(top_means['prcp'])} mm** (Jahresmittel {fmt(means['prcp'])} mm)."
)

st.divider()
st.subheader("Stundenverlauf eines Tages")
options = list(top.index)
silvester = pd.Timestamp(config.YEAR, 1, 1)
if silvester not in options:
    options.append(silvester)
day = st.selectbox(
    "Tag", options, format_func=lambda d: d.strftime("%d.%m.%Y") + (" (Neujahr)" if d == silvester else "")
)
window = data.air[
    (data.air["datum"] >= day - pd.Timedelta(days=1)) & (data.air["datum"] <= day + pd.Timedelta(days=1))
]
st.plotly_chart(charts.pollutant_lines(window, list(config.POLLUTANTS)), use_container_width=True)
st.caption("Gewählter Tag mit Vor- und Folgetag. Neujahr zeigt den Feuerwerkseffekt in den ersten Stunden.")
