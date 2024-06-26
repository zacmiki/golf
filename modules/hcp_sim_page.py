import numpy as np
import streamlit as st

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
        sr, cr, per_percorso = get_course_value(get_allcourses())

        new_sd, hcp_simulato = new_hcp(sr, cr, per_percorso)
        
        st.info(
        f"\n\n##### Handicap Calcolato: {hcp_simulato: .2f}"
        + f"\n\n##### SD Calcolato: {new_sd: .2f}",
        )

        st.success(
        f"\n\n#### EGA Plot - 20 results plus new projected value"
        )
        
        # Last 20 as an example
        plot_last_n(20, plot_type="line", new_handicap=hcp_simulato)

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
    filtered_df = all_courses[
        (all_courses["Circolo"] == st.session_state.circolo)
        & (all_courses["Percorso"] == st.session_state.percorso)
    ]

    if not filtered_df.empty:
        cr = filtered_df.iloc[0]["CR Giallo Uomini"]
        sr = filtered_df.iloc[0]["Slope Giallo Uomini"]
        par_percorso = filtered_df.iloc[0]["PAR"]

        return sr, cr, par_percorso

    else:
        return None


# ---------------------------------------


# New HCP Calculator --------
def new_hcp(sr_percorso, cr_percorso, par_percorso):

    #filtered_df = st.session_state.df.dropna(subset=["SD"]).head(20)
    filtered_df = st.session_state.df.dropna(subset=["SD"]).head(19)
    valid_results_SD = filtered_df["SD"].values

    migliori_8 = np.sort(valid_results_SD)[:8]

    new_sd = (113 / float(sr_percorso)) * (
        int(par_percorso)
        + int(st.session_state.playing_hcp)
        - (int(st.session_state.punti_stbl) - 36)
        - float(cr_percorso)
    )
    # Taking the SD rounded to the first decimal according to Royal & Ancient
    new_sd = round(new_sd, 1)

    migliori_8 = np.append(migliori_8, new_sd)
    best_8_SD = np.sort(migliori_8)[:8]
    
    # Calculating the new HCP by taking the 96% of the avg(best 8)  
    hcp_simulato = np.mean(best_8_SD)
    hcp_simulato = round(hcp_simulato, 1)
    # --------------------------------------- Debugging String ------------------------
    #st.write(f"Temp String to verify calculation {new_sd}, {best_8_SD}, {hcp_simulato}")
    # --------------------------------------- Debugging String ------------------------

    return new_sd, hcp_simulato
