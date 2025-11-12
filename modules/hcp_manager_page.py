import streamlit as st
import pandas as pd

@st.cache_data
def load_coursetable(df):
    filtered_df = df.dropna(subset=["SD"]).head(20).copy()
    
    # Make sure SD is numeric (handle both '.' and ',' decimal separators)
    filtered_df["SD"] = (
        filtered_df["SD"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    filtered_df["SD"] = pd.to_numeric(filtered_df["SD"], errors="coerce")

    # Select relevant columns
    relevant_columns = ["Date_String", "Gara", "Stbl", "AGS", "SD", "Index Nuovo"]
    strippeddf = filtered_df[relevant_columns].copy().reset_index(drop=True)

    # -------------------------
    # COMPUTE BEST 8 ROUNDS
    # -------------------------
    best_8 = strippeddf.nsmallest(8, "SD")
    best_8_indices = best_8.index
    max_index = best_8_indices.max()
    highest_indexed_element = best_8.loc[max_index]

    # -------------------------
    # RENAME COLUMNS
    # -------------------------
    strippeddf = strippeddf.rename(columns={
        "Index Nuovo": "New EGA",
        "Date_String": "Date"
    })

    # -------------------------
    # PAGE LAYOUT
    # -------------------------
    st.title("Handicap Manager ⛳️")
    st.divider()

    current_handicap = df["Index Nuovo"].iloc[0]
    best_handicap = df["Index Nuovo"].min()

    st.success(
        f"""
        #### 🏌️ Tesserato {df['Tesserato'].iloc[0]}
        #### ⛳️ Current HCP: {current_handicap:.1f}  
        #### ⛳️ Best HCP: {best_handicap:.1f}
        """
    )

    # -------------------------
    # NEXT EXPIRING ROUND
    # -------------------------
    st.info("Your Next EXPIRING Round is")
    st.markdown(f"##### {strippeddf.iloc[-1]['Gara]()
