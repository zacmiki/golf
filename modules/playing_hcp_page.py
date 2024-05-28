import streamlit as st
import requests
from bs4 import BeautifulSoup
from .login_federgolf import generate_headers

def playing_hcp():
	st.title("⛳️ Playing HCP Calculator")
	st.caption("The program takes your current EGA as the starting value to calculate the playing handicap.  \nJust input a different number to check the playing handicap for that specific EGA")
	playing_handicap()
	st.divider()
	st.markdown(
	"""
    <a href="https://buymeacoffee.com/miczac?l=it" target="_blank">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YourUsername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff">
    </a>
    """,
    unsafe_allow_html=True,
    )   

def playing_handicap():
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
        st.error("Failed to fetch data from the server.")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    antiforgery_token = ""
    script_tags = soup.find_all("script")
    for script_tag in script_tags:
        script_content = script_tag.string
        if script_content and "antiforgeryToken" in script_content:
            antiforgery_token = script_content.split('value="')[1].split('"')[0]
            break

    request_verification_token = response.cookies.get("__RequestVerificationToken")
    arraffinity = response.cookies.get("ARRAffinity")
    arraffinity_same_site = response.cookies.get("ARRAffinitySameSite")
    session_id = response.cookies.get("ASP.NET_SessionId")

    st.session_state.session_id = session_id
    st.session_state.request_verification_token = request_verification_token
    st.session_state.arraffinity = arraffinity
    st.session_state.arraffinity_same_site = arraffinity_same_site
    st.session_state.antiforgery_token = antiforgery_token

    circolo_options = {}
    options = soup.select("#ddlCircolo option")
    for option in options:
        name = option.text.strip()
        value = option["value"]
        circolo_options[name] = value

    selected_circolo = st.selectbox("Select Circolo Option", options=list(circolo_options.keys()))

    selected_circolo_value = circolo_options[selected_circolo]

    if selected_circolo_value:
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

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            course_options = {}
            course_select = soup.select("#ddlPercorso option")
            for option in course_select:
                name = option.text.strip()
                value = option["value"]
                course_options[name] = value

            selected_course = st.selectbox("Select Course", options=list(course_options.keys()))
            selected_course_value = course_options[selected_course]

            tee_color = st.selectbox(
                "Select Tee Color",
                options=["Bianco", "Giallo", "Verde", "Blu", "Rosso", "Arancio"],
            )

            handicap = st.number_input(":green[Enter The Playing Index]", min_value = -6.0, max_value = 54.0, value = st.session_state.df['Index Nuovo'][0])

            if st.button("Compute Playing Handicap"):
                url = "https://areariservata.federgolf.it/CourseHandicapCalc/Calc"

                data = {
                    "selectedCircolo": selected_circolo_value,
                    "SelectedPercorso": selected_course_value,
                    "tee": tee_color,
                    "hcp": handicap,
                    "__RequestVerificationToken": st.session_state.antiforgery_token,
                }

                response = requests.post(url, headers=headers, data=data)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    table = soup.find("table", id="risultatiHCP")
                    rows = table.find_all("tr")

                    playing_hcp = None
                    for row in rows:
                        columns = row.find_all("td")
                        if columns:
                            playing_hcp = columns[4].get_text(strip=True)

                    st.info(f"#### Playing Hcp = {playing_hcp}")
                else:
                    st.error("Failed to compute handicap.")
        else:
            st.error("Failed to fetch course data.")
    else:
        st.error("Please select a Circolo option.")
