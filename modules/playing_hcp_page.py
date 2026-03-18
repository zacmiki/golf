from __future__ import annotations

import streamlit as st
import requests
from bs4 import BeautifulSoup

from .federgolf_client import (
    BASE_URL,
    COURSE_HCP_URL,
    TEE_COLORS,
    build_cookies,
    calc_request_payload,
    fetch_course_hcp_page,
    generate_headers,
    store_session_cookies,
)


def playing_hcp() -> None:
    st.title("⛳️ Playing HCP Calculator")
    st.caption(
        "The program takes your current EGA as the starting value to calculate the playing handicap.  \n"
        "Just input a different number to check the playing handicap for that specific EGA"
    )
    playing_handicap()
    st.divider()
    st.markdown(
        """
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
        unsafe_allow_html=True,
    )


def playing_handicap() -> None:
    response, token = fetch_course_hcp_page()
    if response is None:
        st.error("Failed to fetch data from the server.")
        return

    store_session_cookies(response)
    st.session_state.antiforgery_token = token

    soup = BeautifulSoup(response.text, "html.parser")
    circolo_options = {
        opt.text.strip(): opt["value"] for opt in soup.select("#ddlCircolo option")
    }

    selected_circolo = st.selectbox(
        "Select Circolo", options=list(circolo_options.keys())
    )
    selected_circolo_value = circolo_options[selected_circolo]

    if not selected_circolo_value:
        st.error("Please select a Circolo option.")
        return

    url = f"{BASE_URL}/CourseHandicapCalc/Calc"
    cookies = build_cookies()
    headers = generate_headers(
        cookies=cookies,
        referer=COURSE_HCP_URL,
        content_length=260,
    )
    payload = calc_request_payload(selected_circolo_value)

    resp = requests.post(url, headers=headers, data=payload)
    if resp.status_code != 200:
        st.error("Failed to fetch course data.")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    course_options = {
        opt.text.strip(): opt["value"] for opt in soup.select("#ddlPercorso option")
    }

    selected_course = st.selectbox("Select Course", options=list(course_options.keys()))
    selected_course_value = course_options[selected_course]
    tee_color = st.selectbox("Select Tee Color", options=TEE_COLORS)

    handicap = st.number_input(
        ":green[Enter The Playing Index]",
        min_value=-6.0,
        max_value=54.0,
        value=st.session_state.df["Index Nuovo"][0],
    )

    if st.button("Compute Playing Handicap"):
        payload = calc_request_payload(
            selected_circolo_value,
            selected_course_value,
            tee_color,
            str(handicap),
        )
        resp = requests.post(url, headers=headers, data=payload)

        if resp.status_code != 200:
            st.error("Failed to compute handicap.")
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", id="risultatiHCP")
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols:
                    playing_hcp = cols[4].get_text(strip=True)
                    st.info(f"#### Playing Hcp = {playing_hcp}")
                    return

        st.error("Failed to compute handicap.")
