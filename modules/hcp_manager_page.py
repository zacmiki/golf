@st.cache_data
def load_coursetable(df):
    import pandas as pd

    # Filter and prepare DataFrame
    filtered_df = df.dropna(subset=["SD"]).head(20)

    # 🔧 Ensure numeric type for SD
    filtered_df["SD"] = pd.to_numeric(filtered_df["SD"], errors="coerce")

    relevant_columns = ["Date_String", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    strippeddf = filtered_df[relevant_columns].copy().reset_index(drop=True)

    # Compute best rounds
    best_8 = strippeddf.nsmallest(8, "SD")  # <-- Now safe
    best_8_indices = best_8.index
    max_index = best_8_indices.max()
    highest_indexed_element = best_8.loc[max_index]

    strippeddf = strippeddf.rename(columns={
        "Index Nuovo": "New EGA",
        "Date_String": "Date"
    })

    # -------- PAGE LAYOUT --------
    st.title("Handicap Manager ⛳️")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()

    st.success(
        f"\n\n#### 🏌️ Tesserato {df['Tesserato'][0]}"
        + f"\n\n#### ⛳️ Current HCP: {current_handicap}  ⛳️"
        + f"\n\n#### ⛳️ Best HCP: {best_handicap}  ⛳️"
    )

    st.info("Your Next EXPIRING Round is")
    st.markdown(f"##### {strippeddf.iloc[-1]['Gara']}")
    st.markdown(
        f"##### Date: {strippeddf.iloc[-1]['Date']} - Stableford = {strippeddf.iloc[-1]['Stbl']} - SD = {strippeddf.iloc[-1]['SD']}"
    )
    st.divider()

    st.info(
        f"""Apparently you have {20 - max_index} games to play before you lose your next valid round which is  
    	{highest_indexed_element['Gara']} - Stbl = {highest_indexed_element['Stbl']} - SD = {highest_indexed_element['SD']}"""
    )
    st.divider()

    st.subheader("Last 20 VALID Rounds")
    st.markdown("##### Rounds Valid for HCP (Lowest SD) are highlighted")

    smallest_8_indices = strippeddf.nsmallest(8, 'SD').index

    def highlight_smallest(s):
        return ['background-color: rgba(0, 128, 0, 0.8)' if i in smallest_8_indices else '' for i in s.index]

    format_dict = {
        'Stbl': '{:,.0f}',
        'AGS': '{:,.0f}',
        'SD': '{:,.1f}',
        'New EGA': '{:,.1f}'
    }

    styled_df = strippeddf.style.apply(highlight_smallest, axis=0).format(format_dict)
    st.write(styled_df)
