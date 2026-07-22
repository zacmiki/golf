from __future__ import annotations

import streamlit as st

from .course_hcp import course_details, select_course
from .federgolf_client import FederGolfError
from .ui import current_handicap


def playing_hcp() -> None:
    st.title("⛳️ Course Handicap Calculator")
    st.caption(
        "Choose a course and tee to see how many strokes you receive. "
        "Your current Handicap Index is already filled in."
    )
    with st.container(border=True):
        st.subheader("Your course and tee")
        selection = select_course("playing")
        if selection is None:
            return
        handicap = st.number_input(
            ":green[Your Handicap Index]",
            min_value=-12.0,
            max_value=54.0,
            value=current_handicap(st.session_state.df),
            step=0.1,
        )
        calculate = st.button(
            "Calculate my handicap", type="primary", width="stretch"
        )
    if not calculate:
        return
    try:
        result = course_details(selection, handicap)
    except FederGolfError as exc:
        st.error(str(exc))
        return
    st.success(f"## ⛳ Your Course Handicap is **{result.course_handicap}**")
    st.caption("This is the number of strokes you receive for the selected tee.")
    with st.expander("Course details"):
        rating, slope, tee = st.columns(3)
        rating.metric("Course Rating", f"{result.course_rating:.1f}")
        slope.metric("Slope Rating", f"{result.slope_rating:.0f}")
        tee.metric("Tee", result.tee)
