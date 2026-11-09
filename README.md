# Luftqualität Köln 2025 – Streamlit-Dashboard

Interaktives Dashboard zu Feinstaub (PM10, PM2,5), Stickstoffdioxid (NO₂) und dem
Luftqualitätsindex der Kölner Messstation DENW211 im Jahr 2025, verknüpft mit Kölner
Wetterdaten.

## Fragestellungen

| Seite | Frage |
|---|---|
| Home | Wie gut war die Luft 2025 insgesamt? |
| Zeitverlauf | Wie haben sich die Werte im Jahresverlauf entwickelt? |
| Grenzwerte | Wurden EU-Grenzwerte (heute und ab 2030) und WHO-Richtwerte eingehalten? |
| Muster | Gibt es Muster nach Tageszeit, Wochentag und Monat? |
| Wettereinfluss | Wie hängen Schadstoffe mit Wind, Regen, Temperatur und Luftdruck zusammen? |
| Extremereignisse | Welche Tage waren am schlechtesten, und wie war dort das Wetter? |
| Datenqualität | Wie vollständig sind die Daten? |

## Einrichtung

Voraussetzung: Python 3.11 oder neuer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Start
Wenn das Environment nicht geladen wurde:
```bash
.venv/bin/streamlit run app/Home.py 
```
Wenn das Environment vorher geladen wurde:
```bash
streamlit run app/Home.py 
```


## Tests und Linting

```bash
pytest
ruff check src app tests
```

## Projektstruktur

```
data/                    Rohdaten (CSV, unverändert)
src/koeln_luft/
  config.py              Pfade, Spaltennamen, Grenzwerte, Farben
  data_loader.py         Einlesen und Bereinigen der CSV-Dateien
  processing.py          Auswertungen (ohne Streamlit, testbar)
  charts.py              Plotly-Diagramme
app/
  Home.py                Startseite
  shared.py              Gecachtes Laden, Seitenkopf
  pages/                 Unterseiten
tests/                   pytest-Tests
```

Der Datenordner kann über die Umgebungsvariable `KOELN_LUFT_DATA_DIR` geändert werden.

## Hinweise zu den Daten

- **Zeitstempel:** Die Luftqualitätsdaten geben das Stunden-Ende in Ortszeit an. Das Dashboard
  rechnet auf den Stunden-Beginn mit Zeitzone Europe/Berlin um, damit die Zeitumstellung
  korrekt behandelt wird.
- **Leere Spalten:** Ozon und Schwefeldioxid sind leer. In den Wetterdaten sind Schnee,
  Windrichtung, Böen und Sonnenscheindauer leer. Alle diese Spalten werden entfernt.
- **Lücken:** Im Dezember fehlen fast alle Luftmesswerte, die Wetterdaten fehlen vom 15. bis
  21.03. Tagesmittel gelten erst ab 18 Stundenwerten als gültig.
