from __future__ import annotations

import pandas as pd
import streamlit as st

from .ui import player_overview

WINDOW_SIZE = 20
COUNTING_SCORES = 8
EXCLUDED_FORMULAS = {"L4M", "L2M"}


def handicap_window(df: pd.DataFrame) -> pd.DataFrame:
    rounds = df.copy()
    if "Formula" in rounds:
        rounds = rounds[~rounds["Formula"].isin(EXCLUDED_FORMULAS)]
    rounds["SD"] = pd.to_numeric(rounds["SD"], errors="coerce")
    rounds = rounds.dropna(subset=["SD"]).head(WINDOW_SIZE).copy()
    rounds["Counting"] = False
    if not rounds.empty:
        indices = rounds.nsmallest(min(COUNTING_SCORES, len(rounds)), "SD").index
        rounds.loc[indices, "Counting"] = True
    return rounds.reset_index(drop=True)


def handicap_manager() -> None:
    load_coursetable(st.session_state.df)


def load_coursetable(df: pd.DataFrame) -> None:
    rounds = handicap_window(df)
    st.title("Handicap Manager ⛳️")
    player_overview(df)
    if rounds.empty:
        st.warning("No valid handicap rounds are available.")
        return

    expiring = rounds.iloc[-1]
    st.info(
        f"Next expiring round: **{expiring['Gara']}** · {expiring['Data']} · "
        f"Stableford {expiring['Stbl']:.0f} · SD {expiring['SD']:.1f}"
    )

    counting = rounds[rounds["Counting"]]
    next_counting = counting.loc[counting.index.max()]
    rounds_remaining = len(rounds) - 1 - int(counting.index.max())
    st.info(
        f"**{rounds_remaining}** round(s) until the next counting score expires: "
        f"{next_counting['Gara']} · SD {next_counting['SD']:.1f}"
    )

    display = rounds.rename(columns={"Index Nuovo": "New HCP", "Data": "Date"})
    columns = ["Date", "Gara", "Stbl", "Formula", "SD", "New HCP", "Counting"]
    st.subheader("Current 20-round handicap window")
    st.dataframe(
        display[[column for column in columns if column in display]],
        hide_index=True,
        width="stretch",
        column_config={
            "Stbl": st.column_config.NumberColumn(format="%.0f"),
            "SD": st.column_config.NumberColumn(format="%.1f"),
            "New HCP": st.column_config.NumberColumn(format="%.1f"),
            "Counting": st.column_config.CheckboxColumn(),
        },
    )
