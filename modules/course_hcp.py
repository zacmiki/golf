import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from .login_federgolf import generate_headers


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

    st.subheader("Handicap Calculator")

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

    cookies = {
        "ASP.NET_SessionId": st.session_state.session_id,
        "__RequestVerificationToken": st.session_state.request_verification_token,
        "ARRAffinity": st.session_state.arraffinity,
        "ARRAffinitySameSite": st.session_state.arraffinity_same_site,
    }

    headers = generate_headers(
        cookies=cookies,
        referer="https://areariservata.federgolf.it/CourseHandicapCalc/Index",
        content_length=260,
    )

    data = {
        "selectedCircolo": selected_circolo_value,
        "SelectedPercorso": "",
        "tee": "",
        "hcp": "",
        "__RequestVerificationToken": st.session_state.antiforgery_token,
    }

    response = requests.post(url, headers=headers, data=data)

    if selected_circolo_value:
        soup = BeautifulSoup(response.text, "html.parser")
        course_options = {}
        course_select = soup.select("#ddlPercorso option")
        for option in course_select:
            name = option.text.strip()
            value = option["value"]
            course_options[name] = value

        selected_course = st.selectbox(
            "Select Course", options=list(course_options.keys())
        )

        selected_course_value = course_options[selected_course]
        tee_color = st.selectbox(
            "Select Tee Color",
            options=["Bianco", "Giallo", "Verde", "Blu", "Rosso", "Arancio"],
        )

        handicap = st.session_state.df["Index Nuovo"][0]

        # Get punti_stbl from user
        st.session_state.punti_stbl = st.text_input("Entrai il Punteggion Stableford")

        if st.button("Compute Handicap"):
            url = "https://areariservata.federgolf.it/CourseHandicapCalc/Calc"

            headers = generate_headers(
                cookies=cookies,
                referer="https://areariservata.federgolf.it/CourseHandicapCalc/Index",
                content_length=260,
            )

            data = {
                "selectedCircolo": selected_circolo_value,
                "SelectedPercorso": selected_course_value,
                "tee": tee_color,
                "hcp": handicap,
                "__RequestVerificationToken": st.session_state.antiforgery_token,
            }

            response = requests.post(url, headers=headers, data=data)

            playing_hcp = None
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", id="risultatiHCP")
            rows = table.find_all("tr")

            for row in rows:
                columns = row.find_all("td")
                if columns:
                    playing_hcp = columns[4].get_text(strip=True)

                    # Find the index of the first space after the dash

            # Get the index of the dash
            index = selected_course.index("-") + 2

            # st.markdown(f"Course Handicap: {course_handicap}")
            st.session_state.circolo = selected_circolo
            # Extract only the second part after the dash
            st.session_state.percorso = selected_course[index:]
            st.session_state.playing_hcp = playing_hcp


@st.cache_data
def get_allcourses():
    # GET THE TABLE OF ALL COURSES OFFICIALLY REGISTERED TO FEDERGOLF
    # returns - Percorso Par / SR / CR /

    url = "https://areariservata.federgolf.it/SlopeAndCourseRating/Index"

    # Fetch the HTML content from the URL
    response = requests.get(url)
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="single-table slope responsive")

    # Assuming `html_content` contains the HTML content of the table
    html_content = """
    <tr>
    <th>Circolo</th>
    <th>Percorso</th>
    <th align="center">PAR</th>
    <th align="center">CR Nero Uomini</th>
    <th align="center">Slope Nero Uomini</th>
    <th align="center">CR Bianco Uomini</th>
    <th align="center">Slope Bianco Uomini</th>
    <th align="center">CR Giallo Uomini</th>
    <th align="center">Slope Giallo Uomini</th>
    <th align="center">CR Verde Uomini</th>
    <th align="center">Slope Verde Uomini</th>
    <th align="center">CR Blu Donne</th>
    <th align="center">Slope Blu Donne</th>
    <th align="center">CR Rosso Donne</th>
    <th align="center">Slope Rosso Donne</th>
    <th align="center">CR Arancio Donne</th>
    <th align="center">Slope Arancio Donne</th>
    </tr>
    """

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all table rows
    rows = soup.find_all("tr")

    # Extract headers
    headers = [th.text.strip() for th in rows[0].find_all("th")]

    # Extract data rows
    data = []

    for row in rows[1:]:
        data.append([td.text.strip() for td in row.find_all(["th", "td"])])

    # Create Pandas DataFrame
    allcourses_df = pd.DataFrame(data, columns=headers)

    column_data = table.find_all("tr")
    skippedrows = 3

    for row in column_data[3:]:
        row_data = row.find_all("td")
        individual_row_data = [data.text.strip() for data in row_data]

        if len(individual_row_data) == len(allcourses_df.columns):
            # Add the row to the DataFrame
            length = len(allcourses_df)
            allcourses_df.loc[length] = individual_row_data
        else:
            # print(f"I had to Skip {skippedrows} row")
            skippedrows += 1
            continue

    # st.write(f"Created and loaded a dataframe made of {len(allcourses_df)} courses")
    # st.session_state.allcourses_df = allcourses_df

    return allcourses_df
