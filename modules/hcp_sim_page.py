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

    tee = getattr(st.session_state, 'tee_color', st.session_state.percorso)
    #tee = st.session_state.percorso

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

    df["SD"] = pd.to_numeric(df["SD"], errors="coerce")

    # ensure correct ordering (latest first)
    if "Data" in df.columns:
        df = df.sort_values("Data", ascending=False)

    valid_sd = df["SD"].dropna().head(20).values.astype(float)

    if len(valid_sd) == 0:
        st.error("❌ Not enough valid SDs for calculation.")
        return 0, 0

    # correct WHS adjusted gross score
    punti = st.session_state.punti_stbl
    playing_hcp = st.session_state.playing_hcp
    
    punti = float(punti)
    playing_hcp = float(playing_hcp)
    par_percorso = float(par_percorso)
    
    adjusted_score = par_percorso + playing_hcp - (punti - 36)
    
    new_sd = (113 / float(sr_percorso)) * (adjusted_score - float(cr_percorso))
    new_sd = round(new_sd, 1)

    # WHS logic: take last 20 + new → best 8
    all_sd = np.append(valid_sd, new_sd)
    best_8 = np.sort(all_sd)[:8]

    hcp_simulato = round(np.mean(best_8), 1)

    return new_sd, hcp_simulato
