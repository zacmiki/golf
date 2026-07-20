from __future__ import annotations

import os

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from modules.federgolf_client import (
    CourseCatalogClient,
    extract_antiforgery_token,
    par_from_course_name,
    parse_results_table,
)
from modules.hcp_manager_page import handicap_window
from modules.hcp_sim_page import simulate_handicap
from modules.insights_page import (
    counting_rounds,
    potential_exceptional_rounds,
    summarize_performance,
)
from modules.rounds_page import strokes_distribution


def _results_html(rows: str) -> str:
    return f"""
    <table class="whatever-the-site-calls-it-next">
      <thead><tr>
        <th>Data</th><th>Numero tessera</th><th>Gara</th><th>Valida</th>
        <th>Formula</th><th>AGS</th><th>SD</th><th>Index Nuovo</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


def test_extract_antiforgery_token_from_input() -> None:
    soup = BeautifulSoup(
        '<input name="__RequestVerificationToken" value="token-123">',
        "html.parser",
    )
    assert extract_antiforgery_token(soup) == "token-123"


def test_results_are_filtered_and_sorted_newest_first() -> None:
    soup = BeautifulSoup(
        _results_html(
            """
            <tr><td>02/01/2026</td><td>12345</td><td>B</td><td>S</td><td>18H</td><td>90</td><td>15,2</td><td>12,4</td></tr>
            <tr><td>05/01/2026</td><td>12345</td><td>C</td><td>N</td><td>18H</td><td>88</td><td>14.1</td><td>12.1</td></tr>
            <tr><td>10/01/2026</td><td>12345</td><td>D</td><td>S</td><td>18H</td><td>87</td><td>13.8</td><td>11.9</td></tr>
            <tr><td>31/12/2025</td><td>12345</td><td>A</td><td>S</td><td>18H</td><td>91</td><td>16.0</td><td>12.8</td></tr>
            """
        ),
        "html.parser",
    )

    result = parse_results_table(soup)

    assert result["Data"].tolist() == ["2026-01-10", "2026-01-02", "2025-12-31"]
    assert result["Gara"].tolist() == ["D", "B", "A"]
    assert result["SD"].tolist() == [13.8, 15.2, 16.0]
    assert pd.api.types.is_numeric_dtype(result["Index Nuovo"])


def test_course_par_is_read_from_the_selected_course() -> None:
    assert par_from_course_name("18 Buche Par 71") == 71.0
    assert par_from_course_name("Seconde Nove Par 36") == 36.0
    assert par_from_course_name("Prime Nove") is None


def test_performance_insights_use_newest_rounds_and_last_365_days() -> None:
    recent_dates = pd.to_datetime(
        ["2026-01-01", "2025-12-20", "2025-12-01", "2025-11-10", "2025-10-20"]
    )
    old_dates = pd.to_datetime(
        [
            pd.Timestamp("2024-12-01") - pd.DateOffset(days=20 * index)
            for index in range(16)
        ]
    )
    dates = recent_dates.append(old_dates)
    dataframe = pd.DataFrame(
        {
            "Data": dates.strftime("%Y-%m-%d"),
            "SD": [10.0, 11.0, 12.0, 13.0, 14.0] + [20.0] * 16,
            "Index Nuovo": [12.0, 11.5, 11.0, 10.5, 10.0] + [9.0] * 16,
            "Index Vecchio": [18.0] + [12.0] * 20,
            "Gara": [f"Round {index}" for index in range(21)],
            "Formula": ["18H"] * 21,
        }
    )

    summary = summarize_performance(dataframe)
    selected = counting_rounds(dataframe)
    exceptional = potential_exceptional_rounds(dataframe)

    assert summary.current_handicap == 12.0
    assert summary.low_index_365 == 10.0
    assert summary.recent_sd_average == 12.0
    assert summary.previous_sd_average == 20.0
    assert summary.form_change == -8.0
    assert summary.best_eight_average == 15.0
    assert selected["Counting"].sum() == 8
    assert len(exceptional) == 1


def test_handicap_window_and_simulation_are_pure_calculations() -> None:
    dataframe = pd.DataFrame(
        {
            "Data": pd.date_range("2026-01-20", periods=21, freq="-1D").strftime(
                "%Y-%m-%d"
            ),
            "SD": [5.0] + [float(value) for value in range(10, 30)],
            "Index Nuovo": [12.0] * 21,
            "Formula": ["L4M"] + ["18H"] * 20,
            "Gara": [f"Round {index}" for index in range(21)],
            "Stbl": [36.0] * 21,
            "AGS": [84.0] * 21,
        }
    )

    window = handicap_window(dataframe)
    projection = simulate_handicap(dataframe.iloc[1:], 12.0, 113, 72, 72, 36)
    distribution = strokes_distribution(dataframe, 20, show_curve=True)

    assert len(window) == 20
    assert window["Counting"].sum() == 8
    assert 5.0 not in window["SD"].tolist()
    assert projection.score_differential == 12.0
    assert projection.handicap == 12.9
    assert distribution is not None
    assert len(distribution.data) == 1  # zero variance means no Gaussian curve


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1",
    reason="set RUN_LIVE_TESTS=1 to call public FederGolf endpoints",
)
def test_public_course_service_contract() -> None:
    client = CourseCatalogClient()
    clubs = client.list_clubs()
    assert len(clubs) > 100

    club_name, club_id = next(iter(clubs.items()))
    courses = client.list_courses(club_id)
    assert club_name
    assert courses

    course_id = next(iter(courses.values()))
    tees = client.list_tees(course_id)
    assert tees

    result = client.calculate_handicap(
        club_id, course_id, next(iter(tees.values())), 18.0
    )[0]
    assert 20 <= result.slope_rating <= 200
    assert 20 <= result.course_rating <= 100
