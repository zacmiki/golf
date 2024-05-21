import streamlit as st


@st.cache_data
def load_coursetable(df):
    # Filter the DataFrame to select the first 20 elements where 'SD' is not NaN
    filtered_df = df.dropna(subset=["SD"]).head(20)
    relevant_columns = ["Date_String", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    strippeddf = filtered_df[relevant_columns].copy()

    # Reset the index of strippeddf
    strippeddf = strippeddf.reset_index(drop=True)

    # worst_8 = strippeddf.nsmallest(8, "SD")
    best_8 = strippeddf.nsmallest(8, "SD")

    # Keep the original indices
    best_8_indices = best_8.index

    # Find the maximum index value from the best_8 indices
    max_index = best_8_indices.max()

    # Retrieve the corresponding row in the best_8 DataFrame
    highest_indexed_element = best_8.loc[max_index]

    strippeddf = strippeddf.rename(columns={"Index Nuovo": "New EGA"})
    strippeddf = strippeddf.rename(columns={"Date_String": "Date"})
    # --------- PAGE LAYOUT

    st.title("Handicap Manager ⛳️")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()

    st.success(
        f"\n\n#### 🏌️ Tesserato {df['Tesserato'][0]}"
        + f"\n\n#### ⛳️ Current HCP: {current_handicap}  ⛳️"
        + f"\n\n#### ⛳️ Best HCP: {best_handicap}  ⛳️",
    )

    st.info(f"Your Next EXPIRING Round is")
    st.markdown(f"##### {strippeddf.iloc[-1]['Gara']}")
    st.markdown(
        f"##### Date: {strippeddf.iloc[-1]['Date']} - Stableford = {strippeddf.iloc[-1]['Stbl']} - SD = {strippeddf.iloc[-1]['SD']}"
    )
    st.divider()
    st.info(
        f"""Apparently you have {20 - max_index} games to play before you lose your next valid round which is  \n
    	{highest_indexed_element['Gara']} - Stbl = {highest_indexed_element['Stbl']} - SD = {highest_indexed_element['SD']}"""
    )
    st.divider()
    
    
    
    st.subheader("Last 20 VALID Rounds")
    st.markdown(
        "##### Rounds Valid for HCP (Lowest SD) are highlighted"
    )
    
    smallest_8_indices = strippeddf.nsmallest(8, 'SD').index
    # Step 2: Define the highlighting function
    
    def highlight_smallest(s):
        #return ['background-color: skyblue' if i in smallest_8_indices else '' for i in s.index]
        return ['background-color: rgba(250, 255, 225, 0.3)' if i in smallest_8_indices else '' for i in s.index]
    
    format_dict = {
        'Stbl': '{:,.0f}',         # Integer format with no decimals
        'AGS': '{:,.0f}',          # Integer format with no decimals
        'SD': '{:,.1f}',           # Float format with one decimal
        'New EGA': '{:,.1f}'       # Float format with one decimal
    }
    
    styled_df = strippeddf.style.apply(highlight_smallest, axis=0).format(format_dict)
    st.write(styled_df)


    """
    st.write(worstofbest)
    st.write(element_number)
    """
