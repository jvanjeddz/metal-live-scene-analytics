"""Review score distribution by subgenre."""

import plotly.express as px
import streamlit as st
import utils.charts  # noqa: F401

from utils.db import query

st.header("Review Scores by Subgenre")
st.markdown(
    "Which genres are most critically acclaimed? Which are polarizing? "
    "Box plots show the median, quartiles, and outliers for each subgenre."
)

# Get top genres by album count for default selection
top_genres = query("""
    SELECT primary_subgenre, count(*) as n
    FROM marts.agg_genre_review_distribution
    GROUP BY primary_subgenre
    ORDER BY n DESC
    LIMIT 20
""")

defaults = [
    "Death Metal", "Black Metal", "Thrash Metal", "Heavy Metal",
    "Power Metal", "Doom Metal", "Progressive Metal", "Melodic Death Metal",
]
available = top_genres["primary_subgenre"].tolist()
defaults = [g for g in defaults if g in available]

selected = st.multiselect("Select subgenres to compare", available, default=defaults)

if selected:
    placeholders = ", ".join(f"'{g}'" for g in selected)
    df = query(f"""
        SELECT * FROM marts.agg_genre_review_distribution
        WHERE primary_subgenre IN ({placeholders})
    """)

    # Sort genres by median score for better readability
    genre_order = (
        df.groupby("primary_subgenre")["avg_review_pct"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = px.box(
        df,
        x="primary_subgenre",
        y="avg_review_pct",
        color="primary_subgenre",
        category_orders={"primary_subgenre": genre_order},
        labels={
            "primary_subgenre": "Subgenre",
            "avg_review_pct": "Review Score (%)",
        },
        title="Review Score Distribution by Subgenre",
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, width='stretch')

    # Summary stats table
    st.subheader("Summary Statistics")
    stats = (
        df.groupby("primary_subgenre")["avg_review_pct"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(1)
        .sort_values("median", ascending=False)
        .rename(columns={
            "count": "Albums",
            "mean": "Mean",
            "median": "Median",
            "std": "Std Dev",
            "min": "Min",
            "max": "Max",
        })
    )
    st.dataframe(stats, width='stretch')
