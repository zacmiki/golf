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

    # Extract user's profile ID and name from pages after login
    try:
        pages_to_try = [
            f"{BASE_URL}/AnagraficaTesserati/Index",
            f"{BASE_URL}/AnagraficaTesserati/ShowGrid",
            f"{BASE_URL}/Risultati/FilterForm",
            f"{BASE_URL}/Home/Index",
            f"{BASE_URL}/",
        ]

        for page_url in pages_to_try:
            headers = generate_headers(cookies={}, referer=f"{BASE_URL}/")
            r = session.get(page_url, headers=headers)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text()

            # Look for profile ID in various links that contain UUIDs
            if not st.session_state.get("profile_id"):
                links = soup.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    # Look for UUID patterns in href (works for ViewDetail, GoToEdit, ScaricaSDGiocatoreToPdf, etc.)
                    uuid_match = re.search(
                        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
                        href,
                        re.IGNORECASE,
                    )
                    if uuid_match:
                        st.session_state.profile_id = uuid_match.group(1)
                        break

            # Look for player name pattern like "SURNAME, NAME (12345)"
            # First try to find in h2 elements (common for titles)
            if not st.session_state.get("tesserato_name"):
                # Look specifically in h2, h1, h3 elements for better accuracy
                for tag in ["h2", "h1", "h3"]:
                    elements = soup.find_all(tag)
                    for element in elements:
                        element_text = element.get_text(strip=True)
                        name_match = re.search(
                            r"([A-Za-z]+),\s*([A-Za-z]+(?:\s*[A-Za-z]+)*)\s*\((\d{5,})\)",
                            element_text,
                        )
                        if name_match:
                            st.session_state.tesserato_name = (
                                f"{name_match.group(1)} {name_match.group(2)}"
                            ).strip()
                            st.session_state.tesserato_num = name_match.group(3)
                            break
                    if st.session_state.get("tesserato_name"):
                        break

                # Fallback to searching all text if not found in headers
                if not st.session_state.get("tesserato_name"):
                    name_match = re.search(
                        r"([A-Za-z]+),\s*([A-Za-z]+(?:\s*[A-Za-z]+)*)\s*\((\d{5,})\)",
                        text,
                    )
                    if name_match:
                        st.session_state.tesserato_name = (
                            f"{name_match.group(1)} {name_match.group(2)}"
                        ).strip()
                        st.session_state.tesserato_num = name_match.group(3)

            if st.session_state.get("profile_id") and st.session_state.get(
                "tesserato_name"
            ):
                break

    except Exception:
        pass

    return True


def extract_data(session: Optional[requests.Session]) -> Optional[pd.DataFrame]:
    if session is None:
        st.error("No session available. Please login first.")
        return None

    # Get the user's profile ID from session state (set during login)
    profile_id = st.session_state.get("profile_id")

    if not profile_id:
        # Fall back to results page
        return extract_data_from_results(session)

    profile_url = f"{BASE_URL}/AnagraficaTesserati/ViewDetail/{profile_id}"
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

    # Use name and tessera from login if already extracted
    if st.session_state.get("tesserato_name"):
        # Already extracted during login
        pass
    else:
        # Extract from profile page - use same robust regex as during login
        text = soup.get_text()
        # First try to find in h2 elements (common for titles)
        for tag in ["h2", "h1", "h3"]:
            elements = soup.find_all(tag)
            for element in elements:
                element_text = element.get_text(strip=True)
                name_match = re.search(
                    r"([A-Za-z]+),\s*([A-Za-z]+(?:\s*[A-Za-z]+)*)\s*\((\d{5,})\)",
                    element_text,
                )
                if name_match:
                    st.session_state.tesserato_name = (
                        f"{name_match.group(1)} {name_match.group(2)}"
                    ).strip()
                    st.session_state.tesserato_num = name_match.group(3)
                    break
            if st.session_state.get("tesserato_name"):
                break

        # Fallback to searching all text if not found in headers
        if not st.session_state.get("tesserato_name"):
            name_match = re.search(
                r"([A-Za-z]+),\s*([A-Za-z]+(?:\s*[A-Za-z]+)*)\s*\((\d{5,})\)", text
            )
            if name_match:
                st.session_state.tesserato_name = (
                    f"{name_match.group(1)} {name_match.group(2)}"
                ).strip()
                st.session_state.tesserato_num = name_match.group(3)

    # Use tessera number from login if available, otherwise from profile
    if st.session_state.get("tesserato_num"):
        df["Numero tessera"] = st.session_state.tesserato_num
    else:
        text = soup.get_text()
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


def extract_data_from_results(session: requests.Session) -> Optional[pd.DataFrame]:
    """Fallback: extract data from /Risultati/ShowGrid when profile page fails."""
    if session is None:
        st.error("No session available. Please login first.")
        return None

    url = f"{BASE_URL}/Risultati/ShowGrid"
    headers = generate_headers(cookies={}, referer=f"{BASE_URL}/Home/AuthenticateUser")

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

    if not rows:
        st.warning("No data found")
        return None

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

    if "Index Nuovo" in df.columns and len(df) > 0:
        st.session_state.current_handicap = float(df["Index Nuovo"].iloc[0])

    # Try to extract name from Gara column
    if "Gara" in df.columns and "Numero tessera" in df.columns:
        gara = df["Gara"].iloc[0]
        name_match = re.search(r"^([A-Z]+),\s*([A-Z]+)\s*-", gara)
        if name_match:
            st.session_state.tesserato_name = (
                f"{name_match.group(1)} {name_match.group(2)}"
            )
        else:
            st.session_state.tesserato_name = "Golfer"

    return df
