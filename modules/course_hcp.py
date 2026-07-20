from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .federgolf_client import (
    CourseCatalogClient,
    CourseHandicapResult,
    FederGolfError,
    par_from_course_name,
)

VALID_ROUNDS = 20


@dataclass(frozen=True)
class CourseSelection:
    club: str
    club_id: str
    course: str
    course_id: str
    tee: str


@st.cache_data(ttl=86400, max_entries=2, show_spinner=False)
def get_ratings() -> pd.DataFrame:
    return CourseCatalogClient().list_ratings()


@st.cache_data(ttl=86400, max_entries=2, show_spinner=False)
def get_clubs() -> dict[str, str]:
    return CourseCatalogClient().list_clubs()


@st.cache_data(ttl=86400, max_entries=300, show_spinner=False)
def get_courses(club_id: str) -> dict[str, str]:
    return CourseCatalogClient().list_courses(club_id)


@st.cache_data(ttl=86400, max_entries=1000, show_spinner=False)
def get_tees(course_id: str) -> dict[str, str]:
    return CourseCatalogClient().list_tees(course_id)


def select_course(key: str) -> CourseSelection | None:
    """Render the shared club/course/tee controls."""
    try:
        clubs = get_clubs()
        club = st.selectbox("Select club", clubs, key=f"{key}_club")
        courses = get_courses(clubs[club])
        course = st.selectbox("Select course", courses, key=f"{key}_course")
        tees = get_tees(courses[course])
        tee = st.selectbox("Select tee", tees, key=f"{key}_tee")
        return CourseSelection(club, clubs[club], course, courses[course], tees[tee])
    except FederGolfError as exc:
        st.error(str(exc))
        return None


def course_details(
    selection: CourseSelection, handicap: float
) -> CourseHandicapResult:
    return CourseCatalogClient().calculate_handicap(
        selection.club_id,
        selection.course_id,
        selection.tee,
        handicap,
    )[0]


@st.cache_data(ttl=86400, max_entries=3000, show_spinner=False)
def course_rating(selection: CourseSelection) -> CourseHandicapResult:
    """Cache public CR/SR metadata independently of a player's handicap."""
    return course_details(selection, 0.0)


def course_par(selection: CourseSelection) -> float | None:
    par = par_from_course_name(selection.course)
    if par is not None:
        return par
    try:
        ratings = get_ratings()
        match = ratings[
            ratings["Circolo"].str.casefold().eq(selection.club.casefold())
            & ratings["Percorso"].str.casefold().eq(selection.course.casefold())
        ]
        return None if match.empty else float(match.iloc[0]["PAR"])
    except (FederGolfError, KeyError, TypeError, ValueError):
        return None
