"""Wiederverwendbare Plotly-Diagramme.

Gestaltungsregeln: eine y-Achse pro Diagramm (kein Doppelachsen-Diagramm),
feste Farben pro Schadstoff, dünne Linien, Referenzlinien in neutralem Grau.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from koeln_luft import config

LINE_WIDTH = 2


def _style(fig: go.Figure, *, height: int = 380, hovermode: str = "closest") -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode=hovermode,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            title=None, traceorder="normal",
        ),
        separators=",.",
    )
    return fig


def _add_reference_lines(fig: go.Figure, lines: list[tuple[float, str]]) -> None:
    for value, label in lines:
        fig.add_hline(
            y=value,
            line=dict(color=config.REFERENCE_LINE_COLOR, width=1, dash="dash"),
            annotation_text=label,
            annotation_position="top left",
            annotation_font_color=config.REFERENCE_LINE_COLOR,
        )


def pollutant_lines(
    df: pd.DataFrame, pollutants: list[str], reference_lines: list[tuple[float, str]] | None = None
) -> go.Figure:
    fig = go.Figure()
    for col in pollutants:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                name=config.POLLUTANTS[col],
                mode="lines",
                line=dict(color=config.POLLUTANT_COLORS[col], width=LINE_WIDTH),
                hovertemplate="%{y:.1f} " + config.UNIT,
                connectgaps=False,
            )
        )
    _add_reference_lines(fig, reference_lines or [])
    fig.update_yaxes(title=config.UNIT, rangemode="tozero")
    return _style(fig, hovermode="x unified")


def single_line(series: pd.Series, label: str, *, bar: bool = False, height: int = 220) -> go.Figure:
    trace_cls = go.Bar if bar else go.Scatter
    kwargs = (
        dict(marker_color=config.SINGLE_SERIES_COLOR)
        if bar
        else dict(mode="lines", line=dict(color=config.SINGLE_SERIES_COLOR, width=LINE_WIDTH))
    )
    fig = go.Figure(trace_cls(x=series.index, y=series.values, name=label, **kwargs))
    fig.update_layout(title=dict(text=label, font_size=14), showlegend=False)
    return _style(fig, height=height, hovermode="x unified")


def aqi_share_bar(share: pd.DataFrame) -> go.Figure:
    """Ein horizontaler 100-%-Balken mit den Anteilen der Indexstufen."""
    fig = go.Figure()
    for level in config.AQI_LEVELS:
        value = float(share.loc[level, "anteil"]) if level in share.index else 0.0
        fig.add_trace(
            go.Bar(
                y=["2025"],
                x=[value],
                name=level,
                orientation="h",
                marker_color=config.AQI_COLORS[level],
                text=[f"{value:.0f} %" if value >= 4 else ""],
                textposition="inside",
                insidetextfont_color="#0b0b0b",
                hovertemplate=f"{level}: " + "%{x:.1f} %<extra></extra>",
            )
        )
    fig.update_layout(barmode="stack", bargap=0.2)
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", showgrid=False)
    fig.update_yaxes(showticklabels=False)
    return _style(fig, height=150)


def aqi_monthly_bars(table: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    months = [config.MONTHS[m - 1] for m in table.index]
    for level in config.AQI_LEVELS:
        fig.add_trace(
            go.Bar(
                x=months,
                y=table[level],
                name=level,
                marker_color=config.AQI_COLORS[level],
                hovertemplate=f"{level}: " + "%{y:.1f} %<extra>%{x}</extra>",
            )
        )
    fig.update_layout(barmode="stack", bargap=0.25)
    fig.update_yaxes(range=[0, 100], ticksuffix=" %", title="Anteil der Stunden")
    return _style(fig)


def hour_weekday_heatmap(matrix: pd.DataFrame, label: str) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=[f"{h:02d}" for h in matrix.columns],
            y=[config.WEEKDAYS[d] for d in matrix.index],
            colorscale=[[i / (len(config.SEQUENTIAL_BLUE) - 1), c]
                        for i, c in enumerate(config.SEQUENTIAL_BLUE)],
            colorbar=dict(title=config.UNIT),
            xgap=2,
            ygap=2,
            hovertemplate="%{y}, %{x} Uhr: %{z:.1f} " + config.UNIT + "<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Stunde (Beginn, Ortszeit)")
    fig.update_layout(title=dict(text=label, font_size=14))
    return _style(fig, height=340)


def diurnal_lines(profile: pd.DataFrame, pollutant: str) -> go.Figure:
    color = config.POLLUTANT_COLORS[pollutant]
    styles = {"Werktag": "solid", "Wochenende": "dot"}
    fig = go.Figure()
    for col in profile.columns:
        fig.add_trace(
            go.Scatter(
                x=profile.index,
                y=profile[col],
                name=col,
                mode="lines+markers",
                marker_size=6,
                line=dict(color=color, width=LINE_WIDTH, dash=styles.get(col, "solid")),
                hovertemplate="%{y:.1f} " + config.UNIT,
            )
        )
    fig.update_xaxes(title="Stunde (Beginn, Ortszeit)", dtick=3)
    fig.update_yaxes(title=config.UNIT, rangemode="tozero")
    return _style(fig, hovermode="x unified")


def monthly_box(air: pd.DataFrame, pollutant: str) -> go.Figure:
    fig = go.Figure(
        go.Box(
            x=[config.MONTHS[m - 1] for m in air["monat"]],
            y=air[pollutant],
            marker_color=config.POLLUTANT_COLORS[pollutant],
            line_width=1.5,
            boxpoints=False,
            name=config.POLLUTANTS[pollutant],
        )
    )
    fig.update_yaxes(title=config.UNIT, rangemode="tozero")
    fig.update_layout(showlegend=False)
    return _style(fig)


def monthly_bars(series: pd.Series, label: str, y_title: str) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=[config.MONTHS[m - 1] for m in series.index],
            y=series.values,
            marker_color=config.SINGLE_SERIES_COLOR,
            text=[str(v) if v else "" for v in series.values],
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(title=dict(text=label, font_size=14), showlegend=False, bargap=0.3)
    fig.update_yaxes(title=y_title, rangemode="tozero")
    return _style(fig, height=320)


def daily_strip(daily: pd.Series, threshold: float, label: str) -> go.Figure:
    """Tagesmittel als Balken; Tage über dem Schwellenwert hervorgehoben."""
    over = daily > threshold
    colors = [config.AQI_COLORS["sehr schlecht"] if o else config.SEQUENTIAL_BLUE[2] for o in over]
    fig = go.Figure(
        go.Bar(
            x=daily.index,
            y=daily.values,
            marker_color=colors,
            hovertemplate="%{x|%d.%m.%Y}: %{y:.1f} " + config.UNIT + "<extra></extra>",
        )
    )
    _add_reference_lines(fig, [(threshold, label)])
    fig.update_yaxes(title=config.UNIT, rangemode="tozero")
    fig.update_layout(showlegend=False, bargap=0.1)
    return _style(fig, height=320)


def scatter_with_fit(
    merged: pd.DataFrame, x: str, y: str, fit: tuple[float, float] | None
) -> go.Figure:
    data = merged[[x, y]].dropna()
    fig = go.Figure(
        go.Scatter(
            x=data[x],
            y=data[y],
            mode="markers",
            name="Tage",
            marker=dict(
                color=config.POLLUTANT_COLORS[y],
                size=8,
                opacity=0.7,
                line=dict(width=1, color="rgba(255,255,255,0.8)"),
            ),
            text=data.index.strftime("%d.%m.%Y"),
            hovertemplate="%{text}<br>%{x:.1f} → %{y:.1f} " + config.UNIT + "<extra></extra>",
        )
    )
    if fit is not None:
        slope, intercept = fit
        xs = [data[x].min(), data[x].max()]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=[slope * v + intercept for v in xs],
                mode="lines",
                name="Lineare Regression",
                line=dict(color=config.REFERENCE_LINE_COLOR, width=LINE_WIDTH, dash="dash"),
                hoverinfo="skip",
            )
        )
    fig.update_xaxes(title=config.WEATHER_COLUMNS[x])
    fig.update_yaxes(title=f"{config.POLLUTANTS[y]} ({config.UNIT}, Tagesmittel)")
    return _style(fig, height=420)


def correlation_bars(corr: pd.DataFrame) -> go.Figure:
    labels = [config.WEATHER_COLUMNS[c] for c in corr.columns]
    fig = go.Figure()
    for pollutant in corr.index:
        fig.add_trace(
            go.Bar(
                x=labels,
                y=corr.loc[pollutant],
                name=config.POLLUTANTS[pollutant],
                marker_color=config.POLLUTANT_COLORS[pollutant],
                hovertemplate="%{x}: ρ = %{y:.2f}<extra>" + config.POLLUTANTS[pollutant] + "</extra>",
            )
        )
    fig.add_hline(y=0, line=dict(color=config.REFERENCE_LINE_COLOR, width=1))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    fig.update_yaxes(title="Spearman-Korrelation ρ", range=[-1, 1])
    return _style(fig)


def grouped_bars(table: pd.DataFrame, pollutants: list[str], x_title: str) -> go.Figure:
    fig = go.Figure()
    x = [str(i) for i in table.index]
    for col in pollutants:
        fig.add_trace(
            go.Bar(
                x=x,
                y=table[col],
                name=config.POLLUTANTS[col],
                marker_color=config.POLLUTANT_COLORS[col],
                customdata=table.get("tage"),
                hovertemplate="%{x}: %{y:.1f} " + config.UNIT + " (%{customdata} Tage)<extra></extra>",
            )
        )
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    fig.update_xaxes(title=x_title)
    fig.update_yaxes(title=f"Mittelwert ({config.UNIT})", rangemode="tozero")
    return _style(fig, height=340)


def completeness_heatmap(table: pd.DataFrame) -> go.Figure:
    labels = {**config.POLLUTANTS, "aqi": "Luftqualitätsindex"}
    fig = go.Figure(
        go.Heatmap(
            z=table.T.values,
            x=[config.MONTHS[m - 1] for m in table.index],
            y=[labels[c] for c in table.columns],
            zmin=0,
            zmax=100,
            colorscale=[[i / (len(config.SEQUENTIAL_BLUE) - 1), c]
                        for i, c in enumerate(config.SEQUENTIAL_BLUE)],
            colorbar=dict(title="%", ticksuffix=" %"),
            text=table.T.round(0).astype(int).astype(str).values,
            texttemplate="%{text}",
            xgap=2,
            ygap=2,
            hovertemplate="%{y}, %{x}: %{z:.1f} % vorhanden<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    return _style(fig, height=260)
