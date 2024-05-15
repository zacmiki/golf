import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from graphs import histo_100, histo_100G, plot_last_100_results
from login_federgolf import login

# Set up the sidebar
st.sidebar.title("Your FederGolf Companion")
st.caption("By Zac")
st.sidebar.write("Please select an option from the sidebar.")


# Define a function to display the login form
def display_login_form():
    st.title("Login to Load Your F.I.G. Results")
    st.write("Please enter your username and password to dowload Your Results")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.button("Login")
    return username, password, submit_button


# Define a function to handle logout
def handle_logout():
    st.sidebar.write("---")
    logout_button = st.sidebar.button("Logout")
    if logout_button:
        st.session_state.pop("df", None)
        st.experimental_rerun()


# Main app logic
def main():
    selected_option = st.sidebar.selectbox(
        "Select an option",
        [
            "Handicap Visualizer",
            "New HCP Calculator (In Progress)",
        ],
    )

    # Check if the user has already logged in
    if "df" not in st.session_state:
        username, password, submit_button = display_login_form()
        login_attempt = False

        if submit_button:
            login_attempt, df = login(username, password)

            if login_attempt:
                st.session_state["df"] = df
                st.experimental_rerun()
            else:
                st.write(
                    "Please enter both username and password. Something went wrong."
                )
    else:
        if selected_option == "Handicap Visualizer":
            # User has already logged in, display the handicap visualizer
            fig_companion(st.session_state.df)

            # Add a logout button in the sidebar
            handle_logout()

        else:
            # Need to implement this
            pass


def plot_last_20(df):
    fig, ax = plt.subplots(figsize=(12, 7))  # create a new Figure with fixed Size
    last_20_results = df.iloc[:20]

    ax.plot(
        last_20_results["Date_String"][::-1],
        last_20_results["Index Nuovo"][::-1],
        linestyle="-",
        marker="o",
    )
    ax.fill_between(
        last_20_results["Date_String"][::-1],
        last_20_results["Index Nuovo"][::-1],
        color="skyblue",
        alpha=0.5,
    )

    ax.set_title("EGA Handicap for last 20 Rounds", fontsize=16)
    ax.set_ylabel("EGA", fontsize=16)

    # Add minor ticks drawn in thin red dotted lines
    ax.minorticks_on()
    ax.grid(which="minor", linestyle=":", linewidth=0.2, color="red")
    ax.grid(True)

    ax.tick_params(axis="x", rotation=45)

    # Set x-axis ticks and labels every 5 values
    ax.set_xticks(range(0, len(last_20_results["Date_String"][::-1]), 2))
    ax.set_xticklabels(last_20_results["Date_String"][::-1].iloc[::2])

    ax.set_ylim(
        last_20_results["Index Nuovo"].min() - 0.2,
        last_20_results["Index Nuovo"].max() + 0.2,
    )

    plt.tight_layout()
    st.pyplot(fig)


def fig_companion(dff):
    import pandas as pd

    df = pd.DataFrame(dff)

    st.title("Official FederGolf Results")
    st.write("Hcp Visualizer -  and more services still to come ...")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()
    st.subheader(f"Tesserato {df['Tesserato'][0]}")
    st.subheader(
        f"Your Current HCP is: {current_handicap} - Best handicap: {best_handicap}"
    )

    st.header("Last 20 results")
    plot_last_20(df)
    
    st.header("Strokes in the Last 100 Rounds")
    #histo_100(dff)
    histo_100G(dff)

    
    st.header("Graph of the last 100 results")
    plot_last_100_results(df)

    st.subheader("Last 100 Rounds - All Your Data [Downloadable CSV]")
    st.write(st.write(st.session_state.df))



# ------------------------------------------------

if __name__ == "__main__":
    main()
