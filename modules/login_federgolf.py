from typing import Union

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


def generate_headers(
    cookies: dict, referer: str = None, content_length: int = None
) -> dict:
    headers = {
        "Host": "areariservata.federgolf.it",
        "Cookie": "; ".join([f"{key}={value}" for key, value in cookies.items()]),
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    if referer:
        headers["Referer"] = referer

    if content_length:
        headers["Content-Length"] = str(content_length)

    return headers


def login(username: str, password: str) -> bool:
    url = "https://areariservata.federgolf.it/"
    response = requests.get(url, headers=generate_headers({}))

    if response.status_code != 200:
        return False

    request_verification_token = response.cookies.get("__RequestVerificationToken")
    st.session_state.request_verification_token = request_verification_token

    arraffinity = response.cookies.get("ARRAffinity")
    st.session_state.arraffinity = arraffinity

    arraffinity_same_site = response.cookies.get("ARRAffinitySameSite")
    st.session_state.arraffinity_same_site = arraffinity_same_site

    soup = BeautifulSoup(response.text, "html.parser")
    antiforgery_token = ""

    script_tags = soup.find_all("script")
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content and "antiforgeryToken" in script_content:
            antiforgery_token = script_content.split('value="')[1].split('"')[0]
            break

    st.session_state.antiforgery_token = antiforgery_token

    url = "https://areariservata.federgolf.it/Home/AuthenticateUser"
    data = {
        "UserName": username,
        "Password": password,
        "__RequestVerificationToken": antiforgery_token,
    }

    cookies = {
        "__RequestVerificationToken": request_verification_token,
        "ARRAffinity": arraffinity,
        "ARRAffinitySameSite": arraffinity_same_site,
    }

    headers = generate_headers(
        cookies, referer="https://areariservata.federgolf.it/", content_length=167
    )

    response = requests.post(url, data=data, headers=headers)

    session_id = response.cookies.get("ASP.NET_SessionId", None)
    st.session_state.session_id = session_id

    if response.status_code != 200 or len(response.content) < 10000:
        return False

    return True


def extract_data() -> Union[pd.DataFrame, None]:
    url = "https://areariservata.federgolf.it/Risultati/ShowGrid"

    cookies = {
        "_fbp": "fb.1.1715410992155.276799353",
        "ASP.NET_SessionId": st.session_state.session_id,
        "__RequestVerificationToken": st.session_state.request_verification_token,
        "ARRAffinity": st.session_state.arraffinity,
        "ARRAffinitySameSite": st.session_state.arraffinity_same_site,
        "lb_csc": "necessary_cookies,third_party_adv_cookies,third_party_stats_cookies",
        "version": "2",
        "_ga": "GA1.1.605352262.1715410994",
        "_ga_QBY22814GG": "GS1.1.1715410992.1.0.1715410996.0.0.0",
    }

    headers = generate_headers(
        cookies, referer="https://areariservata.federgolf.it/Home/AuthenticateUser"
    )

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="entity-list-view w-100")
    vocihtml = soup.find_all(class_="th-wrapper")
    tabletitles = [titoli.text for titoli in vocihtml]

    df = pd.DataFrame(columns=tabletitles)

    column_data = table.find_all("tr")
    skippedrows = 1

    for row in column_data[1:]:
        row_data = row.find_all("td")
        individual_row_data = [data.text.strip() for data in row_data]

        if len(individual_row_data) == len(df.columns):
            df.loc[len(df)] = individual_row_data
        else:
            print(f"I had to Skip {skippedrows} row")
            skippedrows += 1
            continue

    df.rename(columns={"Tipo Giocatore Nuovo": "Date_String"}, inplace=True)
    df["Date_String"] = df["Data"]
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

    df["Index Nuovo"] = pd.to_numeric(df["Index Nuovo"], errors="coerce")
    df["SD"] = pd.to_numeric(df["SD"])
    df["Index Vecchio"] = pd.to_numeric(df["Index Vecchio"])
    df["Variazione"] = pd.to_numeric(df["Variazione"])
    df["AGS"] = pd.to_numeric(df["AGS"])
    df["Par"] = pd.to_numeric(df["Par"])
    df["Playing HCP"] = pd.to_numeric(df["Playing HCP"])
    df["CR"] = pd.to_numeric(df["CR"])
    df["SR"] = pd.to_numeric(df["SR"])
    df["Stbl"] = pd.to_numeric(df["Stbl"], errors="coerce")
    df["Buche"] = pd.to_numeric(df["Buche"])
    df["Numero tessera"] = pd.to_numeric(df["Numero tessera"])

    st.session_state.df = df

    return df
