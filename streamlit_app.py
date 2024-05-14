import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from login_federgolf import login

# Set up the sidebar
st.sidebar.title("Your FederGolf Companion")
st.sidebar.write("Please select an option from the sidebar.")
st.sidebar.write("START BY RETRIEVING YOUR GOLF HISTORY ")


# Define a function to display the login form
def display_login_form():
    st.title("Login to Load Your F.I.G. Results")
    st.write("Please enter your username and password to dowload Your Results")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.button("Login")
    return username, password, submit_button


# Define a function to display the handicap visualizer
def display_handicap_visualizer(df):
    st.subheader("Handicap Visualizer")
    st.write(
        "Welcome to the Handicap Visualizer app. Here you can visualize your handicap data."
    )

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()

    #st.write(f"Your current handicap is: {current_handicap}")
    #st.write(f"Your best handicap is: {best_handicap}")
    st.title(f"Your current handicap is: {current_handicap}")
    st.title(f"Your best handicap is: {best_handicap}")
    
    plot_last_20(df)

    st.write(st.write(st.session_state.df))
#------------------------------------------------

# Main app logic
def main():        
    # Check if the user has selected an option from the sidebar
    selected_option = st.sidebar.radio(
        "Select an option", ["Retrieve FederGolf Data", "Handicap Visualizer", "New HCP Calculator (In Progress)"]
    )

    if selected_option == "Retrieve FederGolf Data":
        username, password, submit_button = display_login_form()
        login_attempt = False

        if submit_button:            
            login_attempt, df = login(username, password)
            
            if login_attempt:
                st.write("Login successful!")
                
                display_handicap_visualizer(df)
                # If his is correct I want to get into the Handicap visualizer option and use the df that I found

            else:
                st.write(
                    "Please enter both username and password. Something went wrong."
                )

    elif selected_option == "Handicap Visualizer":
        # Assuming you have already logged in and have the necessary data
        fig_companion(st.session_state.df)

# Define a function to plot the last result
def plot_last_100_results(df):
    fig, ax = plt.subplots(figsize=(12, 6))

    reversed_index = df.index[::-1]
    ax.plot(df["Data"], df["Index Nuovo"], linestyle="-", marker="o")

    ax.set_title("EGA Handicap vs Date for last 100 Rounds", fontsize=16)
    ax.set_ylabel("EGA", fontsize=16)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True)

    # Add minor ticks drawn in thin red dotted lines
    ax.grid(which="minor", linestyle=":", linewidth=0.2, color="red")

    plt.tight_layout()
    st.pyplot(fig)
    

def plot_last_20(df):
    fig, ax = plt.subplots(figsize = (12,7))   #create a new Figure with fixed Size
    last_20_results = df.iloc[:20]
    
    ax.plot(last_20_results['Date_String'][::-1], last_20_results['Index Nuovo'][::-1], linestyle = '-', marker = 'o')
    ax.fill_between(last_20_results['Date_String'][::-1], last_20_results['Index Nuovo'][::-1], color='skyblue', alpha=0.5)
    
    ax.set_title("EGA Handicap for last 20 Rounds", fontsize = 16)
    ax.set_ylabel('EGA', fontsize = 16)
    
    #Add minor ticks drawn in thin red dotted lines
    ax.minorticks_on()
    ax.grid(which = 'minor', linestyle = ":", linewidth = 0.2, color = 'red')
    ax.grid(True)
    
    ax.tick_params(axis = 'x', rotation = 45)
    
    # Set x-axis ticks and labels every 5 values
    ax.set_xticks(range(0, len(last_20_results['Date_String'][::-1]), 2))
    ax.set_xticklabels(last_20_results['Date_String'][::-1].iloc[::2])
    
    ax.set_ylim(last_20_results['Index Nuovo'].min() - .2, last_20_results['Index Nuovo'].max() + .2)
    
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
    st.subheader(f"Your Current HCP is: {current_handicap} - Best handicap: {best_handicap}")
    #st.subheader(f"Current handicap: {current_handicap} - Best handicap: {best_handicap}")
    #st.subheader(f"Best handicap: {best_handicap}")

    st.header("Last 20 results")
    plot_last_20(df)

    st.write()
    
    st.subheader("Your Last 100 results [Downloadable CSV]")
    st.write(st.write(st.session_state.df))
    
    plot_last_100_results(df)
#------------------------------------------------
    
if __name__ == "__main__":
    main()