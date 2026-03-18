import numpy as np
import streamlit as st
import pandas as pd

from .course_hcp import get_allcourses, handicap_request
from .graphs import plot_last_n


# THE PAGE DISPLAY --------------------------------------
def hcp_sim():
    st.title("🧮 New HCP Calculator")
    st.divider()

    current_handicap = st.session_state.df["Index Nuovo"][0]
    # best_handicap = st.session_state.df["Index Nuovo"].min()

    st.success(
        f"\n\n##### 🏌️ Tesserato {st.session_state.df['Tesserato'][0]}"
        + f"\n\n##### ⛳️ Current HCP: {current_handicap}  ⛳️",
    )

    # Playing handicap set to none
    st.session_state.playing_hcp = None

    # Make the request to get the course par
    handicap_request()

    # If handicap_request has been completed we can get to this part
    if st.session_state.playing_hcp:
        # Get all of the courses
        sr, cr, par_percorso = get_course_value(get_allcourses())

        new_sd, hcp_simulato = new_hcp(sr, cr, par_percorso)

        st.info(
            f"\n\n##### New Handicap: {hcp_simulato: .2f}"
            + f"\n\n##### Last Round SD: {new_sd: .2f}",
        )

        st.success(f"\n\n#### EGA Plot - 20 results plus new projected value")

        # Last 20 as an example
        plot_last_n(20, new_handicap=hcp_simulato)

    st.divider()
    st.markdown(
        """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
        unsafe_allow_html=True,
    )


# This needs to be fixed
def get_course_value(all_courses):
    # st.write("🔍 Available columns:", list(all_courses.columns))
    # st.write("🔍 Example row:", all_courses.head(1))
    # st.write("🔍 Looking for Circolo:", st.session_state.circolo)
    # st.write("🔍 Looking for Percorso:", st.session_state.percorso)

    filtered_df = all_courses[
        (all_courses["Circolo"] == st.session_state.circolo)
        & (all_courses["Percorso"] == st.session_state.percorso)
    ]

    if filtered_df.empty:
        st.error("Course not found")
        return

    tee = st.session_state.tee_color

    cr_column = f"CR {tee} Uomini"
    sr_column = f"Slope {tee} Uomini"

    if cr_column not in filtered_df.columns:
        cr_column = f"CR {tee} Donne"
        sr_column = f"Slope {tee} Donne"

    cr = filtered_df.iloc[0][cr_column]
    sr = filtered_df.iloc[0][sr_column]
    par_percorso = filtered_df.iloc[0]["PAR"]

    return sr, cr, par_percorso


# ---------------------------------------


def new_hcp(sr_percorso, cr_percorso, par_percorso):
    df = st.session_state.df.copy()

    # Clean SD column: convert empty/invalid to NaN
    df["SD"] = pd.to_numeric(df["SD"], errors="coerce")

    # Take the 20 most recent rounds with valid SD
    valid_sd_df = df.dropna(subset=["SD"]).head(20)

    if valid_sd_df.empty:
        st.error("❌ Not enough valid SDs for calculation.")
        return 0, 0

    # Take the SD values
    valid_results_SD = valid_sd_df["SD"].values.astype(float)

    # Best 8 of the latest 20 valid rounds
    best_8_SD = np.sort(valid_results_SD)[:8]

    # Compute new SD for the round being added
    new_sd = (113 / float(sr_percorso)) * (
        int(par_percorso)
        + int(st.session_state.playing_hcp)
        - (int(st.session_state.punti_stbl) - 36)
        - float(cr_percorso)
    )
    new_sd = round(new_sd, 1)

    # Include the new SD in the best 8 calculation
    best_8_SD = np.sort(np.append(best_8_SD, new_sd))[:8]

    # Compute simulated handicap
    hcp_simulato = round(np.mean(best_8_SD), 1)

    # st.write("✅ Debug:", {
    # "latest_20_valid_SD": valid_results_SD.tolist(),
    # "best_8_SD": best_8_SD.tolist(),
    # "new_sd": new_sd,
    # "hcp_simulato": hcp_simulato
    # })

    return new_sd, hcp_simulato
