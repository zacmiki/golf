import requests
import streamlit as st
from bs4 import BeautifulSoup

from .hcp_functions import compute_handicap


# Function to perform the additional requests
def handicap_request():
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

    # print("First Request Response Status Code:", response.status_code)
    # print("First Request Response Content:", response.content.decode())

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

    # Get the necessaary information for the next requests from the cookies
    # ----------------------------------------
    request_verification_token = response.cookies.get("__RequestVerificationToken")
    st.session_state.request_verification_token = request_verification_token

    arraffinity = response.cookies.get("ARRAffinity")
    st.session_state.arraffinity = arraffinity

    arraffinity_same_site = response.cookies.get("ARRAffinitySameSite")
    st.session_state.arraffinity_same_site = arraffinity_same_site

    # Get Session id from the cookies
    session_id = response.cookies.get("ASP.NET_SessionId", None)
    st.session_state.session_id = session_id

    st.subheader("Playing Handicap Calculator")

    # Get the course with the soup from before
    # Parse the HTML content
    # Extract Circolo options as a mapping with a dictionary for fast lookup
    circolo_options = {}
    options = soup.select("#ddlCircolo option")
    for option in options:
        name = option.text.strip()
        value = option["value"]
        circolo_options[name] = value

    selected_circolo = st.selectbox(
        "Select Circolo Option", options=list(circolo_options.keys())
    )

    # Getting the value based on the selected name
    selected_circolo_value = circolo_options[selected_circolo]

    # Make the other request for the Percorso
    url = "https://areariservata.federgolf.it/CourseHandicapCalc/Calc"

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
        "Referer": "https://areariservata.federgolf.it/CourseHandicapCalc/Index",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Connection": "close",
    }

    data = {
        "selectedCircolo": selected_circolo_value,
        "SelectedPercorso": "",
        "tee": "",
        "hcp": "",
        "__RequestVerificationToken": st.session_state.antiforgery_token,
    }

    response = requests.post(url, headers=headers, data=data)

    if selected_circolo_value:
        # Get the soup and select the Percorso
        soup = BeautifulSoup(response.text, "html.parser")
        course_options = {}
        course_select = soup.select("#ddlPercorso option")
        for option in course_select:
            name = option.text.strip()
            value = option["value"]
            course_options[name] = value

        # Dropdown for selecting the course
        selected_course = st.selectbox(
            "Select Course", options=list(course_options.keys())
        )

        # Getting the value based on the selected course name
        selected_course_value = course_options[selected_course]

        # Dropdown for Giallo and Rosso
        tee_color = st.selectbox(
            "Select Tee Color",
            options=["Bianco", "Giallo", "Verde", "Blu", "Rosso", "Arancio"],
        )

        # Text field for handicap
        handicap = st.text_input("Enter Handicap")

        # Button to trigger the request
        if st.button("Compute Handicap"):
            url = "https://areariservata.federgolf.it/CourseHandicapCalc/Calc"

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
                "Referer": "https://areariservata.federgolf.it/CourseHandicapCalc/Index",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Priority": "u=0, i",
                "Connection": "close",
            }

            data = {
                "selectedCircolo": selected_circolo_value,
                "SelectedPercorso": selected_course_value,
                "tee": tee_color,
                "hcp": handicap,
                "__RequestVerificationToken": st.session_state.antiforgery_token,
            }

            response = requests.post(url, headers=headers, data=data)

            # print("Second Request Response Status Code:", response.status_code)
            # print("Second Request Response Content:", response.content.decode())

            # if response.status_code != 200:
            #     return None

            # Get course handicap
            course_handicap = None

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the table by its id
            table = soup.find("table", id="risultatiHCP")

            # Get all rows in the tbody
            rows = table.find_all("tr")

            # Loop through the rows to find the Course Handicap
            for row in rows:
                columns = row.find_all("td")
                if columns:
                    course_handicap = columns[4].get_text(
                        strip=True
                    )  # 5th column is the Course Handicap

            st.markdown(f"Course Handicap: {course_handicap}")

            compute_handicap(
                course_handicap,
                selected_circolo_value,
                selected_course_value,
                tee_color,
                handicap,
            )
