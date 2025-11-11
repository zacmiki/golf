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
    Date column is formatted as YYYY-MM-DD (no time).
    """
    if not session:
        st.error("No session available. Please login first.")
        return None

    url = "https://areariservata.federgolf.it/Risultati/ShowGrid"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://areariservata.federgolf.it/Home/AuthenticateUser"
    }

    r = ses
