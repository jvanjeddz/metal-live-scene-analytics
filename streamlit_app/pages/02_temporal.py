"""Temporal trends in metal live activity."""

import plotly.express as px
import streamlit as st
import utils.charts  # noqa: F401

from utils.db import query

st.header("Temporal Trends")

# Tile 2: Metal Live Activity Over Time
st.subheader("Metal Concert Activity Over Time")
df_time = query("""
    SELECT
        event_year,
        sum(concert_count) as concert_count
    FROM marts.agg_concerts_over_time
    WHERE event_year >= 1980 AND event_year <= 2025
    GROUP BY event_year
    ORDER BY event_year
""")
fig2 = px.line(
    df_time,
    x="event_year",
    y="concert_count",
    labels={"event_year": "Year", "concert_count": "Concerts"},
    title="Metal Concerts per Year",
    markers=True,
)
st.plotly_chart(fig2, width='stretch')

# Tile 4: Subgenre Popularity Shifts
st.subheader("Subgenre Share Over Time")
df_sub = query("""
    WITH top_genres AS (
        SELECT primary_subgenre
        FROM marts.agg_genre_touring_intensity
        ORDER BY total_concerts DESC
        LIMIT 10
    ),
    tagged AS (
        SELECT
            event_year,
            CASE WHEN primary_subgenre IN (SELECT primary_subgenre FROM top_genres)
                 THEN primary_subgenre
                 ELSE 'Other'
            END AS primary_subgenre,
            concert_share_pct
        FROM marts.agg_subgenre_share_over_time
        WHERE event_year >= 1990 AND event_year <= 2025
    )
    SELECT
        event_year,
        primary_subgenre,
        sum(concert_share_pct) AS concert_share_pct
    FROM tagged
    GROUP BY event_year, primary_subgenre
""")
fig4 = px.bar(
    df_sub,
    x="event_year",
    y="concert_share_pct",
    color="primary_subgenre",
    labels={
        "event_year": "Year",
        "concert_share_pct": "Share (%)",
        "primary_subgenre": "Subgenre",
    },
    title="Subgenre Concert Share Over Time",
)
st.plotly_chart(fig4, width='stretch')
