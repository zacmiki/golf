from __future__ import annotations

import pandas as pd
import streamlit as st


def current_handicap(df: pd.DataFrame) -> float:
    stored = st.session_state.get("current_handicap")
    if stored is not None:
        return float(stored)
    return float(df["Index Nuovo"].dropna().iloc[0])


def player_label(df: pd.DataFrame) -> str:
    name = st.session_state.get("tesserato_name")
    membership = int(df["Numero tessera"].dropna().iloc[0])
    return f"{name} ({membership})" if name else f"Tessera {membership}"


def player_overview(df: pd.DataFrame) -> None:
    player, current, best = st.columns(3)
    player.metric("Player", player_label(df))
    current.metric("Current Handicap", f"{current_handicap(df):.1f}")
    best.metric("Best recorded Handicap", f"{df['Index Nuovo'].min():.1f}")


def sidebar_footer() -> None:
    st.sidebar.divider()
    coffee_url = "https://buymeacoffee.com/miczac?l=it"
    button_url = (
        "https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee"
        "&emoji=&slug=miczac&button_colour=FFDD00&font_colour=000000"
        "&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"
    )
    st.sidebar.markdown(f"[![Buy me a coffee]({button_url})]({coffee_url})")
