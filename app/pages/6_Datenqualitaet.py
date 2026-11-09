import streamlit as st

from koeln_luft import charts, config, processing
from shared import load_data, page_header

page_header("Datenqualität", "Wie vollständig sind die Messdaten, und wo gibt es Lücken?")

data = load_data()
air, weather = data.air, data.weather

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stunden 2025", f"{len(air):,}".replace(",", "."))
for col, pollutant in zip((c2, c3, c4), config.POLLUTANTS):
    share = air[pollutant].notna().mean() * 100
    col.metric(f"{config.POLLUTANTS[pollutant]} vorhanden", f"{share:.1f} %".replace(".", ","))

st.subheader("Vollständigkeit je Monat")
st.plotly_chart(charts.completeness_heatmap(processing.completeness_by_month(air)), use_container_width=True)

st.subheader("Längste Lücken")
pollutant = st.selectbox("Schadstoff", list(config.POLLUTANTS), format_func=config.POLLUTANTS.get)
runs = processing.missing_runs(air[pollutant]).head(10)
runs["beginn"] = runs["beginn"].dt.strftime("%d.%m.%Y %H:%M")
runs["ende"] = runs["ende"].dt.strftime("%d.%m.%Y %H:%M")
st.dataframe(
    runs.rename(columns={"beginn": "Beginn", "ende": "Ende (letzte fehlende Stunde)", "stunden": "Stunden"}),
    hide_index=True,
    use_container_width=True,
)

st.subheader("Hinweise zur Aufbereitung")
missing_weather = weather.index[weather.isna().all(axis=1)].strftime("%d.%m.%Y").tolist()
invalid_days = {
    config.POLLUTANTS[p]: int(data.daily[p].isna().sum()) for p in config.POLLUTANTS
}
st.markdown(
    f"""
- **Leere Spalten entfernt:** Luftqualität: {", ".join(air.attrs.get("leere_spalten", [])) or "keine"}
  (Ozon, Schwefeldioxid), Wetter: {", ".join(weather.attrs.get("leere_spalten", [])) or "keine"}.
- **Zeitstempel:** Die Rohdaten geben das Stunden-*Ende* in Ortszeit an (erkennbar an der Zeitumstellung:
  am 30.03. fehlt 03:00, am 26.10. kommt 03:00 doppelt vor). Im Dashboard wird der Stunden-*Beginn* verwendet.
  Der erste Rohwert (01.01. 00:00) gehört damit zum 31.12.2024 und ist nicht enthalten.
- **Uneinheitliches Datumsformat:** Eine Zeile liegt im Format TT.MM.JJJJ HH:MM vor und wird mit eingelesen.
- **Ungültige Tagesmittel** (weniger als {config.MIN_HOURS_PER_DAY} Stundenwerte):
  {", ".join(f"{k}: {v}" for k, v in invalid_days.items())} Tage.
- **Wetterdaten fehlen** an {len(missing_weather)} Tagen: {", ".join(missing_weather) or "keine"}.
"""
)
