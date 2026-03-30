from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm


def fig_companion() -> None:
    relevant_columns = ["Data", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    strippeddf = st.session_state.df[relevant_columns].copy()
    strippeddf = strippeddf.rename(columns={"Index Nuovo": "New EGA"})
    strippeddf = strippeddf.rename(columns={"Data": "Date"})

    st.title("Official FederGolf Results ⛳️")
    st.divider()

    current_handicap = st.session_state.df["Index Nuovo"][0]
    best_handicap = st.session_state.df["Index Nuovo"].min()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### 🏌️ {st.session_state.df['Tesserato'][0]}")
    with col2:
        st.success(
            f"Current HCP: **{current_handicap:.1f}** | Best: **{best_handicap:.1f}**"
        )

    st.markdown("#### Select number of results")

    slider_value = st.slider(
        "Select number of results", 1, 100, 20, label_visibility="collapsed"
    )
    st.session_state.slider_value = slider_value

    st.markdown(f"##### Handicap Progression: last {slider_value} results")
    plot_last_n(slider_value)

    st.markdown(f"#### Strokes Distribution [Last {slider_value} Rounds]")
    col1, col2 = st.columns([1, 3])
    with col1:
        plot_gaussian = st.checkbox("Show Gaussian Fit", value=True)
    with col2:
        pass
    histo_n(plot_gaussian, slider_value)

    st.markdown("#### Handicap Progression by Date")
    plot_handicap_by_date(slider_value)

    st.markdown(f"### Detail of the last {slider_value} rounds:")
    st.dataframe(
        strippeddf.iloc[:slider_value].style.format(precision=1),
        use_container_width=True,
        hide_index=True,
    )


def plot_last_n(n: int, new_handicap: Optional[float] = None) -> None:
    last_n_results = st.session_state.df.dropna(subset=["SD"]).head(n).copy()
    last_n_results = last_n_results.iloc[::-1].reset_index(drop=True)

    fig = go.Figure()

    round_numbers = list(range(1, len(last_n_results) + 1))

    fig.add_trace(
        go.Scatter(
            x=round_numbers,
            y=last_n_results["Index Nuovo"],
            mode="lines+markers",
            name="Handicap",
            line=dict(color="#2E86AB", width=3),
            marker=dict(size=10, color="#2E86AB", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(46, 134, 171, 0.1)",
            hovertemplate="Round %{x}<br>Handicap: %{y:.1f}<extra></extra>",
        )
    )

    if new_handicap is not None:
        fig.add_trace(
            go.Scatter(
                x=[len(round_numbers), len(round_numbers) + 1],
                y=[last_n_results["Index Nuovo"].iloc[-1], new_handicap],
                mode="lines+markers",
                name="Simulated HCP",
                line=dict(color="#E63946", width=2, dash="dot"),
                marker=dict(size=12, color="#E63946", symbol="star"),
                fill="tozeroy",
                fillcolor="rgba(50, 205, 50, 0.25)",
                hovertemplate="Round %{x}<br>Handicap: %{y:.1f}<extra></extra>",
            )
        )

        y_min = min(last_n_results["Index Nuovo"].min(), new_handicap) - 1
        y_max = max(last_n_results["Index Nuovo"].max(), new_handicap) + 1
        x_max = len(round_numbers) + 1
    else:
        y_min = last_n_results["Index Nuovo"].min() - 1
        y_max = last_n_results["Index Nuovo"].max() + 1
        x_max = len(round_numbers)

    fig.update_layout(
        title=dict(text=f"EGA Handicap - Last {n} Valid Rounds", font=dict(size=18)),
        yaxis=dict(title="EGA Handicap", range=[y_min, y_max], gridcolor="lightgray"),
        xaxis=dict(
            title="Round",
            range=[0.5, x_max + 0.5],
            tickvals=list(range(1, x_max + 1)),
            gridcolor="lightgray",
        ),
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False,
        margin=dict(t=60, b=60),
        height=450,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom",
                "zoomIn",
                "zoomOut",
                "pan",
                "autoScale",
                "resetScale",
                "select2d",
                "lasso2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
        },
    )


def histo_n(plot_gaussian: bool = True, num_results: int = 100) -> None:
    filtered_data = st.session_state.df["AGS"].dropna().replace(0, np.nan).dropna()
    last_n_values = filtered_data.iloc[:num_results]

    max_value = int(last_n_values.max())
    min_value = int(last_n_values.min())
    bins = list(range(70, max_value + 4, 4))

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=last_n_values,
            xbins=dict(start=70, end=max_value + 4, size=4),
            marker=dict(
                color="rgba(100, 149, 237, 0.7)", line=dict(color="white", width=1)
            ),
            name="Strokes",
            hovertemplate="Strokes: %{x}<br>Count: %{y}<extra></extra>",
        )
    )

    if plot_gaussian:
        mu, std = norm.fit(last_n_values)
        x_smooth = np.linspace(min_value - 10, max_value + 10, 500)
        gaussian_curve = norm.pdf(x_smooth, mu, std) * len(last_n_values) * 4

        fig.add_trace(
            go.Scatter(
                x=x_smooth,
                y=gaussian_curve,
                mode="lines",
                name=f"Gaussian (μ={mu:.1f})",
                line=dict(color="#E63946", width=2, dash="dash"),
                hovertemplate="Strokes: %{x:.1f}<br>Freq: %{y:.1f}<extra></extra>",
            )
        )

        annotations = [
            dict(
                x=mu,
                y=max(gaussian_curve) / 2,
                xref="x",
                yref="y",
                text=f"Avg Strokes = {mu:.1f}",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=40,
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=12, color="black"),
            )
        ]
    else:
        annotations = []

    x_range_min = min_value - 5
    x_range_max = max_value + 5

    fig.update_layout(
        title=dict(
            text=f"Strokes Distribution - Last {num_results} Rounds", font=dict(size=16)
        ),
        xaxis=dict(
            title="Strokes per Round",
            gridcolor="lightgray",
            range=[x_range_min, x_range_max],
        ),
        yaxis=dict(title="Frequency", gridcolor="lightgray"),
        plot_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=60),
        height=400,
        bargap=0.1,
        annotations=annotations,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom",
                "zoomIn",
                "zoomOut",
                "pan",
                "autoScale",
                "resetScale",
                "select2d",
                "lasso2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
        },
    )


def plot_handicap_by_date(n: int, new_handicap: Optional[float] = None) -> None:
    last_n_results = st.session_state.df.dropna(subset=["SD"]).head(n).copy()
    last_n_results = last_n_results.iloc[::-1].reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=last_n_results["Data"],
            y=last_n_results["Index Nuovo"],
            mode="lines+markers",
            name="EGA Handicap",
            line=dict(color="#2E86AB", width=3),
            marker=dict(size=8, color="#2E86AB", line=dict(color="white", width=2)),
            hovertemplate="Date: %{x}<br>EGA Handicap: %{y:.1f}<extra></extra>",
        )
    )

    y_min = last_n_results["Index Nuovo"].min() - 1
    y_max = last_n_results["Index Nuovo"].max() + 1

    fig.update_layout(
        title=dict(text="Handicap Progression", font=dict(size=18)),
        yaxis=dict(title="EGA Handicap", range=[y_min, y_max], gridcolor="lightgray"),
        xaxis=dict(
            title="Date",
            tickangle=45,
            gridcolor="lightgray",
        ),
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False,
        margin=dict(t=60, b=60),
        height=400,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom",
                "zoomIn",
                "zoomOut",
                "pan",
                "autoScale",
                "resetScale",
                "select2d",
                "lasso2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
        },
    )


def plot_scenarios_comparison(
    n: int,
    scenario_hcps: list[float],
    scenario_labels: list[str],
    scenario_colors: list[str],
) -> None:
    last_n_results = st.session_state.df.dropna(subset=["SD"]).head(n).copy()
    last_n_results = last_n_results.iloc[::-1].reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(last_n_results) + 1)),
            y=last_n_results["Index Nuovo"],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#2E86AB", width=3),
            marker=dict(size=10, color="#2E86AB", line=dict(color="white", width=2)),
            hovertemplate="Round %{x}<br>HCP: %{y:.1f}<extra></extra>",
        )
    )

    n_rounds = len(last_n_results)
    all_hcps = list(last_n_results["Index Nuovo"]) + scenario_hcps
    y_min = min(all_hcps) - 1
    y_max = max(all_hcps) + 1

    scenario_x_start = n_rounds + 1
    for i, (hcp, label) in enumerate(zip(scenario_hcps, scenario_labels)):
        x_pos = scenario_x_start + i * 0.3
        fig.add_trace(
            go.Scatter(
                x=[x_pos],
                y=[hcp],
                mode="markers",
                name=f"⛳️ {label}",
                marker=dict(
                    size=16,
                    color=scenario_colors[i],
                    symbol="circle",
                    line=dict(color="white", width=2),
                ),
                hovertemplate=f"{label}<br>New HCP: {hcp:.1f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text="Handicap Progression with Scenario Projections", font=dict(size=18)
        ),
        yaxis=dict(title="EGA Handicap", range=[y_min, y_max], gridcolor="lightgray"),
        xaxis=dict(
            title="Round",
            range=[0.5, scenario_x_start + len(scenario_hcps) * 0.3 + 0.5],
            tickvals=list(range(1, n_rounds + 1)),
            ticktext=[str(x) for x in range(1, n_rounds + 1)],
            gridcolor="lightgray",
        ),
        plot_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        margin=dict(t=60, b=60),
        height=450,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "modeBarButtonsToRemove": [
                "zoom",
                "zoomIn",
                "zoomOut",
                "pan",
                "autoScale",
                "resetScale",
                "select2d",
                "lasso2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
        },
    )
