from __future__ import annotations

from typing import Optional

import pandas as pd
import requests
import streamlit as st
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

VALID_ROUNDS = 20


def handicap_request() -> None:
    response, token = fetch_course_hcp_page()
    if response is None:
        st.error("Failed to load course handicap page.")
        return

    st.session_state.antiforgery_token = token
    store_session_cookies(response)
    st.subheader("Handicap Calculator")

    soup = BeautifulSoup(response.text, "html.parser")

    circolo_options = {
        opt.text.strip(): opt["value"] for opt in soup.select("#ddlCircolo option")
    }
    selected_circolo = st.selectbox(
        "Select Circolo", options=list(circolo_options.keys())
    )
    selected_circolo_value = circolo_options[selected_circolo]

    url = f"{BASE_URL}/CourseHandicapCalc/Calc"
    headers = generate_headers(
        cookies=build_cookies(),
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

    handicap = st.session_state.df["Index Nuovo"][0]
    st.session_state.punti_stbl = st.text_input("Punteggio Stableford")

    if st.button("Compute Handicap"):
        payload = calc_request_payload(
            selected_circolo_value,
            selected_course_value,
            tee_color,
            str(handicap),
        )
        resp = requests.post(url, headers=headers, data=payload)

        playing_hcp: Optional[str] = None
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", id="risultatiHCP")
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols:
                    playing_hcp = cols[4].get_text(strip=True)

        idx = selected_course.index("-") + 2
        st.session_state.circolo = selected_circolo
        st.session_state.percorso = selected_course[idx:]
        st.session_state.tee_color = tee_color
        st.session_state.playing_hcp = playing_hcp


@st.cache_data(ttl=86400)
def get_allcourses() -> pd.DataFrame:
    url = f"{BASE_URL}/SlopeAndCourseRating/Index"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="single-table slope responsive")

    if table is None:
        return pd.DataFrame()

    headers_html = """
    <tr>
    <th>Circolo</th>
    <th>Percorso</th>
    <th align="center">PAR</th>
    <th align="center">CR Nero Uomini</th>
    <th align="center">Slope Nero Uomini</th>
    <th align="center">CR Bianco Uomini</th>
    <th align="center">Slope Bianco Uomini</th>
    <th align="center">CR Giallo Uomini</th>
    <th align="center">Slope Giallo Uomini</th>
    <th align="center">CR Verde Uomini</th>
    <th align="center">Slope Verde Uomini</th>
    <th align="center">CR Blu Donne</th>
    <th align="center">Slope Blu Donne</th>
    <th align="center">CR Rosso Donne</th>
    <th align="center">Slope Rosso Donne</th>
    <th align="center">CR Arancio Donne</th>
    <th align="center">Slope Arancio Donne</th>
    </tr>
    """
    headers_soup = BeautifulSoup(headers_html, "html.parser")
    headers_list = [th.text.strip() for th in headers_soup.find_all("th")]

    data: list[list[str]] = []
    for row in table.find_all("tr")[3:]:
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) == len(headers_list):
            data.append(cells)

    return pd.DataFrame(data, columns=headers_list)
