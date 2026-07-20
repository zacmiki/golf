from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

PRIVATE_BASE_URL = "https://areariservata.federgolf.it"
PUBLIC_BASE_URL = "https://www.federgolf.it"
COURSE_CALCULATOR_URL = f"{PUBLIC_BASE_URL}/settore-tecnico/calcolo-hcp/"
COURSE_AJAX_URL = f"{PUBLIC_BASE_URL}/wp-admin/admin-ajax.php"
RATINGS_URL = f"{PRIVATE_BASE_URL}/SlopeAndCourseRating/Index"
DEFAULT_TIMEOUT = 20

RESULT_NUMERIC_COLUMNS = (
    "Index Nuovo",
    "Index Vecchio",
    "Variazione",
    "AGS",
    "Par",
    "Playing HCP",
    "CR",
    "SR",
    "Stbl",
    "Buche",
    "Numero tessera",
    "SD",
    "Corr SD",
)

RATING_COLUMNS = (
    "Circolo",
    "Percorso",
    "PAR",
    "CR Nero Uomini",
    "Slope Nero Uomini",
    "CR Bianco Uomini",
    "Slope Bianco Uomini",
    "CR Giallo Uomini",
    "Slope Giallo Uomini",
    "CR Verde Uomini",
    "Slope Verde Uomini",
    "CR Blu Donne",
    "Slope Blu Donne",
    "CR Rosso Donne",
    "Slope Rosso Donne",
    "CR Arancio Donne",
    "Slope Arancio Donne",
)


class FederGolfError(RuntimeError):
    """Raised when FederGolf returns an unexpected or unusable response."""


@dataclass(frozen=True)
class CourseHandicapResult:
    course: str
    course_rating: float
    slope_rating: float
    tee: str
    course_handicap: int
    limitation: int | None = None


@dataclass(frozen=True)
class MemberResults:
    dataframe: pd.DataFrame
    player_name: str
    membership_number: str
    current_handicap: float | None


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": "FederGolf-Companion/1.0 (+https://github.com/)",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
    }


def extract_antiforgery_token(soup: BeautifulSoup) -> str:
    token = soup.select_one('input[name="__RequestVerificationToken"]')
    if isinstance(token, Tag) and token.get("value"):
        return str(token["value"])

    for script in soup.find_all("script"):
        content = script.string or script.get_text(" ", strip=True)
        match = re.search(
            r'name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)',
            content,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return ""


def _response_soup(response: requests.Response, context: str) -> BeautifulSoup:
    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FederGolfError(f"{context} failed: HTTP {response.status_code}") from exc
    return BeautifulSoup(response.content, "html.parser")


def _request(
    session: requests.Session,
    method: str,
    url: str,
    context: str,
    **kwargs: Any,
) -> requests.Response:
    try:
        return session.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise FederGolfError(f"{context} failed: {exc.__class__.__name__}") from exc


def _normalize_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.strip().str.replace(",", ".", regex=False),
        errors="coerce",
    )


def parse_results_table(soup: BeautifulSoup) -> pd.DataFrame:
    """Parse the results table by its semantic headers, not its CSS layout."""
    required = {"Data", "Numero tessera", "SD", "Index Nuovo"}
    selected: Tag | None = None

    for table in soup.find_all("table"):
        headers = [cell.get_text(" ", strip=True) for cell in table.find_all("th")]
        if required.issubset(headers):
            selected = table
            break

    if selected is None:
        raise FederGolfError(
            "FederGolf results table was not found or its columns changed"
        )

    headers = [cell.get_text(" ", strip=True) for cell in selected.find_all("th")]
    rows: list[list[str]] = []
    for row in selected.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
        if len(cells) == len(headers):
            rows.append(cells)

    if not rows:
        raise FederGolfError("FederGolf returned an empty results table")

    dataframe = pd.DataFrame(rows, columns=headers)
    for column in RESULT_NUMERIC_COLUMNS:
        if column in dataframe:
            dataframe[column] = _normalize_number(dataframe[column])

    parsed_dates = pd.to_datetime(dataframe["Data"], dayfirst=True, errors="coerce")
    dataframe = dataframe.assign(_parsed_date=parsed_dates)
    dataframe = dataframe[dataframe["_parsed_date"].notna()].copy()
    if "Valida" in dataframe:
        dataframe = dataframe[
            dataframe["Valida"].astype(str).str.strip().str.upper().eq("S")
        ].copy()

    dataframe = dataframe.sort_values(
        "_parsed_date", ascending=False, kind="stable"
    ).reset_index(drop=True)
    if dataframe.empty:
        raise FederGolfError("FederGolf returned no valid, dated results")
    dataframe["Data"] = dataframe.pop("_parsed_date").dt.strftime("%Y-%m-%d")
    return dataframe


def _extract_player_name(soup: BeautifulSoup) -> str:
    logout = soup.find("a", href=re.compile(r"/Home/Logout", re.IGNORECASE))
    if logout:
        nav = logout.find_parent("nav")
        if nav:
            candidates = [
                item.get_text(" ", strip=True)
                for item in nav.find_all("li")
                if item.get_text(" ", strip=True)
            ]
            if candidates:
                return candidates[0]
    return "Golfer"


class MemberClient:
    """Authenticated client for a member's private result history."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(_default_headers())
        self.timeout = timeout
        self.player_name = "Golfer"

    def authenticate(self, username: str, password: str) -> None:
        login_url = f"{PRIVATE_BASE_URL}/"
        response = _request(
            self.session,
            "GET",
            login_url,
            "Loading the FederGolf login page",
            timeout=self.timeout,
        )
        soup = _response_soup(response, "Loading the FederGolf login page")
        token = extract_antiforgery_token(soup)
        if not token:
            raise FederGolfError("FederGolf login form token was not found")

        response = _request(
            self.session,
            "POST",
            f"{PRIVATE_BASE_URL}/Home/AuthenticateUser",
            "FederGolf login",
            data={
                "User": username,
                "Password": password,
                "__RequestVerificationToken": token,
            },
            headers={"Referer": login_url},
            timeout=self.timeout,
        )
        soup = _response_soup(response, "FederGolf login")
        login_form = soup.select_one("form.login-form")
        logout_link = soup.find("a", href=re.compile(r"/Home/Logout", re.IGNORECASE))
        if login_form is not None or logout_link is None:
            raise FederGolfError("FederGolf rejected the credentials")
        self.player_name = _extract_player_name(soup)

    def get_results(self) -> MemberResults:
        response = _request(
            self.session,
            "GET",
            f"{PRIVATE_BASE_URL}/Risultati/ShowGrid",
            "Loading FederGolf results",
            headers={"Referer": f"{PRIVATE_BASE_URL}/Home/AuthenticateUser"},
            timeout=self.timeout,
        )
        soup = _response_soup(response, "Loading FederGolf results")
        dataframe = parse_results_table(soup)

        membership_numbers = dataframe["Numero tessera"].dropna()
        if membership_numbers.empty:
            raise FederGolfError("FederGolf returned results without a membership number")
        membership = str(int(membership_numbers.iloc[0]))
        current = dataframe["Index Nuovo"].dropna()
        current_handicap = float(current.iloc[0]) if not current.empty else None
        return MemberResults(
            dataframe=dataframe,
            player_name=self.player_name,
            membership_number=membership,
            current_handicap=current_handicap,
        )


class CourseCatalogClient:
    """Client for FederGolf's public, unauthenticated course JSON service."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(_default_headers())
        self.timeout = timeout

    def list_clubs(self) -> dict[str, str]:
        response = _request(
            self.session,
            "GET",
            COURSE_CALCULATOR_URL,
            "Loading FederGolf clubs",
            timeout=self.timeout,
        )
        soup = _response_soup(response, "Loading FederGolf clubs")
        clubs = self._options(soup.select("#circolo option"))
        if not clubs:
            raise FederGolfError("FederGolf returned no clubs; the calculator changed")
        return clubs

    def list_courses(self, club_id: str) -> dict[str, str]:
        payload = self._post_json("club-courses", club_id=club_id)
        courses = {
            str(item["nome_percorso"]).strip(): str(item["percorso_id"])
            for item in self._dict_items(payload, "courses")
            if item.get("nome_percorso") and item.get("percorso_id")
        }
        if not courses:
            raise FederGolfError("FederGolf returned no courses for this club")
        return courses

    def list_tees(self, course_id: str) -> dict[str, str]:
        payload = self._post_json("courses-tees", percorso_id=course_id)
        tees: dict[str, str] = {}
        if not isinstance(payload, list):
            raise FederGolfError("FederGolf returned an invalid tee response")
        for item in payload:
            if isinstance(item, list) and len(item) >= 2:
                tees[str(item[1]).strip().title()] = str(item[0]).strip()
        if not tees:
            raise FederGolfError("FederGolf returned no tees for this course")
        return tees

    def calculate_handicap(
        self,
        club_id: str,
        course_id: str,
        tee: str,
        handicap: float,
    ) -> list[CourseHandicapResult]:
        payload = self._post_json(
            "course-handicap",
            club_id=club_id,
            percorso_id=course_id,
            tee=tee,
            handicap=f"{handicap:.1f}",
        )
        if not isinstance(payload, list):
            raise FederGolfError("FederGolf returned an invalid handicap response")

        results: list[CourseHandicapResult] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 5:
                continue
            try:
                results.append(
                    CourseHandicapResult(
                        course=str(row[0]),
                        course_rating=float(row[1]),
                        slope_rating=float(row[2]),
                        tee=str(row[3]),
                        course_handicap=int(row[4]),
                        limitation=int(row[5]) if len(row) > 5 else None,
                    )
                )
            except (TypeError, ValueError):
                continue
        if not results:
            raise FederGolfError("FederGolf returned no handicap result")
        return results

    def list_ratings(self) -> pd.DataFrame:
        response = _request(
            self.session,
            "GET",
            RATINGS_URL,
            "Loading FederGolf course ratings",
            timeout=self.timeout,
        )
        soup = _response_soup(response, "Loading FederGolf course ratings")
        table = soup.select_one("table.single-table.slope")
        if table is None:
            raise FederGolfError("FederGolf rating table was not found")

        rows: list[list[str]] = []
        for row in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) == len(RATING_COLUMNS):
                rows.append(cells)
        if not rows:
            raise FederGolfError("FederGolf returned an empty rating table")
        return pd.DataFrame(rows, columns=RATING_COLUMNS)

    @staticmethod
    def _options(options: Iterable[Tag]) -> dict[str, str]:
        return {
            option.get_text(" ", strip=True): str(option.get("value", "")).strip()
            for option in options
            if str(option.get("value", "")).strip()
        }

    @staticmethod
    def _dict_items(payload: Any, name: str) -> list[dict[str, Any]]:
        if not isinstance(payload, list) or not all(
            isinstance(item, dict) for item in payload
        ):
            raise FederGolfError(f"FederGolf returned an invalid {name} response")
        return payload

    def _post_json(self, action: str, **data: str) -> Any:
        try:
            response = _request(
                self.session,
                "POST",
                COURSE_AJAX_URL,
                f"Loading FederGolf {action}",
                data={"action": action, **data},
                headers={"Referer": COURSE_CALCULATOR_URL},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except (FederGolfError, requests.RequestException, ValueError) as exc:
            raise FederGolfError(
                f"FederGolf public service failed while loading {action}"
            ) from exc


def par_from_course_name(course_name: str) -> float | None:
    match = re.search(r"\bPar\s*(\d{2})\b", course_name, re.IGNORECASE)
    return float(match.group(1)) if match else None
