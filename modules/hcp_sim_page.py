import streamlit as st

# THE PAGE DISPLAY --------------------------------------
def hcp_sim(dff):
    import numpy as np
    import pandas as pd

    df = pd.DataFrame(dff)
        
    st.title("🧮 New HCP Calculator")
    st.divider()

    current_handicap = df["Index Nuovo"][0]
    best_handicap = df["Index Nuovo"].min()

    st.success(
        f"\n\n#### 🏌️ Tesserato {df['Tesserato'][0]}"
        + f"\n\n#### ⛳️ Current HCP: {current_handicap}  ⛳️",
    )
    
    getallcourses()


def compute_handicap(
    course_handicap, selected_circolo_value, selected_course_value, tee_color, handicap
):
    pass

# ---------------------------------------

# New HCP Calculator --------
def new_hcp(df, punti_stbl):
    import numpy as np
    import pandas as pd

    filtered_df = df.dropna(subset=["SD"]).head(20)
    valid_results_SD = filtered_df['SD'].values
    
    migliori_8 = np.sort(valid_results_SD)[:8]
    
    #Da Ricevere:
    par_percorso = 70
    sr_percorso = 126
    cr_percorso = 70.3
    #punti_stbl = 35
    playing_hcp = 16
    
    new_sd = (113/sr_percorso) * (par_percorso + playinghcp - (punti_stbl - 36) - cr_percorso)
    
    migliori_8 = np.append(migliori_8, new_sd)
    best_8_SD = np.sort(migliori_8)[:8]
    hcpsimulato = np.mean(best_8_SD)
    
    return new_sd, hcpsimulato
# -------------------------------------

def getallcourses():
    # GET THE TABLE OF ALL COURSES OFFICIALLY REGISTERED TO FEDERGOLF
    # returns - Percorso Par / SR / CR /
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    
    url = "https://areariservata.federgolf.it/SlopeAndCourseRating/Index"
    
    # Fetch the HTML content from the URL
    response = requests.get(url)
    html_content = response.text
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_ ="single-table slope responsive")
    
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
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    # Extract headers
    headers = [th.text.strip() for th in rows[0].find_all('th')]
    
    # Extract data rows
    data = []
    
    for row in rows[1:]:
        data.append([td.text.strip() for td in row.find_all(['th', 'td'])])
        
    # Create Pandas DataFrame
    allcourses_df = pd.DataFrame(data, columns=headers)
    
    column_data = table.find_all('tr')
    skippedrows = 3
    
    for row in column_data[3:]:
        row_data = row.find_all('td')
        individual_row_data = [data.text.strip() for data in row_data]
        
        if len(individual_row_data) == len(allcourses_df.columns):
            # Add the row to the DataFrame
            length = len(allcourses_df)
            allcourses_df.loc[length] = individual_row_data
        else:
            print(f"I had to Skip {skippedrows} row")
            skippedrows +=1
            continue
            
    st.write(f"Created and loaded a dataframe made of {len(allcourses_df)} courses")
    st.session_state.allcourses_df = allcourses_df
    
    return allcourses_df
