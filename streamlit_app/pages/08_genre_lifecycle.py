"""Genre lifecycle curves — rise and fall of subgenres over time."""

import plotly.express as px
import streamlit as st
import utils.charts  # noqa: F401

from utils.db import query

st.header("Genre Lifecycle Curves")
st.markdown(
    "How many new bands started releasing music in each subgenre per year? "
    "Uses each band's first album year as a proxy for when they entered the scene."
)

# Get top genres by total bands
top_genres = query("""
    SELECT primary_subgenre, sum(new_bands) as total
    FROM marts.agg_genre_lifecycle
    GROUP BY primary_subgenre
    ORDER BY total DESC
    LIMIT 20
""")

default_genres = ["Death Metal", "Black Metal", "Thrash Metal", "Heavy Metal", "Power Metal", "Doom Metal"]
available = top_genres["primary_subgenre"].tolist()
defaults = [g for g in default_genres if g in available]

selected = st.multiselect(
    "Select subgenres to compare",
    available,
    default=defaults,
)

if selected:
    placeholders = ", ".join(f"'{g}'" for g in selected)
    df = query(f"""
        SELECT * FROM marts.agg_genre_lifecycle
        WHERE primary_subgenre IN ({placeholders})
        ORDER BY debut_year
    """)

    fig = px.line(
        df,
        x="debut_year",
        y="new_bands",
        color="primary_subgenre",
        labels={
            "debut_year": "Year",
            "new_bands": "New Bands",
            "primary_subgenre": "Subgenre",
        },
        title="New Bands per Year by Subgenre",
        markers=True,
    )
    st.plotly_chart(fig, width='stretch')

    # Cumulative view
    df_sorted = df.sort_values(["primary_subgenre", "debut_year"])
    df_sorted["cumulative_bands"] = df_sorted.groupby("primary_subgenre")["new_bands"].cumsum()

    fig2 = px.area(
        df_sorted,
        x="debut_year",
        y="cumulative_bands",
        color="primary_subgenre",
        labels={
            "debut_year": "Year",
            "cumulative_bands": "Cumulative Bands",
            "primary_subgenre": "Subgenre",
        },
        title="Cumulative Band Count Over Time",
    )
    st.plotly_chart(fig2, width='stretch')
