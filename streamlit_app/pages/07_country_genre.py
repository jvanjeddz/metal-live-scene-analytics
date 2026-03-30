"""Country-genre affinity using location quotient."""

import plotly.express as px
import streamlit as st
import utils.charts  # noqa: F401

from utils.db import query

st.header("Country-Genre Affinity")
st.markdown(
    """
    Which countries specialize in which subgenres? The **location quotient (LQ)** measures
    over-representation: LQ > 1 means a genre is more common in that country than globally.
    LQ of 5 means 5x the global average concentration.
    """
)

countries = query(
    "SELECT DISTINCT country FROM marts.agg_country_genre_affinity ORDER BY country"
)
selected = st.selectbox("Select a country", countries["country"].tolist())

df = query(f"""
    SELECT * FROM marts.agg_country_genre_affinity
    WHERE country = '{selected}'
    ORDER BY location_quotient DESC
    LIMIT 15
""")

fig = px.bar(
    df,
    x="location_quotient",
    y="primary_subgenre",
    orientation="h",
    color="band_count",
    text="band_count",
    labels={
        "location_quotient": "Location Quotient",
        "primary_subgenre": "Subgenre",
        "band_count": "Bands",
    },
    title=f"Top Subgenre Specializations in {selected}",
)
fig.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, width='stretch')

# Cross-country comparison for a genre
st.subheader("Compare Countries for a Genre")
genres = query(
    "SELECT DISTINCT primary_subgenre FROM marts.agg_country_genre_affinity ORDER BY primary_subgenre"
)
genre_list = genres["primary_subgenre"].tolist()
default_idx = genre_list.index("Heavy Metal") if "Heavy Metal" in genre_list else 0
selected_genre = st.selectbox("Select a subgenre", genre_list, index=default_idx)

df2 = query(f"""
    SELECT * FROM marts.agg_country_genre_affinity
    WHERE primary_subgenre = '{selected_genre}'
    ORDER BY location_quotient DESC
""")
n_show = max(5, min(15, len(df2)))
df2 = df2.head(n_show)

fig2 = px.bar(
    df2,
    x="location_quotient",
    y="country",
    orientation="h",
    color="band_count",
    text="band_count",
    labels={
        "location_quotient": "Location Quotient",
        "country": "Country",
        "band_count": "Bands",
    },
    title=f"Top Countries for {selected_genre}",
)
fig2.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig2, width='stretch')

# Genre popularity by country
st.subheader("Genre Popularity by Country")
genres_map = query(
    "SELECT DISTINCT primary_subgenre FROM marts.agg_country_genre_affinity ORDER BY primary_subgenre"
)
genre_map_list = genres_map["primary_subgenre"].tolist()
default_map_idx = genre_map_list.index("Heavy Metal") if "Heavy Metal" in genre_map_list else 0
selected_genre_map = st.selectbox(
    "Select a subgenre", genre_map_list, index=default_map_idx, key="genre_map"
)

n_countries = st.slider("Number of countries to show", 10, 40, 20, key="n_countries")

df_map = query(f"""
    SELECT country, band_count
    FROM marts.agg_country_genre_affinity
    WHERE primary_subgenre = '{selected_genre_map}'
    ORDER BY band_count DESC
    LIMIT {n_countries}
""")

fig3 = px.bar(
    df_map,
    x="band_count",
    y="country",
    orientation="h",
    text="band_count",
    labels={"band_count": "Bands", "country": "Country"},
    title=f"{selected_genre_map} Bands by Country",
)
fig3.update_layout(yaxis=dict(autorange="reversed"), height=max(400, n_countries * 25))
st.plotly_chart(fig3, width='stretch')
