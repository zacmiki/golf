from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

from .course_hcp import get_allcourses, handicap_request, TEE_COLORS, VALID_ROUNDS
from .graphs import plot_last_n

BEST_8_COUNT = 8


def hcp_sim() -> None:
    st.title("🧮 New HCP Calculator")
    st.divider()

    current_handicap = st.session_state.df["Index Nuovo"][0]
    st.success(
        f"\n\n##### 🏌️ Tesserato {st.session_state.df['Tesserato'][0]}"
        + f"\n\n##### ⛳️ Current HCP: {current_handicap:.1f}  ⛳️",
    )

    st.session_state.playing_hcp = None

    handicap_request()

    if st.session_state.playing_hcp:
        sr, cr, par = get_course_value(get_allcourses())
        if sr is None:
            return

        new_sd, hcp_simulato = new_hcp(sr, cr, par)

        st.info(
            f"\n\n##### New Handicap: {hcp_simulato:.2f}"
            + f"\n\n##### Last Round SD: {new_sd:.2f}",
        )

        st.success("#### EGA Plot - 20 results plus new projected value")
        plot_last_n(VALID_ROUNDS, new_handicap=hcp_simulato)

    st.divider()
    st.markdown(
        """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
        unsafe_allow_html=True,
    )


def get_course_value(
    all_courses: pd.DataFrame,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if all_courses.empty:
        st.error("No course data available.")
        return None, None, None

    filtered = all_courses[
        (all_courses["Circolo"] == st.session_state.circolo)
        & (all_courses["Percorso"] == st.session_state.percorso)
    ]

    if filtered.empty:
        st.error("Course not found.")
        return None, None, None

    tee = getattr(st.session_state, "tee_color", st.session_state.percorso)

    cr_col = f"CR {tee} Uomini"
    sr_col = f"Slope {tee} Uomini"

    if cr_col not in filtered.columns:
        cr_col = f"CR {tee} Donne"
        sr_col = f"Slope {tee} Donne"

    if cr_col not in filtered.columns:
        st.error(f"No rating found for tee '{tee}'.")
        return None, None, None

    cr = float(filtered.iloc[0][cr_col])
    sr = float(filtered.iloc[0][sr_col])
    par = float(filtered.iloc[0]["PAR"])

    return sr, cr, par


def new_hcp(
    sr_percorso: float, cr_percorso: float, par_percorso: float
) -> tuple[float, float]:
    df = st.session_state.df.copy()
    df["SD"] = pd.to_numeric(df["SD"], errors="coerce")

    if "Data" in df.columns:
        df = df.sort_values("Data", ascending=False)

    valid_sd = df["SD"].dropna().head(VALID_ROUNDS).values.astype(float)

    if len(valid_sd) == 0:
        st.error("Not enough valid SDs for calculation.")
        return 0.0, 0.0

    punti = st.session_state.punti_stbl
    playing_hcp = st.session_state.playing_hcp

    punti = float(punti)
    playing_hcp = float(playing_hcp)

    adjusted_score = par_percorso + playing_hcp - (punti - 36)
    new_sd = (113 / sr_percorso) * (adjusted_score - cr_percorso)
    new_sd = round(new_sd, 1)

    all_sd = np.append(valid_sd, new_sd)
    best_8 = np.sort(all_sd)[:BEST_8_COUNT]

    hcp_simulato = round(float(np.mean(best_8)), 1)
    return new_sd, hcp_simulato
