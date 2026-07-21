from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from .course_hcp import (
    VALID_ROUNDS,
    course_par,
    course_rating,
    select_course,
)
from .federgolf_client import FederGolfError
from .rounds_page import PLOT_CONFIG, handicap_chart
from .ui import current_handicap, player_overview

BEST_8_COUNT = 8
SCENARIO_PRESETS = (33, 36, 38)


@dataclass(frozen=True)
class Simulation:
    score_differential: float
    handicap: float


def simulate_handicap(
    df: pd.DataFrame,
    current_index: float,
    slope: float,
    course_rating: float,
    par: float,
    stableford_points: float,
) -> Simulation:
    """Project one new round from a Stableford score and course ratings."""
    recent = df.copy()
    recent["_date"] = pd.to_datetime(recent["Data"], errors="coerce")
    recent = recent.sort_values("_date", ascending=False, kind="stable")
    differentials = (
        pd.to_numeric(recent["SD"], errors="coerce")
        .dropna()
        .head(VALID_ROUNDS - 1)
        .to_numpy(dtype=float)
    )
    if differentials.size == 0:
        raise ValueError("At least one valid Score Differential is required")

    adjusted_score = int(par + current_index - (stableford_points - 36))
    new_sd = round((113 / slope) * (adjusted_score - course_rating), 1)
    best = np.sort(np.append(differentials, new_sd))[:BEST_8_COUNT]
    return Simulation(new_sd, round(float(best.mean()), 1))


def hcp_sim() -> None:
    df = st.session_state.df
    current = current_handicap(df)
    st.title("🧮 Handicap Simulator")
    st.caption("Project how one new 18-hole Stableford result may affect your Index.")
    player_overview(df)

    selection = select_course("simulation")
    if selection is None:
        return
    par = course_par(selection)
    if par is None:
        st.error("FederGolf did not publish a Par value for this course.")
        return
    try:
        details = course_rating(selection)
    except FederGolfError as exc:
        st.error(str(exc))
        return

    points = st.number_input(
        "Stableford score", min_value=1, max_value=54, value=36, step=1
    )
    try:
        projection = simulate_handicap(
            df,
            current,
            details.slope_rating,
            details.course_rating,
            par,
            points,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    projected, differential = st.columns(2)
    projected.metric(
        "Calculated New Handicap",
        f"{projection.handicap:.1f}",
        delta=f"{projection.handicap - current:+.1f}",
        delta_color="inverse",
    )
    differential.metric("Score Differential", f"{projection.score_differential:.1f}")

    st.subheader("What if?")
    columns = st.columns(len(SCENARIO_PRESETS))
    for column, scenario_points in zip(columns, SCENARIO_PRESETS, strict=True):
        scenario = simulate_handicap(
            df,
            current,
            details.slope_rating,
            details.course_rating,
            par,
            scenario_points,
        )
        column.metric(
            f"{scenario_points} points",
            f"HCP {scenario.handicap:.1f}",
            delta=f"{scenario.handicap - current:+.1f}",
            delta_color="inverse",
        )
        column.caption(f"Score Differential {scenario.score_differential:.1f}")

    figure = handicap_chart(df, VALID_ROUNDS, projection.handicap)
    st.plotly_chart(figure, width="stretch", config=PLOT_CONFIG)
