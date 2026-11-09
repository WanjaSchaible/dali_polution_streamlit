import streamlit as st

from koeln_luft import charts, config, processing
from shared import fmt, load_data, page_header

page_header(
    "Muster",
    "Gibt es typische Muster nach Tageszeit, Wochentag und Jahreszeit? "
    "Ist die Belastung an Werktagen höher als am Wochenende?",
)

data = load_data()
pollutant = st.selectbox(
    "Schadstoff", list(config.POLLUTANTS), index=2, format_func=config.POLLUTANTS.get
)
label = config.POLLUTANTS[pollutant]

profile = processing.diurnal_profile(data.air, pollutant)
weekday_mean = data.air.loc[~data.air["wochenende"], pollutant].mean()
weekend_mean = data.air.loc[data.air["wochenende"], pollutant].mean()
diff = (weekday_mean / weekend_mean - 1) * 100

c1, c2, c3 = st.columns(3)
c1.metric("Mittel Werktag (Mo–Fr)", f"{fmt(weekday_mean)} {config.UNIT}")
c2.metric("Mittel Wochenende (Sa–So)", f"{fmt(weekend_mean)} {config.UNIT}")
c3.metric("Werktag gegenüber Wochenende", f"{diff:+.0f} %".replace(".", ","))

st.subheader("Mittelwert nach Wochentag und Stunde")
st.plotly_chart(
    charts.hour_weekday_heatmap(processing.hour_weekday_matrix(data.air, pollutant), label),
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    st.subheader("Tagesgang")
    st.plotly_chart(charts.diurnal_lines(profile, pollutant), use_container_width=True)
    st.caption("Feiertage sind nicht gesondert berücksichtigt und zählen als Werktag.")
with right:
    st.subheader("Verteilung je Monat")
    st.plotly_chart(charts.monthly_box(data.air, pollutant), use_container_width=True)
    st.caption("Box: mittlere 50 % der Stundenwerte, Strich: Median, Antennen: übliche Spannweite.")
