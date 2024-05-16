import streamlit as st
def loadcoursetable(dff):
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(dff)
    
    # Filter the DataFrame to select the first 20 elements where 'SD' is not NaN
    filtered_df = df.dropna(subset=['SD']).head(20)
    relevant_columns = ['Date_String', 'Gara', 'Stbl', 'AGS', 'SD', 'Index Nuovo']
    strippeddf = filtered_df[relevant_columns].copy()
    
    # Extract the values of 'Index Nuovo' from the filtered DataFrame and convert to a NumPy array
    #valid_results = filtered_df['Index Nuovo'].values
    #sorted_valid_results = np.sort(valid_results)
    # Select the 8 lowest values
    #best_8 = sorted_valid_results[:8]
    
    #doing the same in one line
    best_8 = strippeddf.nlargest(8, 'Stbl')
    
    min_stbl_index = best_8['Stbl'].idxmin()
    worstofbest = best_8.loc[min_stbl_index]
    
    element_number = strippeddf.index[strippeddf.eq(worstofbest).all(axis=1)][0]
    
    nextgoodone = strippeddf.iloc[element_number]
    
    strippeddf = strippeddf.rename(columns={'Index Nuovo': 'New EGA'})
    strippeddf = strippeddf.rename(columns={'Date_String': 'Date'})
    # --------- PAGE LAYOUT
    
    st.title("Handicap Manager")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()
    st.subheader(f"Tesserato {df['Tesserato'][0]}")
    
    st.success(f"Your Current HCP is: {current_handicap} - Best handicap: {best_handicap}", icon="⛳️",)
    st.info(f"Your Next EXPIRING Round is" )
    st.subheader(f" {strippeddf.iloc[-1]['Gara']}")
    st.subheader(f"Date: {strippeddf.iloc[-1]['Date']} - Stablefod Result = {strippeddf.iloc[-1]['Stbl']}")
    st.divider()
    
    st.info(f"""Apparently you have {20 - element_number} games to play before you lose your next valid round which is  \n
    	{nextgoodone['Gara']} - Stbl = {nextgoodone['Stbl']}""")
 
    st.subheader("Last 20 VALID Rounds")
    st.write("You can sort the table by clicking on the column name to  \n ... in case you want to what troubles are you running into, in your golfing future ...")
    st.write(strippeddf)
    
    #st.write(st.write(st.session_state.df))
    
    st.divider()
    st.subheader("Last 8 Valid Rounds (scorewise))")
    st.write(best_8)
    
    '''
    st.write(worstofbest)
    st.write(element_number)
    '''