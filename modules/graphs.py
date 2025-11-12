import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm


# ---------------- Code for the first page ---------------
def fig_companion():
    plot_type_mapping = {
        "Line Area Plot": "line",
        "Bar Chart": "bar",
        "Scatter Plot": "scatter",
    }

    relevant_columns = ["Data", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    strippeddf = st.session_state.df[relevant_columns].copy()
    strippeddf = strippeddf.rename(columns={"Index Nuovo": "New EGA"})
    strippeddf = strippeddf.rename(columns={"Data": "Date"})

    st.title("Official FederGolf Results ⛳️")
    st.divider()

    current_handicap = st.session_state.df["Index Nuovo"][0]
    best_handicap = st.session_state.df["Index Nuovo"].min()

    st.markdown(f"##### Tesserato 🏌️ {st.session_state.df['Tesserato'][0]}")
    st.success(
        f"Your Current HCP is: {current_handicap} - Best handicap: {best_handicap}",
        icon="🏌️",
    )
    st.markdown(f"#### Slider to select the number of results")

    # User has already logged in, display the handicap visualizer
    # slider_value = st.slider("Select the number of results:", 1, 100, 20)
    slider_value = st.slider(
        "Select number of results", 1, 100, 20, label_visibility="collapsed"
    )
    # slider_value = st.slider("", 1, 100, 20)
    st.session_state.slider_value = slider_value

    # st.subheader("Plot of your Handicap progression")
    st.markdown(f"##### Your handicap progression: last {slider_value} results:")
    plot_type_options = list(plot_type_mapping.keys())
    selected_plot_type = st.selectbox("Choose a plot type", plot_type_options)

    plot_last_n(
        slider_value, plot_type=plot_type_mapping.get(selected_plot_type, "line")
    )

    # st.header("Strokes in the Last {} Rounds".format(slider_value))
    st.subheader(f"Strokes Distribution [Last {slider_value} Rounds]")
    plot_gaussian = st.checkbox("Plot Gaussian")
    histo_n(plot_gaussian, slider_value)

    # st.subheader("Last Rounds Data [Downloadable CSV]")
    st.markdown(f"### Detail of the last {slider_value} rounds:")

    # st.write(df.iloc[:slider_value])
    st.write(strippeddf.iloc[:slider_value])


# Cache this result to avoid recomputing it every time
#@st.cache_data
def plot_last_n(n: int, plot_type="line", new_handicap=None):
    import matplotlib.pyplot as plt
    import pandas as pd

    fig, ax = plt.subplots(figsize=(12, 7))

    # Step 1: Take latest n valid rounds (SD not NaN)
    last_n_results = st.session_state.df.dropna(subset=["SD"]).head(n).copy()

    # Step 2: Reverse for chronological plotting (oldest → newest)
    last_n_results = last_n_results.iloc[::-1].reset_index(drop=True)

    # Ensure date column is string
    last_n_results["Data"] = last_n_results["Data"].astype(str)

    # Append new handicap if provided
    if new_handicap is not None:
        new_row = pd.DataFrame({"Data": ["New"], "Index Nuovo": [new_handicap]})
        last_n_results = pd.concat([last_n_results, new_row], ignore_index=True)

    x_values = last_n_results["Data"]
    y_values = last_n_results["Index Nuovo"]

    # Plot
    ax.plot(x_values, y_values, linestyle="-", marker="o", markersize=8)
    ax.fill_between(x_values, y_values, color="skyblue", alpha=0.3)
    ax.grid(True)

    # Highlight new handicap if provided
    if new_handicap is not None:
        ax.plot(x_values.iloc[-1], y_values.iloc[-1], "ro", markersize=12)
        ax.axvline(x=len(last_n_results)-1, color="red", linestyle="--", linewidth=2)

    ax.set_title(f"EGA Handicap - Last {n} Valid Rounds", fontsize=16)
    ax.set_ylabel("Index Nuovo", fontsize=14)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(y_values.min() - 0.2, max(y_values.max(), new_handicap if new_handicap else y_values.max()) + 0.2)

    plt.tight_layout()
    st.pyplot(fig)

