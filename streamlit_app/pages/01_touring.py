"""Touring intensity and rating vs touring correlation."""

import plotly.express as px
import streamlit as st
import utils.charts  # noqa: F401

from utils.db import query

st.header("Touring Analysis")

# Tile 1: Genre Touring Intensity
st.subheader("Touring Intensity by Subgenre")
df_genre = query("""
    SELECT * FROM marts.agg_genre_touring_intensity
    WHERE band_count >= 2
    ORDER BY avg_concerts_per_band DESC
    LIMIT 20
""")
fig1 = px.bar(
    df_genre,
    x="avg_concerts_per_band",
    y="primary_subgenre",
    orientation="h",
    color="total_concerts",
    labels={
        "avg_concerts_per_band": "Avg Concerts per Band",
        "primary_subgenre": "Subgenre",
        "total_concerts": "Total Concerts",
    },
    title="Top 20 Subgenres by Average Concerts per Band",
)
fig1.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig1, width='stretch')

# Tile 3: Rating vs Touring
st.subheader("Review Scores vs Touring Activity")
df_rating = query("SELECT * FROM marts.agg_rating_vs_touring")
fig3 = px.bar(
    df_rating,
    x="touring_bucket",
    y=["avg_review_score", "median_review_score"],
    barmode="group",
    labels={
        "touring_bucket": "Concert Count Bucket",
        "value": "Review Score (%)",
        "variable": "Metric",
    },
    title="Do Bands That Tour More Get Better Reviews?",
)
st.plotly_chart(fig3, width='stretch')

with st.expander("Data"):
    st.dataframe(df_rating)
