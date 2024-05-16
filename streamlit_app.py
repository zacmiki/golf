import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from graphs import histo_100, plot_last_100_results, plot_last_20
from login_federgolf import login
from hcpfunctions import loadcoursetable

# Set up the sidebar.  -  SIDEBAR ----------- SIDEBAR ------------ SIDEBAR OPTIONS
st.sidebar.title("Your FederGolf Companion")
st.sidebar.caption("By Zac")
st.sidebar.write("Please select an option from the sidebar.")


# Define a function to display the login form.   ------------------ LOGIN WINDOW 
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


# Main app logic.   ------ MAIN APP LOGIC --- HANDLING OF THE MENU
def main():
    selected_option = st.sidebar.selectbox(
        "Select an option",
        [
            "Handicap Visualizer",
            "HCP Manager",
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
            if selected_option == "HCP Manager":
                # User has already logged in, display the handicap visualizer
                loadcoursetable(st.session_state.df)
                # Add a logout button in the sidebar
                handle_logout()

            pass

# ------------- Visualization Page ------ F.I.G. Session -----------

def fig_companion(dff):
    import pandas as pd

    df = pd.DataFrame(dff)
    relevant_columns = ['Date_String', 'Gara', 'Stbl', 'AGS', 'SD', 'Index Nuovo']
    strippeddf = df[relevant_columns].copy()

    st.title("Official FederGolf Results")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()
    st.subheader(f"Tesserato {df['Tesserato'][0]}")
    st.subheader(
        f"Your Current HCP is: {current_handicap} - Best handicap: {best_handicap}"
    )
    
    st.divider()

    st.header("Last 20 results")
    plot_last_20(df)
    
    st.divider()
    
    st.header("Last 100 Rounds - Strokes Taken - Histogram")
    histo_100(dff)
    
    st.divider()
    
    st.header("Last 100 Rounds - HCP Graph")
    plot_last_100_results(df)
    
    st.divider()

    st.subheader("Last 100 Rounds - Meaningful Data [Downloadable CSV]")
    #st.write(st.write(st.session_state.df))
    st.write(strippeddf)

# ------------------------------------------------

if __name__ == "__main__":
    main()
