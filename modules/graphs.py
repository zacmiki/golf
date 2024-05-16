import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm


# Cache this result to avoid recomputing it every time
@st.cache_data
def plot_last_n(df, n, plot_type="line"):
    fig, ax = plt.subplots(figsize=(12, 7))
    last_n_results = df.iloc[:n]

    if plot_type == "scatter":
        ax.scatter(
            last_n_results["Date_String"][::-1],
            last_n_results["Index Nuovo"][::-1],
        )
    elif plot_type == "line":
        ax.plot(
            last_n_results["Date_String"][::-1],
            last_n_results["Index Nuovo"][::-1],
            linestyle="-",
            marker="o",
        )
        ax.fill_between(
            last_n_results["Date_String"][::-1],
            last_n_results["Index Nuovo"][::-1],
            color="skyblue",
            alpha=0.5,
        )
        ax.grid(True)  # Add grid lines only for line plot
    elif plot_type == "bar":
        ax.bar(last_n_results["Date_String"][::-1], last_n_results["Index Nuovo"][::-1])
    elif plot_type == "hist":
        # Determine the number of bins based on the data range and size
        num_bins = min(10, len(last_n_results))
        ax.hist(last_n_results["Index Nuovo"][::-1], bins=num_bins)

    ax.set_title("EGA Handicap for last {} Rounds".format(n), fontsize=16)
    ax.set_ylabel("EGA", fontsize=16)

    ax.minorticks_off()
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", which="both", length=0)  # Remove y-axis ticks
    ax.set_xticks(range(0, len(last_n_results["Date_String"][::-1]), 2))
    ax.set_xticklabels(last_n_results["Date_String"][::-1].iloc[::2])
    ax.set_ylim(
        last_n_results["Index Nuovo"].min() - 0.2,
        last_n_results["Index Nuovo"].max() + 0.2,
    )

    plt.tight_layout()
    st.pyplot(fig)


# ------- Histogram with Gaussian Fit
@st.cache_data
def histo_n(df, plot_gaussian=True, num_results=100):
    # Filter out non-finite values (None and zeros) from the DataFrame
    filtered_data = df["AGS"].dropna().replace(0, np.nan).dropna()

    # Create a figure with a custom size
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get the last num_results values from filtered_data
    last_n_values = filtered_data.iloc[-num_results:]

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
    ax.set_xlabel("Strokes per Round", fontsize=12)
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

    # Print the center value of the Gaussian
    ax.text(
        mu,
        max(gaussian_curve) * 0.9,
        f"Center: {mu:.2f}",
        color="r",
        ha="center",
        fontsize=10,
    )

    # Add a legend for the Gaussian fit
    ax.legend(["Gaussian Fit"], loc="upper right", fontsize=8)

    # Display the plot using Streamlit
    st.pyplot(fig)
