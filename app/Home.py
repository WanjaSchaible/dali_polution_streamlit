import streamlit as st

from koeln_luft import charts, config, processing
from shared import fmt, load_data, page_header

page_header(
    "Luftqualität Köln 2025",
    "Wie gut war die Luft in Köln im Jahr 2025? Überblick über Feinstaub, Stickstoffdioxid "
    "und den Luftqualitätsindex.",
)

data = load_data()
air = data.air

# Kennzahlen -------------------------------------------------------------------
means = processing.annual_means(air)
eu_annual = {
    lim.pollutant: lim.value for lim in config.LIMITS if lim.source == "EU" and lim.period == "jahr"
}
who_annual = {
    lim.pollutant: lim.value
    for lim in config.LIMITS
    if lim.source == "WHO" and lim.period == "jahr"
}

cols = st.columns(4)
for col, pollutant in zip(cols, config.POLLUTANTS):
    col.metric(
        f"{config.POLLUTANTS_SHORT[pollutant]} · Jahresmittel ({config.UNIT})",
        fmt(means[pollutant]),
        help=(
            f"EU-Grenzwert: {eu_annual[pollutant]:g} {config.UNIT}, "
            f"WHO-Richtwert: {who_annual[pollutant]:g} {config.UNIT}"
        ),
    )
    ratio = means[pollutant] / who_annual[pollutant]
    col.caption(
        f"{fmt(means[pollutant] / eu_annual[pollutant] * 100, 0)} % des EU-Grenzwerts · "
        f"{fmt(ratio, 1)}-fach WHO-Richtwert"
    )

pm10_days = int((data.daily["pm10"] > 50).sum())
cols[3].metric("PM10-Tage > 50 µg/m³", f"{pm10_days}")
cols[3].caption("EU erlaubt höchstens 35 Tage pro Jahr")

st.divider()

# Luftqualitätsindex ---------------------------------------------------------
st.subheader("Verteilung des Luftqualitätsindex")
share = processing.aqi_distribution(air)
good = share.loc[["sehr gut", "gut"], "anteil"].sum()
bad = share.loc[["schlecht", "sehr schlecht"], "anteil"].sum()
st.markdown(
    f"In **{fmt(good, 0)} %** der Stunden mit Indexwert war die Luft *gut* oder *sehr gut*, "
    f"in **{fmt(bad, 0)} %** *schlecht* oder *sehr schlecht*."
)
st.plotly_chart(charts.aqi_share_bar(share), use_container_width=True)

st.markdown("**Anteil der Indexstufen je Monat**")
st.plotly_chart(
    charts.aqi_monthly_bars(processing.aqi_distribution(air, by="monat")),
    use_container_width=True,
)
with st.expander("Tabelle"):
    table = processing.aqi_distribution(air, by="monat").round(1)
    table.index = [config.MONTHS[m - 1] for m in table.index]
    st.dataframe(table, use_container_width=True)

st.divider()
st.markdown(
    """
**Weitere Seiten** (Navigation links)

1. **Zeitverlauf**: Schadstoffe über das Jahr in wählbarer Auflösung
2. **Grenzwerte**: Einhaltung von EU-Grenzwerten und WHO-Richtwerten
3. **Muster**: Tagesgang, Wochentage und Jahreszeiten
4. **Wettereinfluss**: Zusammenhang mit Wind, Regen, Temperatur und Luftdruck
5. **Extremereignisse**: die Tage mit der schlechtesten Luft
6. **Datenqualität**: Lücken und Vollständigkeit der Messungen
"""
)
