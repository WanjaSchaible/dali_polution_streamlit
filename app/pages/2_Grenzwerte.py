import streamlit as st

from koeln_luft import charts, config, processing
from shared import load_data, page_header

page_header(
    "Grenzwerte",
    "Wurden die EU-Grenzwerte und die WHO-Richtwerte 2025 eingehalten? "
    "An wie vielen Tagen bzw. Stunden wurden sie überschritten?",
)

data = load_data()
table = processing.limit_table(data.air, data.daily)

sources = st.segmented_control(
    "Bewertungsmaßstab",
    ["EU", "EU 2030", "WHO"],
    default=["EU", "EU 2030", "WHO"],
    selection_mode="multi",
)
view = table[table["Quelle"].isin(sources or [])]

n_ok = int(view["Eingehalten"].sum())
st.markdown(f"**{n_ok} von {len(view)}** ausgewählten Werten eingehalten.")
st.dataframe(
    view.assign(Eingehalten=view["Eingehalten"].map({True: "✅ ja", False: "❌ nein"})),
    hide_index=True,
    use_container_width=True,
)
st.caption(
    "EU: geltende Grenzwerte (39. BImSchV). EU 2030: Grenzwerte der Richtlinie (EU) 2024/2881, "
    "verbindlich ab 2030. WHO: Richtwerte der Luftqualitätsleitlinien 2021; für Tageswerte gilt "
    "das 99. Perzentil, also etwa 3–4 Überschreitungstage pro Jahr. "
    "Tagesmittel zählen nur bei mindestens 18 gültigen Stundenwerten."
)

st.divider()
st.subheader("Überschreitungen im Jahresverlauf")

daily_limits = [lim for lim in config.LIMITS if lim.period in ("tag", "stunde")]
choice = st.selectbox(
    "Grenz-/Richtwert",
    daily_limits,
    format_func=lambda lim: f"{config.POLLUTANTS[lim.pollutant]} · {lim.label}",
)
if choice.period == "tag":
    series = data.daily[choice.pollutant]
    unit = "Tage"
else:
    series = data.air[choice.pollutant].tz_localize(None)
    unit = "Stunden"

monthly = processing.exceedances_per_month(series, choice.value)
left, right = st.columns([2, 3])
left.plotly_chart(
    charts.monthly_bars(monthly, f"{unit} über {choice.value:g} {config.UNIT}", unit),
    use_container_width=True,
)
right.plotly_chart(
    charts.daily_strip(data.daily[choice.pollutant], choice.value, choice.label),
    use_container_width=True,
)
right.caption("Tagesmittel; rot markiert sind Tage über dem gewählten Wert.")
