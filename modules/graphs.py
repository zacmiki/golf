import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm


def grapr_last_n(dff, n, plot_type):
    df = pd.DataFrame(dff)

    # Create a figure and axis object
    fig, ax = plt.subplots()

    if plot_type == "histogram":
        # Calculate the maximum value of df['AGS']
        max_value = df["AGS"].max()

        # Create a histogram with fixed range bins
        ax.hist(
            df["AGS"][-n:],
            bins=range(70, int(max_value) + 15, 4),
            edgecolor="black",
            alpha=0.5,
        )

        # Add labels and title
        ax.set_xlabel("Strokes per Round")
        ax.set_ylabel("Frequency")
        ax.set_title("Strokes per round in the Last {} FIG Tournaments".format(n))

        # Show the grid
        ax.grid(True)

        # Show both major and minor ticks
        ax.minorticks_on()

        # Customize grid for minor ticks only on the y-axis
        ax.grid(
            True, which="minor", axis="y", linestyle="--", color="red", linewidth=0.2
        )

    elif plot_type == "scatter":
        ax.scatter(df["Date_String"][-n:], df["AGS"][-n:])
        ax.set_title("Strokes per Round vs Date")
        ax.set_xlabel("Date")
        ax.set_ylabel("Strokes per Round")

    elif plot_type == "line":
        ax.plot(df["Date_String"][-n:], df["AGS"][-n:])
        ax.set_title("Strokes per Round over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Strokes per Round")

    elif plot_type == "bar":
        ax.bar(df["Date_String"][-n:], df["AGS"][-n:])
        ax.set_title("Strokes per Round")
        ax.set_xlabel("Date")
        ax.set_ylabel("Strokes per Round")

    # Display the plot using Streamlit
    st.pyplot(fig)


# Plot the last 100 Results ------------------------
def plot_last_100_results(dff):
    df = pd.DataFrame(dff)
    fig, ax = plt.subplots(figsize=(12, 7))

    # reversed_index = df.index[::-1]
    ax.plot(
        df["Date_String"][::-1],
        df["Index Nuovo"][::-1],
        linestyle="-",
        marker="o",
        color="purple",
        markersize=8,
    )
    # ax.plot(df["Data"], df["Index Nuovo"], linestyle="-", marker="o")

    ax.set_title("EGA Handicap vs Date for last 100 Rounds", fontsize=16)

    ax.set_ylabel("EGA", fontsize=16)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True)

    # Add minor ticks drawn in thin red dotted lines
    ax.grid(which="minor", linestyle=":", linewidth=0.2, color="red")

    # Set Special ticks for allocating the Strings
    ax.set_xticks(range(0, len(df["Date_String"][::-1]), 6))
    ax.set_xticklabels(df["Date_String"][::-1].iloc[::6])

    plt.tight_layout()
    st.pyplot(fig)


# ------- Histogram with Gaussian Fit
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

    # Calculate bin centers
    # bin_centers = 0.5 * (bins[1:] + bins[:-1])

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
        f"Strokes per round in the Last {num_results} FIG Tournaments", fontsize=14
    )

    # Show the grid
    ax.grid(True)

    # Show both major and minor ticks
    ax.minorticks_on()

    # Customize grid for minor ticks only on the y-axis
    ax.grid(True, which="minor", axis="y", linestyle="--", color="red", linewidth=0.2)

    # Print the center value of the Gaussian
    ax.text(
        mu,
        max(gaussian_curve) * 0.9,
        f"Center: {mu:.2f}",
        color="r",
        ha="center",
        fontsize=12,
    )

    # Add a legend for the Gaussian fit
    ax.legend(["Gaussian Fit"], loc="upper right", fontsize=10)

    # Display the plot using Streamlit
    st.pyplot(fig)
