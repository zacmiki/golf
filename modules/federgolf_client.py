from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup

BASE_URL = "https://areariservata.federgolf.it"
COURSE_HCP_URL = f"{BASE_URL}/CourseHandicapCalc/Index"
TEE_COLORS = ["Bianco", "Giallo", "Verde", "Blu", "Rosso", "Arancio"]


def generate_headers(
    cookies: Optional[dict] = None,
    referer: Optional[str] = None,
    content_length: Optional[int] = None,
) -> dict:
    headers = {
        "Host": "areariservata.federgolf.it",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    if referer:
        headers["Referer"] = referer
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    return headers


def extract_antiforgery_token(soup: BeautifulSoup) -> str:
    for script in soup.find_all("script"):
        content = script.string
        if content and "antiforgeryToken" in content:
            parts = content.split('value="')
            if len(parts) > 1:
                return parts[1].split('"')[0]
    return ""


def fetch_course_hcp_page() -> tuple[Optional[requests.Response], Optional[str]]:
    response = requests.get(COURSE_HCP_URL, headers=generate_headers({}))
    if response.status_code != 200:
        return None, None
    soup = BeautifulSoup(response.text, "html.parser")
    token = extract_antiforgery_token(soup)
    return response, token


def store_session_cookies(response: requests.Response) -> None:
    st.session_state.request_verification_token = response.cookies.get(
        "__RequestVerificationToken"
    )
    st.session_state.arraffinity = response.cookies.get("ARRAffinity")
    st.session_state.arraffinity_same_site = response.cookies.get("ARRAffinitySameSite")
    st.session_state.session_id = response.cookies.get("ASP.NET_SessionId")


def build_cookies() -> dict:
    return {
        "ASP.NET_SessionId": st.session_state.session_id,
        "__RequestVerificationToken": st.session_state.request_verification_token,
        "ARRAffinity": st.session_state.arraffinity,
        "ARRAffinitySameSite": st.session_state.arraffinity_same_site,
    }


def calc_request_payload(
    selected_circolo: str,
    selected_percorso: str = "",
    tee: str = "",
    hcp: str = "",
) -> dict:
    return {
        "selectedCircolo": selected_circolo,
        "SelectedPercorso": selected_percorso,
        "tee": tee,
        "hcp": hcp,
        "__RequestVerificationToken": st.session_state.antiforgery_token,
    }
