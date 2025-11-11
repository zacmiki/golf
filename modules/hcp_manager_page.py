# modules/hcp_manager_page.py

import streamlit as st
import pandas as pd

@st.cache_data
def load_coursetable(df: pd.DataFrame):
    """
    Display the course table. Automatically handles missing columns.
    """
    if df is None or df.empty:
        st.warning("No data available.")
        return

    # Define the columns you want to display
    relevant_columns = [
        "Data", "Index Nuovo", "Index Vecchio", "Variazione", 
        "AGS", "Par", "Playing HCP", "CR", "SR", "Stbl", 
        "Buche", "Numero tessera"
    ]

    # Keep only columns that actually exist in the DataFrame
    existing_cols = [col for col in relevant_columns if col in df.columns]

    # Warn about any missing columns
    missing_cols = [col for col in relevant_columns if col not in df.columns]
    if missing_cols:
        st.warning(f"The following columns are missing and will not be displayed: {missing_cols}")

    # Copy the filtered DataFrame
    strippeddf = df[existing_cols].copy()

    # Optional: display the table
    st.dataframe(strippeddf)
