import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


# Login and call the function to extract data
def login(username, password):
    # Make the first request
    # ============================================================================================
    url = "https://areariservata.federgolf.it/"

    # Maybe take a better look at what are ga etc ...
    request_headers = {
        "Host": "areariservata.federgolf.it",
        "Cookie": '_fbp=fb.1.1715410992155.276799353; lb_csc={"level": ["necessary_cookies","third_party_adv_cookies","third_party_stats_cookies"], "version": "2"}; _ga=GA1.1.605352262.1715410994; _ga_QBY22814GG=GS1.1.1715410992.1.1.1715411659.0.0.0',
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Sec-Purpose": "prefetch;prerender",
        "Purpose": "prefetch",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "iframe",
        "Referer": "https://www.federgolf.it/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    response = requests.get(url, headers=request_headers)

    # If the first request fails, return False and an empty DataFrame
    if response.status_code != 200:
        return False

    # print(response.status_code)

    # Get the necessaary information for the next requests from the cookies
    # ----------------------------------------
    request_verification_token = response.cookies.get("__RequestVerificationToken")
    st.session_state.request_verification_token = request_verification_token

    arraffinity = response.cookies.get("ARRAffinity")
    st.session_state.arraffinity = arraffinity

    arraffinity_same_site = response.cookies.get("ARRAffinitySameSite")
    st.session_state.arraffinity_same_site = arraffinity_same_site

    # Get the info from the html
    # ----------------------------------------
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    antiforgery_token = ""

    # Find all script tags in the HTML
    script_tags = soup.find_all("script")

    # Loop through each script tag to find antiforgeryToken
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content and "antiforgeryToken" in script_content:
            # Extract the value of antiforgeryToken
            antiforgery_token = script_content.split('value="')[1].split('"')[0]
            break  # Exit the loop after finding the antiforgeryToken

    st.session_state.antiforgery_token = antiforgery_token

    # Make the second request
    # ============================================================================================

    url = "https://areariservata.federgolf.it/Home/AuthenticateUser"
    data = {
        "UserName": username,
        "Password": password,
        "__RequestVerificationToken": antiforgery_token,
    }

    headers = {
        "Host": "areariservata.federgolf.it",
        "Cookie": f"__RequestVerificationToken={request_verification_token}; ARRAffinity={arraffinity}; ARRAffinitySameSite={arraffinity_same_site}",
        "Content-Length": "167",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://areariservata.federgolf.it",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://areariservata.federgolf.it/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    response = requests.post(url, data=data, headers=headers)

    # Get Session id from the cookies
    session_id = response.cookies.get("ASP.NET_SessionId", None)
    st.session_state.session_id = session_id

    # If the third request fails, return False and an empty DataFrame
    # We check the lenght of the response
    if response.status_code != 200 or len(response.content) != 11666:
        return False

    # If all requests are successful, set success to True and extract the data
    return True


# Extract data in the correct format
def extract_data():
    # Make the third request
    # ============================================================================================
    url = "https://areariservata.federgolf.it/Risultati/ShowGrid"

    request_headers = {
        "Host": "areariservata.federgolf.it",
        # "Cookie": f"_fbp=fb.1.1715410992155.276799353; ASP.NET_SessionId=0bb4w1pr5n1avxi42wclunhb; __RequestVerificationToken=Q3cQZ6rRNuCFJJ1PDGPWihBGMadA-2bH6ML37Ll5eWbcvrq9drjRkoHZVPnvoR44MIk131av4rtbREXSYdYneFIa2RHg764DHXYZH6Zx_bI1; ARRAffinity=ffb49eabd953a476cb98d9c8c11af5f9d36554739c50a642edc8826844f26d98; ARRAffinitySameSite=ffb49eabd953a476cb98d9c8c11af5f9d36554739c50a642edc8826844f26d98; lb_csc=necessary_cookies,third_party_adv_cookies,third_party_stats_cookies; version=2; _ga=GA1.1.605352262.1715410994; _ga_QBY22814GG=GS1.1.1715410992.1715410994; _ga_QBY22814GG=GS1.1.1715410992.1.0.1715410996.0.0.0",
        "Cookie": f"_fbp=fb.1.1715410992155.276799353; ASP.NET_SessionId={st.session_state.session_id}; __RequestVerificationToken={st.session_state.request_verification_token}; ARRAffinity={st.session_state.arraffinity}; ARRAffinitySameSite={st.session_state.arraffinity_same_site}; lb_csc=necessary_cookies,third_party_adv_cookies,third_party_stats_cookies; version=2; _ga=GA1.1.605352262.1715410994; _ga_QBY22814GG=GS1.1.1715410992.1.0.1715410996.0.0.0",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://areariservata.federgolf.it/Home/AuthenticateUser",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    response = requests.get(url, headers=request_headers)

    # Get the info from the html for the new antiforgery token since it changes every time we have to get the new one
    # ----------------------------------------
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    antiforgery_token = ""

    # Find all script tags in the HTML
    script_tags = soup.find_all("script")

    # Loop through each script tag to find antiforgeryToken
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content and "antiforgeryToken" in script_content:
            # Extract the value of antiforgeryToken
            antiforgery_token = script_content.split('value="')[1].split('"')[0]
            break  # Exit the loop after finding the antiforgeryToken

    # Update to the latest antiforgery token for the next requests
    st.session_state.antiforgery_token = antiforgery_token

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="entity-list-view w-100")
    vocihtml = soup.find_all(class_="th-wrapper")
    tabletitles = [titoli.text for titoli in vocihtml]

    table = soup.find("table", class_="entity-list-view w-100")
    vocihtml = soup.find_all(class_="th-wrapper")
    tabletitles = [titoli.text for titoli in vocihtml]

    df = pd.DataFrame(columns=tabletitles)

    column_data = table.find_all("tr")
    skippedrows = 1

    for row in column_data[1:]:
        row_data = row.find_all("td")
        individual_row_data = [data.text.strip() for data in row_data]
        # print(individual_row_data)
        # print(len(individual_row_data), len(column_data))

        if len(individual_row_data) == len(df.columns):
            # Add the row to the DataFrame
            length = len(df)
            df.loc[length] = individual_row_data

        else:
            print(f"I had to Skip {skippedrows} row")
            skippedrows += 1
            continue

    df.rename(columns={"Tipo Giocatore Nuovo": "Date_String"}, inplace=True)
    df["Date_String"] = df["Data"]
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

    # Need to add a check and make it works anyway if there are missing values
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


# Function to perform the additional requests
# def handicap_request(selected_percorso, tee, hcp):
def handicap_request(tee, hcp):
    url = "http://areariservata.federgolf.it/CourseHandicapCalc/Index"
    headers = {
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    response = requests.get(url, headers=headers)

    print("First Request Response Status Code:", response.status_code)
    print("First Request Response Content:", response.content.decode())

    if response.status_code != 200:
        return False

    # Get the info from the html for the new antiforgery token since it changes every time we have to get the new one
    # ----------------------------------------
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    antiforgery_token = ""
    # Find all script tags in the HTML
    script_tags = soup.find_all("script")

    # Loop through each script tag to find antiforgeryToken
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content and "antiforgeryToken" in script_content:
            # Extract the value of antiforgeryToken
            antiforgery_token = script_content.split('value="')[1].split('"')[0]
            break  # Exit the loop after finding the antiforgeryToken

    # Update to the latest antiforgery token for the next requests
    st.session_state.antiforgery_token = antiforgery_token

    ## Second Request
    selected_circolo = "0a68d8fc-4339-4f92-889d-fbc60747d7bb"
    selected_percorso = "c409a93b-af1b-43c6-b735-00bf5d612885"

    # Set the request headers
    headers = {
        "Host": "areariservata.federgolf.it",
        "Cookie": f"ASP.NET_SessionId={st.session_state.session_id}; __RequestVerificationToken={st.session_state.request_verification_token}; ARRAffinity={st.session_state.arraffinity}; ARRAffinitySameSite={st.session_state.arraffinity_same_site}",
        "Content-Length": "260",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://areariservata.federgolf.it",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://areariservata.federgolf.it/CourseHandicapCalc/Calc",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    # Set the request data
    data = {
        "selectedCircolo": selected_circolo,
        "SelectedPercorso": selected_percorso,
        "tee": tee,
        "hcp": hcp,
        "__RequestVerificationToken": {st.session_state.antiforgery_token},
    }

    print(selected_circolo)
    print(selected_percorso)
    print(st.session_state.session_id)
    print(st.session_state.request_verification_token)
    print(st.session_state.antiforgery_token)
    print(st.session_state.arraffinity)
    print(st.session_state.arraffinity_same_site)

    # Make the POST request
    response = requests.post(
        "https://areariservata.federgolf.it/CourseHandicapCalc/Calc",
        headers=headers,
        data=data,
    )

    print("Second Request Response Status Code:", response.status_code)
    print("Second Request Response Content:", response.content.decode())

    if response.status_code != 200:
        return None

    return response.content
