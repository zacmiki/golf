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

    profile_url = f"{BASE_URL}/AnagraficaTesserati/ViewDetail/20d6d93e-9d1e-4fc5-b1c3-915b435c2c0a"
    headers = generate_headers(
        cookies={},
        referer=f"{BASE_URL}/",
    )

    r = session.get(profile_url, headers=headers)
    if r.status_code != 200:
        st.error(f"Failed to fetch data: {r.status_code}")
        return None

    soup = BeautifulSoup(r.content, "html.parser")

    # Extract current handicap from page
    text = soup.get_text()
    match = re.search(r"Handicap Index\s*([0-9]+[.,][0-9]+)", text)
    if match:
        current_hcp = float(match.group(1).replace(",", "."))
        st.session_state.current_handicap = current_hcp

    # Find the results table in the profile page
    tables = soup.find_all("table")
    results_table = None
    for t in tables:
        headers_list = [th.get_text(strip=True) for th in t.find_all("th")]
        if "SD" in headers_list and "Index Nuovo" in headers_list:
            # Check actual row count
            for tr in t.find_all("tr")[1:]:
                cells = tr.find_all("td")
                if len(cells) == len(headers_list):
                    results_table = t
                    break
            if results_table:
                break

    if results_table is None:
        st.warning("No results table found on the profile page")
        return None

    headers_list = [th.get_text(strip=True) for th in results_table.find_all("th")]

    rows = []
    for tr in results_table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == len(headers_list):
            rows.append(cells)
        elif len(cells) > 0:
            print(f"Warning: row with {len(cells)} cells, expected {len(headers_list)}")

    df = pd.DataFrame(rows, columns=headers_list)

    # Extract player info from profile page
    text = soup.get_text()

    # Look for pattern like "ZACCHIGNA, MICHELE (94942)"
    tessera_match = re.search(r"([A-Z]+),\s*([A-Z]+)\s*\((\d+)\)", text)
    if tessera_match:
        player_name = f"{tessera_match.group(1)} {tessera_match.group(2)}"
        player_tessera = tessera_match.group(3)
        st.session_state.tesserato_name = player_name
        df["Numero tessera"] = player_tessera
    else:
        # Fallback: just look for number
        tessera_match = re.search(r"(\d{5,})", text)
        if tessera_match:
            df["Numero tessera"] = tessera_match.group(1)

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
        "SD",
        "Corr SD",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
        df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")

    if "Valida" in df.columns:
        df = df[df["Valida"] == "S"].copy()

    if "Data" in df.columns:
        df = df.sort_values("Data", ascending=False).reset_index(drop=True)

    return df
