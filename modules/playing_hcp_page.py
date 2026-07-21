from __future__ import annotations

import streamlit as st

from .course_hcp import course_details, select_course
from .federgolf_client import FederGolfError
from .ui import current_handicap


def playing_hcp() -> None:
    st.title("⛳️ Course Handicap Calculator")
    st.caption(
        "Your current Handicap Index is used by default. Change it to explore "
        "another value."
    )
    selection = select_course("playing")
    if selection is None:
        return

    handicap = st.number_input(
        "Handicap Index",
        min_value=-12.0,
        max_value=54.0,
        value=current_handicap(st.session_state.df),
        step=0.1,
    )
    if not st.button("Compute Course Handicap"):
        return
    try:
        result = course_details(selection, handicap)
    except FederGolfError as exc:
        st.error(str(exc))
        return
    st.info(
        f"#### Course Handicap: {result.course_handicap}\n"
        f"CR {result.course_rating:.1f} · Slope {result.slope_rating:.0f} · {result.tee}"
    )
