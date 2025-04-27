import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# 1. Load data
df   = pd.read_csv("data/cities_final_ranked.csv")
top10 = df.sort_values("expansion_score", ascending=False).head(10)

# 2. Page config
st.set_page_config(page_title="GeoRetail AI Dashboard", layout="wide")

# 3. Title
st.title("GeoRetail AI: Retail Expansion Hotspots")

# 4. Create two columns
col_map, col_chart = st.columns((2, 1))  # 2:1 width ratio

# 5. Left column: Map
with col_map:
    st.header("Top 10 Expansion Cities Map")
    m = folium.Map(
        location=[top10.latitude.mean(), top10.longitude.mean()],
        zoom_start=2,
        tiles="cartodbpositron"
    )
    for _, row in top10.iterrows():
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=6 + row.expansion_score * 50,
            popup=f"{row.name} ({row.countrycode}) — Score: {row.expansion_score:.3f}",
            color="crimson",
            fill=True,
            fill_opacity=0.8
        ).add_to(m)
    st_folium(m, width=700, height=450)

# 6. Right column: Bar chart
with col_chart:
    st.header("Expansion Score Comparison")
    fig, ax = plt.subplots(figsize=(5,4))
    scores_pct = top10.set_index("name")["expansion_score"] * 100
    bars = ax.bar(scores_pct.index, scores_pct.values)
    ax.set_ylabel("Expansion Score (%)")
    ax.set_ylim(0, scores_pct.max() * 1.1)
    plt.xticks(rotation=45, ha="right")
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{bar.get_height():.2f}%",
            ha="center", va="bottom"
        )
    st.pyplot(fig)
