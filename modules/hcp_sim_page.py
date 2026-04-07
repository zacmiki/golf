from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from .course_hcp import get_allcourses, VALID_ROUNDS
from .federgolf_client import (
    BASE_URL,
    COURSE_HCP_URL,
    TEE_COLORS,
    build_cookies,
    calc_request_payload,
    generate_headers,
    store_session_cookies,
)
from .graphs import plot_last_n

BEST_8_COUNT = 8
SCENARIO_PRESETS = [33, 36, 38]


def hcp_sim() -> None:
    st.title("🧮 New HCP Calculator")
    st.subheader("Currently working for 18 Hole Courses")
    st.divider()

    tesserato_name = st.session_state.get("tesserato_name", "")
    tesserato_num = st.session_state.df["Numero tessera"].iloc[0]
    if tesserato_name:
        tesserato_display = f"{tesserato_name} ({tesserato_num})"
    else:
        tesserato_display = f"Tessera {tesserato_num}"

    current_handicap = st.session_state.get(
        "current_handicap", st.session_state.df["Index Nuovo"][0]
    )
    st.success(
        f"\n\n##### 🏌️ {tesserato_display}"
        + f"\n\n##### ⛳️ Current HCP: {current_handicap:.1f}  ⛳️",
    )

    sr, cr, par = select_course()

    if sr is None:
        st.divider()
        st.markdown(
            """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
            unsafe_allow_html=True,
        )
        return

    punti = st.number_input(
        "⛳️ INPUT YOUR STABLEFORD SCORE", min_value=1, max_value=54, value=36, step=1
    )

    assert cr is not None and par is not None
    new_sd, simulated_hcp = new_hcp(sr, cr, par, punti)

    st.info(
        f"\n\n##### New Handicap: {simulated_hcp:.2f}"
        + f"\n\n##### Last Round SD: {new_sd:.2f}",
    )

    st.divider()
    st.markdown("#### 📊 What If?")

    results: list[tuple[str, float, float]] = []
    for pts in SCENARIO_PRESETS:
        sd_res, hcp_res = new_hcp(sr, cr, par, pts)
        results.append((f"{pts} pts", sd_res, hcp_res))

    card_cols = st.columns(3)
    for i, (label, sd_res, hcp_res) in enumerate(results):
        delta = hcp_res - current_handicap
        delta_color = "#4CAF50" if delta < 0 else "#e63946" if delta > 0 else "#aaa"
        delta_sign = "+" if delta > 0 else ""

        with card_cols[i]:
            st.markdown(
                f"""
                <div style="background:#2d2d2d; border:1px solid #555; border-radius:12px; padding:16px; text-align:center; margin-bottom:8px;">
                <div style="font-size:16px; font-weight:bold; color:#fff;">⛳️ {label}</div>
                <hr style="margin:8px 0; border-color:#555;">
                <div style="font-size:12px; color:#ccc;">New SD</div>
                <div style="font-size:15px; font-weight:bold; color:#fff;">{sd_res:.1f}</div>
                <div style="font-size:12px; color:#ccc; margin-top:8px;">New HCP</div>
                <div style="font-size:20px; font-weight:bold; color:#fff;">{hcp_res:.1f}</div>
                <div style="font-size:13px; margin-top:6px; color:{delta_color}; font-weight:bold;">{delta_sign}{delta:+.1f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.success("#### EGA Plot - 20 results plus new projected value")
    plot_last_n(VALID_ROUNDS, new_handicap=simulated_hcp)

    st.divider()
    st.markdown(
        """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
        unsafe_allow_html=True,
    )


def select_course() -> tuple[Optional[float], Optional[float], Optional[float]]:
    st.markdown("#### 🏌️ Select Course")

    response = requests.get(COURSE_HCP_URL)
    if response.status_code != 200:
        st.error("Failed to load course handicap page.")
        return None, None, None

    soup = BeautifulSoup(response.text, "html.parser")
    token = None
    for script in soup.find_all("script"):
        content = script.string
        if content and "antiforgeryToken" in content:
            parts = content.split('value="')
            if len(parts) > 1:
                token = parts[1].split('"')[0]
            break

    if token:
        st.session_state.antiforgery_token = token
    store_session_cookies(response)

    circolo_options = {
        opt.text.strip(): opt["value"] for opt in soup.select("#ddlCircolo option")
    }
    selected_circolo = st.selectbox(
        "Select Circolo", options=list(circolo_options.keys())
    )

    url = f"{BASE_URL}/CourseHandicapCalc/Calc"
    headers = generate_headers(
        cookies=build_cookies(),
        referer=COURSE_HCP_URL,
        content_length=260,
    )

    circolo_value = circolo_options.get(selected_circolo)
    if not circolo_value:
        return None, None, None

    payload = {
        "selectedCircolo": circolo_value,
        "SelectedPercorso": "",
        "tee": "",
        "hcp": "",
        "__RequestVerificationToken": st.session_state.antiforgery_token,
    }
    resp = requests.post(url, headers=headers, data=payload)

    if resp.status_code != 200:
        st.error("Failed to fetch course data.")
        return None, None, None

    soup2 = BeautifulSoup(resp.text, "html.parser")
    course_options = {
        opt.text.strip(): opt["value"] for opt in soup2.select("#ddlPercorso option")
    }

    selected_course = st.selectbox("Select Course", options=list(course_options.keys()))

    selected_course_value = course_options.get(selected_course)
    if not selected_course_value:
        return None, None, None

    # Use all tee colors (same as playing_hcp_page.py)
    tee_color = st.selectbox("Select Tee Color", options=TEE_COLORS)

    # Get CR/SR/Par by making a POST with the tee (same as playing_hcp_page.py)
    final_payload = calc_request_payload(
        circolo_value, selected_course_value, tee_color, "18"
    )
    final_resp = requests.post(url, headers=headers, data=final_payload)

    if final_resp.status_code != 200:
        st.error("Failed to fetch course details.")
        return None, None, None

    # Parse the results table - same as playing_hcp_page.py
    soup_final = BeautifulSoup(final_resp.text, "html.parser")
    table = soup_final.find("table", id="risultatiHCP")
    if table:
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if cols and len(cols) >= 3:
                # The table has: Course, CR, Slope, Tee, Playing HCP
                try:
                    cr = float(cols[1].get_text(strip=True))
                    sr = float(cols[2].get_text(strip=True))

                    # Get Par from the database using course name
                    par = 72  # default
                    all_courses = get_allcourses()
                    # Match course by name in the database
                    course_match = all_courses[
                        all_courses["Circolo"].str.contains(
                            selected_circolo.split()[0], na=False
                        )
                        & all_courses["Percorso"].str.contains("Giallo-Blu", na=False)
                    ]
                    if not course_match.empty:
                        try:
                            par = float(course_match.iloc[0]["PAR"])
                        except (ValueError, KeyError):
                            pass

                    return sr, cr, par
                except (ValueError, IndexError):
                    pass

    st.error("Could not extract course values.")
    return None, None, None


def get_course_values(
    row: pd.Series, tee: str
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    cr_col = f"CR {tee} Uomini"
    sr_col = f"Slope {tee} Uomini"

    if cr_col not in row.index:
        cr_col = f"CR {tee} Donne"
        sr_col = f"Slope {tee} Donne"

    if cr_col not in row.index:
        return None, None, None

    try:
        cr = float(row[cr_col])
        sr = float(row[sr_col])
        par = float(row["PAR"])
    except (ValueError, TypeError):
        return None, None, None

    return sr, cr, par


def new_hcp(
    sr_percorso: float, cr_percorso: float, par_percorso: float, punti: float
) -> tuple[float, float]:
    df = st.session_state.df.copy()
    df["SD"] = pd.to_numeric(df["SD"], errors="coerce")

    if "Data" in df.columns:
        df = df.sort_values("Data", ascending=False)

    if "Valida" in df.columns:
        df = df[df["Valida"] == "S"]

    valid_sd = df["SD"].dropna().head(VALID_ROUNDS - 1).values.astype(float)

    if len(valid_sd) == 0:
        st.error("Not enough valid SDs for calculation.")
        return 0.0, 0.0

    # Use current_handicap from profile page (most accurate)
    current_hcp = st.session_state.get("current_handicap")
    if current_hcp is not None:
        playing_hcp = current_hcp
    else:
        playing_hcp = float(st.session_state.df["Index Nuovo"][0])

    adjusted_score = int(par_percorso + playing_hcp - (punti - 36))
    new_sd = (113 / sr_percorso) * (adjusted_score - cr_percorso)
    new_sd = round(new_sd, 1)

    all_sd = np.append(valid_sd, new_sd)
    best_8 = np.sort(all_sd)[:BEST_8_COUNT]

    hcp_simulato = round(float(np.mean(best_8)), 1)
    return new_sd, hcp_simulato
