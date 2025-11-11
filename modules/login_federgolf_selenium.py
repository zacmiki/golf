# modules/login_federgolf_requests.py
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import re

# -------------------------
# Login function
# -------------------------
def login(username: str, password: str) -> bool:
    session = requests.Session()
    login_page_url = "https://areariservata.federgolf.it/"

    # Step 1: Get login page to retrieve the antiforgery token
    r = session.get(login_page_url)
    if r.status_code != 200:
        st.error(f"Cannot reach login page: {r.status_code}")
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    antiforgery_token = ""
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and "antiforgeryToken" in script.string:
            match = re.search(r'value="(.+?)"', script.string)
            if match:
                antiforgery_token = match.group(1)
                break

    if not antiforgery_token:
        st.error("Cannot find antiforgeryToken on the page")
        return False

    # Step 2: Post login data
    post_url = "https://areariservata.federgolf.it/Home/AuthenticateUser"
    payload = {
        "User": username,
        "Password": password,
        "__RequestVerificationToken": antiforgery_token,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": login_page_url,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r2 = session.post(post_url, data=payload, headers=headers)

    # Basic check for login success
    if r2.status_code != 200 or len(r2.content) < 10000:
        st.error("Login failed. Check your credentials.")
        return False

    st.session_state.federgolf_session = session
    return True


# -------------------------
# Extract data function
# -------------------------
def extract_data(session: requests.Session) -> pd.DataFrame | None:
    """
    Fetch the user's results page using the provided session.
    Returns a pandas DataFrame with normalized column names.
    """
    if not session:
        st.error("No session available. Please login first.")
        return None

    url = "https://areariservata.federgolf.it/Risultati/ShowGrid"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://areariservata.federgolf.it/Home/AuthenticateUser"
    }

    r = session.get(url, headers=headers)
    if r.status_code != 200:
        st.error(f"Failed to fetch data: {r.status_code}")
        return None

    soup = BeautifulSoup(r.content, "html.parser")
    table = soup.find("table", class_="entity-list-view w-100")
    if table is None:
        st.warning("No table found on the page")
        return None

    # Extract headers
    headers_list = [th.get_text(strip=True) for th in table.find_all("th")]
    # Normalize headers
    headers_list = [col.strip() for col in headers_list]

    # Extract rows
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == len(headers_list):
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers_list)

    # Strip whitespace from column names
    df.columns = [col.strip() for col in df.columns]

    # Convert numeric columns safely
    numeric_cols = [
        "Index Nuovo", "Index Vecchio", "Variazione", "AGS", "Par",
        "Playing HCP", "CR", "SR", "Stbl", "Buche", "Numero tessera"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert date column
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    return df
