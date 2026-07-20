# FederGolf Companion

A Streamlit application for viewing and analyzing your FederGolf (Italian Golf Federation) handicap and game statistics.

## Features

- Secure login to FederGolf Area Riservata
- View your official game results and handicap progression
- Analyze strokes distribution with Gaussian fit
- Review recent form, consistency, counting rounds, PCC, and format trends
- Handicap simulation and scenario planning
- Playing handicap calculation for different courses
- Responsive design for mobile and desktop use

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd golf
```

2. Install the locked dependencies with [uv](https://docs.astral.sh/uv/):
```bash
uv sync
```

## Usage

1. Run the application:
```bash
uv run streamlit run streamlit_app.py
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
- See which of the latest 20 rounds count toward your Index
- Identify the next round and counting score due to expire

### Handicap Simulation
- Simulate how future scores will affect your handicap
- Plan your golfing strategy based on handicap goals

### Course Handicap
- Load current clubs, courses, and tees from FederGolf's public calculator
- Calculate a Course Handicap from the selected ratings and Handicap Index

## How It Works

This application securely logs into the FederGolf Area Riservata portal to retrieve your personal golf data. Key improvements in this version:

- **User-Specific Data**: Each user sees their own name, tessera number, and golf data
- **Transparent Projections**: Simulates the best 8 of the latest 20 valid Score Differentials
- **Proper Session Management**: Login/logout correctly handles user sessions to prevent data mixing
- **Resilient Extraction**: Reads the authenticated results table by semantic column names rather than fragile page layout or profile URLs

## Technical Details

- Built with Streamlit for rapid web app development
- Uses BeautifulSoup for web scraping FederGolf data
- Pandas for data manipulation and analysis
- NumPy and Plotly for calculations and interactive visualizations
- Requests for HTTP communication with FederGolf servers

## Configuration

The application automatically handles:
- Session cookie management
- Anti-forgery token extraction
- Secure credential handling
- Semantic results-table detection and newest-first ordering

## Development and validation

```bash
uv sync --dev
uv run ruff check .
uv run pytest -m "not live"
```

The weekly GitHub Actions smoke test checks only FederGolf's public course
endpoints. It uses no account, password, repository secret, or other
authentication. Authenticated checks remain local and credentials are never
written to disk or committed.

### Streamlit Cloud caching

Public course metadata uses bounded 24-hour shared caches. Member identity,
authenticated HTTP sessions, and round data remain only in each user's
`st.session_state` and are cleared on logout. Private data is never placed in a
shared cache, and only the selected page performs work.

## Privacy & Security

- Your credentials are used only to log into FederGolf and retrieve your data
- No data is stored permanently on the server running this application
- Session data is cleared upon logout
- The password is used for login and is not retained in Streamlit state or on disk
- FederGolf requests run on the Streamlit server; the browser displays the app

## Contributing

Feel free to submit issues or pull requests to improve this application.

## License

MIT License - feel free to use and modify this code for your personal use.

## Acknowledgments

- Thanks to FederGolf for providing the golf data portal
- Built with Streamlit, the fastest way to build data apps
