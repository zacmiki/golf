from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .hcp_manager_page import handicap_window
from .ui import player_overview

PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def official_rounds() -> None:
    df = st.session_state.df
    st.title("Official FederGolf Results ⛳️")
    player_overview(df)

    maximum = min(100, len(df))
    count = st.slider(
        "Number of results",
        min_value=1,
        max_value=maximum,
        value=min(30, maximum),
    )
    st.plotly_chart(handicap_chart(df, count), width="stretch", config=PLOT_CONFIG)

    show_curve = st.checkbox("Show Gaussian fit", value=True)
    distribution = strokes_distribution(df, count, show_curve)
    if distribution is not None:
        st.plotly_chart(distribution, width="stretch", config=PLOT_CONFIG)

    columns = ["Data", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    counting_positions = counting_round_positions(df)
    positioned = df.reset_index(drop=True)
    table = positioned[[column for column in columns if column in df]].head(count)
    st.subheader(f"Last {count} rounds")
    st.caption("🟩 Green rounds are the 8 scores currently counting for your Handicap.")

    def highlight_counting(row: pd.Series) -> list[str]:
        color = (
            "background-color: rgba(0, 128, 0, 0.55)"
            if row.name in counting_positions
            else ""
        )
        return [color] * len(row)

    st.dataframe(
        table.style.apply(highlight_counting, axis=1),
        hide_index=True,
        width="stretch",
        column_config={
            column: st.column_config.NumberColumn(format="%.1f")
            for column in ["Stbl", "AGS", "SD", "Index Nuovo"]
            if column in table
        },
    )


def counting_round_positions(df: pd.DataFrame) -> set[int]:
    positioned = df.reset_index(drop=True).assign(_position=lambda frame: frame.index)
    window = handicap_window(positioned)
    return set(window.loc[window["Counting"], "_position"])


def recent_rounds(df: pd.DataFrame, count: int) -> pd.DataFrame:
    return df.dropna(subset=["SD", "Index Nuovo"]).head(count).iloc[::-1].copy()


def handicap_chart(
    df: pd.DataFrame, count: int, projected_handicap: float | None = None
) -> go.Figure:
    rounds = recent_rounds(df, count).reset_index(drop=True)
    if rounds.empty:
        return go.Figure().update_layout(title="No handicap rounds available")
    x = list(range(1, len(rounds) + 1))
    figure = go.Figure(
        go.Scatter(
            x=x,
            y=rounds["Index Nuovo"],
            mode="lines+markers",
            name="Handicap",
            line={"color": "#2E86AB", "width": 3},
            marker={"size": 9},
            customdata=rounds[["Data", "Gara"]].to_numpy(),
            hovertemplate=(
                "Round %{x}<br>%{customdata[0]}<br>%{customdata[1]}"
                "<br>Handicap %{y:.1f}<extra></extra>"
            ),
        )
    )
    values = rounds["Index Nuovo"].tolist()
    if projected_handicap is not None and values:
        figure.add_trace(
            go.Scatter(
                x=[x[-1], x[-1] + 1],
                y=[values[-1], projected_handicap],
                mode="lines+markers",
                name="Projection",
                line={"color": "#E63946", "dash": "dot"},
                marker={"size": 12, "symbol": "star"},
            )
        )
        values.append(projected_handicap)
        x.append(x[-1] + 1)

    figure.update_layout(
        title=f"Handicap progression · last {count} valid rounds",
        xaxis={"title": "Round", "tickvals": x},
        yaxis={
            "title": "Handicap Index",
            "range": [min(values) - 1, max(values) + 1],
        },
        hovermode="x unified",
        height=430,
        margin={"l": 20, "r": 20, "t": 60, "b": 30},
        showlegend = False,
    )
    figure.update_xaxes(fixedrange=True)
    figure.update_yaxes(fixedrange=True)
    
    return figure


def strokes_distribution(
    df: pd.DataFrame, count: int, show_curve: bool
) -> go.Figure | None:
    if "AGS" not in df:
        return None
    values = df["AGS"].replace(0, np.nan).dropna().head(count).astype(float)
    if values.empty:
        return None

    lower, upper = float(values.min()), float(values.max())
    figure = go.Figure(
        go.Histogram(
            x=values,
            xbins={"start": lower - 2, "end": upper + 4, "size": 3},
            name="Strokes",
            marker={"color": "rgba(100, 149, 237, 0.7)"},
        )
    )
    standard_deviation = float(values.std(ddof=0))
    if show_curve and standard_deviation > 0:
        mean = float(values.mean())
        smooth = np.linspace(lower - 5, upper + 5, 300)
        density = (
            np.exp(-0.5 * ((smooth - mean) / standard_deviation) ** 2)
            / (standard_deviation * np.sqrt(2 * np.pi))
            * len(values)
            * 4
        )
        figure.add_trace(
            go.Scatter(
                x=smooth,
                y=density,
                mode="lines",def strokes_distribution(
    df: pd.DataFrame, count: int, show_curve: bool
) -> go.Figure | None:
    if "AGS" not in df:
        return None

    values = df["AGS"].replace(0, np.nan).dropna().head(count).astype(float)

    if values.empty:
        return None

    lower = float(values.min())
    upper = float(values.max())

    figure = go.Figure(
        go.Histogram(
            x=values,
            xbins={
                "start": lower - 2,
                "end": upper + 3,
                "size": 3,
            },
            marker={
                "color": "rgba(100,149,237,0.75)",
            },
            showlegend=False,
            hovertemplate="%{x:.0f} strokes<br>%{y} rounds<extra></extra>",
        )
    )

    std = float(values.std(ddof=0))

    if show_curve and std > 0:
        mean = float(values.mean())

        smooth = np.linspace(lower - 5, upper + 5, 300)

        density = (
            np.exp(-0.5 * ((smooth - mean) / std) ** 2)
            / (std * np.sqrt(2 * np.pi))
            * len(values)
            * 3
        )

        figure.add_trace(
            go.Scatter(
                x=smooth,
                y=density,
                mode="lines",
                line={
                    "color": "#E63946",
                    "dash": "dash",
                    "width": 3,
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

        figure.add_vline(
            x=mean,
            line_dash="dash",
            line_color="#E63946",
            line_width=2,
        )

        figure.add_annotation(
            x=mean,
            y=0.97,
            xref="x",
            yref="paper",
            text=f"μ = {mean:.1f}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E63946",
            borderwidth=1,
            font=dict(size=12),
        )

    figure.update_layout(
        title=f"Gross-score distribution · last {count} rounds",
        xaxis_title="Adjusted Gross Score",
        yaxis_title="Frequency",
        height=390,
        margin=dict(l=20, r=20, t=60, b=30),
        showlegend=False,
        hovermode="closest",
    )

    figure.update_xaxes(
        fixedrange=True,
        dtick=3,
    )

    figure.update_yaxes(
        fixedrange=True,
    )

    return figure
