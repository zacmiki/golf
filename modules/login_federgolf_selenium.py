import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import pandas as pd
from bs4 import BeautifulSoup

# -------------------------
# Login function (Selenium)
# -------------------------
def login_and_get_session(username: str, password: str) -> requests.Session | None:
    """Login via Selenium and return a requests.Session with valid cookies"""
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://areariservata.federgolf.it/Home/Login")
        driver.find_element(By.ID, "User").send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        if "logout" not in driver.page_source.lower() and "benvenuto" not in driver.page_source.lower():
            st.error("❌ Login failed!")
            driver.quit()
            return None
        
        # Transfer cookies to requests.Session
        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        st.success("✅ Login successful!")
        return session
    
    finally:
        driver.quit()

# -------------------------
# Data extraction function
# -------------------------
def extract_data(session: requests.Session) -> pd.DataFrame | None:
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
