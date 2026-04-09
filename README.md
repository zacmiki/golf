# FederGolf Companion

A Streamlit application for viewing and analyzing your FederGolf (Italian Golf Federation) handicap and game statistics.

## Features

- Secure login to FederGolf Area Riservata
- View your official game results and handicap progression
- Analyze strokes distribution with Gaussian fit
- Handicap simulation and scenario planning
- Playing handicap calculation for different courses
- Responsive design for mobile and desktop use

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd golf
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run streamlit_app.py
```

2. Open your browser to `http://localhost:8501`

3. Login with your FederGolf credentials:
   - Username: Your FederGolf user ID
   - Password: Your FederGolf password

## Features Overview

### Official Rounds
- View your handicap progression over time
- See detailed statistics for each round
- Analyze strokes distribution with optional Gaussian fit

### Handicap Manager
- Manage and view course information
- Calculate playing handicaps for different tee boxes

### Handicap Simulation
- Simulate how future scores will affect your handicap
- Plan your golfing strategy based on handicap goals

### Playing Handicap
- Calculate your playing handicap for any course and tee combination
- Accounts for course rating, slope rating, and PCC

## How It Works

This application securely logs into the FederGolf Area Riservata portal to retrieve your personal golf data. Key improvements in this version:

- **User-Specific Data**: Each user sees their own name, tessera number, and golf data
- **Accurate Handicap Calculation**: Uses the official formula (best 8 of last 20 valid Score Differentials)
- **Proper Session Management**: Login/logout correctly handles user sessions to prevent data mixing
- **Dynamic Data Extraction**: Automatically finds your profile ID and extracts data from your personal pages

## Technical Details

- Built with Streamlit for rapid web app development
- Uses BeautifulSoup for web scraping FederGolf data
- Pandas for data manipulation and analysis
- Plotly for interactive visualizations
- Requests for HTTP communication with FederGolf servers

## Configuration

The application automatically handles:
- Session cookie management
- Anti-forgery token extraction
- Secure credential handling
- Dynamic user profile detection

## Requirements

See `requirements.txt` for the complete list of Python dependencies.

## Privacy & Security

- Your credentials are used only to log into FederGolf and retrieve your data
- No data is stored permanently on the server running this application
- Session data is cleared upon logout
- The application runs client-side in your browser (except for the initial data fetch)

## Contributing

Feel free to submit issues or pull requests to improve this application.

## License

MIT License - feel free to use and modify this code for your personal use.

## Acknowledgments

- Thanks to FederGolf for providing the golf data portal
- Built with Streamlit, the fastest way to build data apps