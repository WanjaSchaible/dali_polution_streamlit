import streamlit as st

from koeln_luft import charts, config, processing
from shared import fmt, load_data, page_header

page_header(
    "Wettereinfluss",
    "Wie hängen die Schadstoffwerte mit Wind, Niederschlag, Temperatur und Luftdruck zusammen?",
)

data = load_data()
merged = data.merged
pollutants = list(config.POLLUTANTS)

st.subheader("Korrelation auf Tagesbasis")
corr = processing.weather_correlations(merged)
st.plotly_chart(charts.correlation_bars(corr), use_container_width=True)
with st.expander("Tabelle"):
    st.dataframe(
        corr.rename(index=config.POLLUTANTS, columns=config.WEATHER_COLUMNS).round(2),
        use_container_width=True,
    )
st.caption(
    "Spearman-Rangkorrelation zwischen Tagesmitteln: −1 = starker gegenläufiger, "
    "+1 = starker gleichläufiger Zusammenhang. Korrelation ist kein Nachweis von Ursache."
)

st.divider()
st.subheader("Einzelzusammenhang")
c1, c2 = st.columns(2)
x = c1.selectbox(
    "Wettergröße",
    [c for c in config.WEATHER_COLUMNS if c in merged.columns],
    index=4,
    format_func=config.WEATHER_COLUMNS.get,
)
y = c2.selectbox("Schadstoff", pollutants, format_func=config.POLLUTANTS.get)
fit = processing.linear_fit(merged[x], merged[y])
st.plotly_chart(charts.scatter_with_fit(merged, x, y, fit), use_container_width=True)
if fit:
    st.caption(
        f"Lineare Regression: pro Einheit {config.WEATHER_COLUMNS[x]} ändert sich "
        f"{config.POLLUTANTS[y]} im Mittel um {fmt(fit[0], 2)} {config.UNIT}."
    )

st.divider()
st.subheader("Vergleich nach Wetterklassen")
tab_wind, tab_rain, tab_temp = st.tabs(["Wind", "Niederschlag", "Temperatur"])
with tab_wind:
    table = processing.binned_means(
        merged, "wspd", [0, 8, 12, 16, 100], ["< 8 km/h", "8–12 km/h", "12–16 km/h", "≥ 16 km/h"]
    )
    st.plotly_chart(
        charts.grouped_bars(table, pollutants, "Mittlere Windgeschwindigkeit"),
        use_container_width=True,
    )
with tab_rain:
    table = processing.binned_means(
        merged, "prcp", [0, 0.1, 5, 100], ["trocken (< 0,1 mm)", "0,1–5 mm", "≥ 5 mm"]
    )
    st.plotly_chart(charts.grouped_bars(table, pollutants, "Tagesniederschlag"), use_container_width=True)
with tab_temp:
    table = processing.binned_means(
        merged, "tavg", [-20, 5, 12, 20, 40], ["< 5 °C", "5–12 °C", "12–20 °C", "≥ 20 °C"]
    )
    st.plotly_chart(
        charts.grouped_bars(table, pollutants, "Tagesmitteltemperatur"), use_container_width=True
    )
st.caption("Klassen mit gleicher Methode: Mittel der Tagesmittelwerte; Tageszahl im Tooltip.")
