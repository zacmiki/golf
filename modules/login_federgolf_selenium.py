from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from .federgolf_client import (
    BASE_URL,
    build_cookies,
    extract_antiforgery_token,
    generate_headers,
)

FEDERGOLF_SESSION_COOKIES = [
    "_fbp",
    "_ga",
    "_ga_QBY22814GG",
    "lb_csc",
    "version",
]


def login(username: str, password: str) -> bool:
    login_page_url = f"{BASE_URL}/"

    session = requests.Session()
    r = session.get(login_page_url)
    if r.status_code != 200:
        st.error(f"Cannot reach login page: {r.status_code}")
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    antiforgery_token = extract_antiforgery_token(soup)
    if not antiforgery_token:
        st.error("Cannot find antiforgeryToken on the page")
        return False

    post_url = f"{BASE_URL}/Home/AuthenticateUser"
    payload = {
        "User": username,
        "Password": password,
        "__RequestVerificationToken": antiforgery_token,
    }

    headers = generate_headers(
        cookies={},
        referer=login_page_url,
        content_length=None,
    )

    r2 = session.post(post_url, data=payload, headers=headers)

    if r2.status_code != 200 or len(r2.content) < 10000:
        st.error("Login failed. Check your credentials.")
        return False

    session_cookies = {c.name: c.value for c in session.cookies}
    for key in FEDERGOLF_SESSION_COOKIES:
        val = session_cookies.get(key)
        if val is not None:
            session.cookies.set(key, str(val))

    st.session_state.federgolf_session = session
    return True


def extract_data(session: Optional[requests.Session]) -> Optional[pd.DataFrame]:
    if session is None:
        st.error("No session available. Please login first.")
        return None

    url = f"{BASE_URL}/Risultati/ShowGrid"
    headers = generate_headers(
        cookies={},
        referer=f"{BASE_URL}/Home/AuthenticateUser",
    )

    r = session.get(url, headers=headers)
    if r.status_code != 200:
        st.error(f"Failed to fetch data: {r.status_code}")
        return None

    soup = BeautifulSoup(r.content, "html.parser")
    table = soup.find("table", class_="entity-list-view w-100")
    if table is None:
        st.warning("No table found on the page")
        return None

    headers_list = [th.get_text(strip=True) for th in table.find_all("th")]

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == len(headers_list):
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers_list)

    numeric_cols = [
        "Index Nuovo",
        "Index Vecchio",
        "Variazione",
        "AGS",
        "Par",
        "Playing HCP",
        "CR",
        "SR",
        "Stbl",
        "Buche",
        "Numero tessera",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
        df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")

    return df
