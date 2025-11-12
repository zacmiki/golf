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
    st.write("🔍 Available columns:", list(all_courses.columns))
    st.write("🔍 Example row:", all_courses.head(1))
    st.write("🔍 Looking for Circolo:", st.session_state.circolo)
    st.write("🔍 Looking for Percorso:", st.session_state.percorso)

    filtered_df = all_courses[
        (all_courses["Circolo"] == st.session_state.circolo)
        & (all_courses["Percorso"] == st.session_state.percorso)
    ]

    st.write("🔍 Filter result:", filtered_df)

    if not filtered_df.empty:
        cr = filtered_df.iloc[0]["CR Giallo Uomini"]
        sr = filtered_df.iloc[0]["Slope Giallo Uomini"]
        par_percorso = filtered_df.iloc[0]["PAR"]
        return sr, cr, par_percorso
    else:
        return None


# ---------------------------------------

def new_hcp(sr_percorso, cr_percorso, par_percorso):
    df = st.session_state.df.copy()

    # --- Clean and prepare the SD column ---
    df["SD"] = (
        df["SD"]
        .astype(str)                      # Ensure all entries are strings
        .replace(r"^\s*$", np.nan, regex=True)  # Replace empty strings or spaces with NaN
    )
    df["SD"] = pd.to_numeric(df["SD"], errors="coerce")  # Convert to float
    filtered_df = df.dropna(subset=["SD"]).head(19)      # Take first 30 valid values

    if filtered_df.empty or len(filtered_df) < 8:
        st.error("❌ Non ci sono abbastanza valori SD validi per il calcolo.")
        return 0, 0

    valid_results_SD = filtered_df["SD"].values.astype(float)
    migliori_8 = np.sort(valid_results_SD)[:8]

    # --- Compute new SD ---
    new_sd = (113 / float(sr_percorso)) * (
        int(par_percorso)
        + int(st.session_state.playing_hcp)
        - (int(st.session_state.punti_stbl) - 36)
        - float(cr_percorso)
    )

    new_sd = round(new_sd, 1)

    # --- Combine old and new SD values ---
    migliori_8 = np.append(migliori_8, new_sd)
    best_8_SD = np.sort(migliori_8)[:8]

    # --- Compute new handicap ---
    hcp_simulato = round(np.mean(best_8_SD), 1)

    # Optional debug output
    st.write("✅ Debug:", {
        "new_sd": new_sd,
        "best_8_SD": best_8_SD.tolist(),
        "hcp_simulato": hcp_simulato
    })

    return new_sd, hcp_simulato
