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

    # Take latest n valid rounds (SD not NaN)
    last_n_results = st.session_state.df.dropna(subset=["SD"]).head(n).copy()
    last_n_results["Data"] = last_n_results["Data"].astype(str)

    # Append new handicap if provided
    if new_handicap is not None:
        new_row = pd.DataFrame({"Data": ["New"], "Index Nuovo": [new_handicap]})
        last_n_results = pd.concat([new_row, last_n_results], ignore_index=True)

    x_values = last_n_results["Data"]
    y_values = last_n_results["Index Nuovo"]

    ax.plot(x_values, y_values, linestyle="-", marker="o", markersize=8)
    ax.fill_between(x_values, y_values, color="skyblue", alpha=0.3)
    ax.grid(True)

    # Highlight new handicap
    if new_handicap is not None:
        ax.plot(x_values.iloc[0], y_values.iloc[0], "ro", markersize=12)
        ax.axvline(x=0, color="red", linestyle="--", linewidth=2)

    ax.set_title(f"EGA Handicap - Last {n} Valid Rounds", fontsize=16)
    ax.set_ylabel("Index Nuovo", fontsize=14)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(y_values.min() - 0.2, max(y_values.max(), new_handicap if new_handicap else y_values.max()) + 0.2)

    plt.tight_layout()
    st.pyplot(fig)


# ------- Histogram with Gaussian Fit
#st.cache_data
def histo_n(plot_gaussian: bool = True, num_results: int = 100) -> None:
    # Filter out non-finite values (None and zeros) from the DataFrame
    
    filtered_data = st.session_state.df["AGS"].dropna().replace(0, np.nan).dropna()

    # Create a figure with a custom size
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get the last num_results values from filtered_data
    last_n_values = filtered_data.iloc[:num_results]

    # Calculate the maximum and minimum values of last_n_values
    max_value = last_n_values.max()
    min_value = last_n_values.min()

    # Create a histogram with fixed range bins and custom bin width
    bins = range(70, int(max_value) + 4, 4)

    hist, bins, _ = ax.hist(
        last_n_values,
        bins=bins,
        edgecolor="black",
        alpha=0.5,
        color="lightblue",
    )

    # Fit a Gaussian distribution to the last_n_values
    mu, std = norm.fit(last_n_values)

    # Generate points along the Gaussian curve for smoother plotting
    x_smooth = np.linspace(min_value - 10, max_value + 10, 1000)
    gaussian_curve = (
        norm.pdf(x_smooth, mu, std) * len(last_n_values) * np.diff(bins)[0]
    )  # scaling by bin width

    # Plot the Gaussian fit if the user wants to
    if plot_gaussian:
        ax.plot(x_smooth, gaussian_curve, "r--", linewidth=2)

    # Add labels and title
    ax.set_xlabel("Strokes per Round Distribution", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(
        f"Strokes per round in the Last {num_results} FIG Tournaments", fontsize=12
    )

    # Show the grid
    ax.grid(False)  # Remove grid lines

    # Show both major and minor ticks
    ax.minorticks_off()  # Turn off minor ticks

    # Customize grid for major ticks
    ax.grid(True, which="major", linestyle="-", linewidth=0.5)  # Adjust grid style

    if plot_gaussian:
        # Print the center value of the Gaussian
        ax.text(
            mu,
            max(gaussian_curve) * 0.5,
            f"Center: {mu:.2f}",
            color="r",
            ha="center",
            fontsize="x-large",
            fontweight = "demibold"
        )
        # Add a legend for the Gaussian fit
        ax.legend(["Gaussian Fit"], loc="upper right", fontsize=8)

    # Display the plot using Streamlit
    st.pyplot(fig)
