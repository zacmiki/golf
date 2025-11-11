# modules/login_federgolf_requests.py
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd

# -------------------------
# Login function
# -------------------------
def login_and_get_session(username: str, password: str) -> bool:
    import re
    session = requests.Session()
    login_page_url = "https://areariservata.federgolf.it/"

    r = session.get(login_page_url)
    if r.status_code != 200:
        st.error(f"Cannot reach login page: {r.status_code}")
        return False

    # Parse token from <script> tag
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

    # Post login
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
    
    if r2.status_code != 200 or len(r2.content) < 10000:  # rough check if login page returned again
        st.error("Login failed. Check your credentials.")
        return False

    st.session_state.federgolf_session = session
    return True



# -------------------------
# Extract data function
# -------------------------
def extract_data() -> pd.DataFrame | None:
    """
    Use the stored session to fetch the results page
    """
    if "federgolf_session" not in st.session_state:
        st.error("No session available. Please login first.")
        return None

    session = st.session_state.federgolf_session
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

    headers_list = [th.get_text(strip=True) for th in table.find_all("th")]

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == len(headers_list):
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers_list)

    # Safe numeric conversion
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            pass

    # Convert date column if it exists
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    return df
