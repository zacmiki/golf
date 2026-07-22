from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


@dataclass(frozen=True)
class PerformanceSummary:
    current_handicap: float | None
    low_index_365: float | None
    recent_sd_average: float | None
    previous_sd_average: float | None
    best_eight_average: float | None
    sd_consistency: float | None
    valid_rounds: int

    @property
    def form_change(self) -> float | None:
        if self.recent_sd_average is None or self.previous_sd_average is None:
            return None
        return self.recent_sd_average - self.previous_sd_average


def summarize_performance(df: pd.DataFrame) -> PerformanceSummary:
    rounds = _dated_rounds(df)
    differentials = rounds.dropna(subset=["SD"])
    recent_twenty = differentials.head(20)
    recent_five = differentials.head(5)["SD"]
    previous_five = differentials.iloc[5:10]["SD"]

    current_values = rounds["Index Nuovo"].dropna()
    current_handicap = (
        float(current_values.iloc[0]) if not current_values.empty else None
    )

    low_index_365: float | None = None
    if not rounds.empty:
        latest_date = pd.Timestamp(rounds["_date"].max())
        last_year = rounds[
            rounds["_date"] >= latest_date - pd.DateOffset(days=365)
        ]
        year_indices = last_year["Index Nuovo"].dropna()
        if not year_indices.empty:
            low_index_365 = float(year_indices.min())

    best_eight = recent_twenty.nsmallest(min(8, len(recent_twenty)), "SD")["SD"]
    return PerformanceSummary(
        current_handicap=current_handicap,
        low_index_365=low_index_365,
        recent_sd_average=_mean_or_none(recent_five),
        previous_sd_average=_mean_or_none(previous_five),
        best_eight_average=_mean_or_none(best_eight),
        sd_consistency=(
            float(recent_twenty["SD"].std(ddof=0))
            if len(recent_twenty) >= 2
            else None
        ),
        valid_rounds=len(differentials),
    )


def counting_rounds(df: pd.DataFrame) -> pd.DataFrame:
    rounds = _dated_rounds(df).dropna(subset=["SD"]).head(20).copy()
    rounds["Counting"] = False
    if not rounds.empty:
        best_indices = rounds.nsmallest(min(8, len(rounds)), "SD").index
        rounds.loc[best_indices, "Counting"] = True
    return rounds


def potential_exceptional_rounds(df: pd.DataFrame) -> pd.DataFrame:
    """Return rounds whose SD is at least 7 below the pre-round Handicap Index."""
    rounds = _dated_rounds(df)
    if "Index Vecchio" not in rounds:
        return rounds.iloc[0:0].copy()
    candidates = rounds.dropna(subset=["SD", "Index Vecchio"]).copy()
    candidates["Gap"] = candidates["Index Vecchio"] - candidates["SD"]
    return candidates[candidates["Gap"] >= 7.0].copy()


def performance_insights() -> None:
    df = st.session_state.df.copy()
    summary = summarize_performance(df)
    rounds = counting_rounds(df)

    st.title("Performance Insights ⛳️")
    st.caption(
        "See at a glance how you are playing and which rounds are helping your Handicap."
    )

    current_col, low_col, form_col = st.columns(3)
    current_col.metric(
        "Current Handicap",
        _format_metric(summary.current_handicap),
    )
    low_col.metric(
        "Best HCP · last 12 months",
        _format_metric(summary.low_index_365),
    )
    form_col.metric(
        "Recent form · last 5",
        _format_metric(summary.recent_sd_average),
        delta=_form_delta(summary.form_change),
        delta_color="inverse",
    )
    _show_form_message(summary)
    with st.expander("What is Score Differential (SD)?"):
        st.write(
            "SD compares a round with the difficulty of the course. Lower is better. "
            "Your Handicap is mainly based on the best 8 SD values from your latest "
            "20 valid rounds."
        )
    _show_differential_chart(rounds)
    _show_counting_rounds(rounds, summary.best_eight_average)

    with st.expander("Advanced details"):
        st.metric(
            "Consistency · last 20",
            _format_metric(summary.sd_consistency),
            help="Lower means your recent Score Differentials are more consistent.",
        )
        left, right = st.columns(2)
        with left:
            _show_round_signals(df)
        with right:
            _show_formula_performance(df)


def _dated_rounds(df: pd.DataFrame) -> pd.DataFrame:
    rounds = df.copy()
    rounds["_date"] = pd.to_datetime(rounds["Data"], errors="coerce")
    rounds = rounds[rounds["_date"].notna()].copy()
    return rounds.sort_values("_date", ascending=False, kind="stable").reset_index(
        drop=True
    )


def _mean_or_none(values: pd.Series) -> float | None:
    return float(values.mean()) if not values.empty else None


def _format_metric(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}"


def _form_delta(change: float | None) -> str | None:
    if change is None:
        return None
    return f"{change:+.1f} vs prior 5"


def _show_form_message(summary: PerformanceSummary) -> None:
    change = summary.form_change
    if change is None:
        st.info("Play at least 10 valid rounds to unlock a recent-form comparison.")
    elif change <= -0.5:
        st.success(
            f"Recent form is improving: your last-five average SD is "
            f"{abs(change):.1f} lower than the previous five."
        )
    elif change >= 0.5:
        st.warning(
            f"Recent form has cooled: your last-five average SD is "
            f"{change:.1f} higher than the previous five."
        )
    else:
        st.info("Recent form is steady compared with the previous five rounds.")


def _show_differential_chart(rounds: pd.DataFrame) -> None:
    if rounds.empty:
        st.warning("No Score Differentials are available for charting.")
        return
    chronological = rounds.sort_values("_date", kind="stable")
    counting = chronological[chronological["Counting"]]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=chronological["_date"],
            y=chronological["SD"],
            mode="lines+markers",
            name="Score Differential",
            line={"color": "#6c8ebf", "width": 2},
            marker={"size": 8},
            customdata=chronological[["Gara"]].to_numpy(),
            hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<br>SD %{y:.1f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=counting["_date"],
            y=counting["SD"],
            mode="markers",
            name="Counting 8",
            marker={"size": 13, "color": "#2ca02c", "symbol": "star"},
            hovertemplate="Counting round<br>%{x|%d %b %Y}<br>SD %{y:.1f}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Score Differential · most recent 20",
        xaxis_title="Date",
        yaxis_title="Score Differential (lower is better)",
        hovermode="x unified",
        height=430,
        margin={"l": 20, "r": 20, "t": 60, "b": 30},
    )
    st.plotly_chart(figure, width="stretch")


def _show_counting_rounds(
    rounds: pd.DataFrame, best_eight_average: float | None
) -> None:
    st.subheader("Your counting rounds")
    if best_eight_average is not None:
        st.caption(
            f"These are the green rounds helping your Handicap now. Their average "
            f"SD is {best_eight_average:.1f}."
        )
    selected = rounds[rounds["Counting"]].copy()
    if selected.empty:
        st.info("No counting rounds are available.")
        return
    selected["Date"] = selected["_date"].dt.strftime("%Y-%m-%d")
    columns = [column for column in ["Date", "Gara", "Formula", "SD"] if column in selected]
    st.dataframe(
        selected[columns].sort_values("SD"),
        hide_index=True,
        width="stretch",
        column_config={"SD": st.column_config.NumberColumn(format="%.1f")},
    )


def _show_round_signals(df: pd.DataFrame) -> None:
    st.subheader("Special round signals")
    exceptional = potential_exceptional_rounds(df)
    pcc_rounds = 0
    if "PCC" in df:
        pcc = pd.to_numeric(df["PCC"], errors="coerce").fillna(0)
        pcc_rounds = int(pcc.ne(0).sum())

    st.metric("Potential exceptional rounds", len(exceptional))
    st.caption(
        "SD at least 7.0 below the pre-round Index. This is an indicator only; "
        "FederGolf applies the official WHS adjustment."
    )
    st.metric("Rounds with non-zero PCC", pcc_rounds)
    st.caption("PCC reflects unusual playing conditions already included in the SD.")


def _show_formula_performance(df: pd.DataFrame) -> None:
    if "Formula" not in df:
        return
    rounds = df.dropna(subset=["SD", "Formula"]).copy()
    if rounds.empty:
        return
    aggregation: dict[str, tuple[str, str]] = {
        "Rounds": ("SD", "count"),
        "Average SD": ("SD", "mean"),
        "Best SD": ("SD", "min"),
    }
    if "AGS" in rounds:
        aggregation["Average Gross"] = ("AGS", "mean")
    by_formula = (
        rounds.groupby("Formula", dropna=False)
        .agg(**aggregation)
        .query("Rounds >= 2")
        .sort_values("Average SD")
        .reset_index()
    )
    if by_formula.empty:
        return
    st.subheader("By competition format")
    st.caption("Formats with at least two valid rounds, ranked by average SD.")
    st.dataframe(
        by_formula,
        hide_index=True,
        width="stretch",
        column_config={
            column: st.column_config.NumberColumn(format="%.1f")
            for column in by_formula
            if column != "Formula"
        },
    )
