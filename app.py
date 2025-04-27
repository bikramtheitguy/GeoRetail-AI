import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import geonamescache

# ── 0. Page configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeoRetail AI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 1. Cached data loaders ─────────────────────────────────────────────────────
@st.cache_data
def load_city_data(path="data/cities_final_ranked.csv"):
    return pd.read_csv(path)

@st.cache_data
def load_country_meta():
    gc = geonamescache.GeonamesCache()
    countries = (
        pd.DataFrame(gc.get_countries())
          .T
          .reset_index()
          .rename(columns={"index": "iso2"})
    )
    return countries[["iso2", "continentcode"]]

@st.cache_data
def build_cont_map():
    gc    = geonamescache.GeonamesCache()
    conts = gc.get_continents()
    # Map codes → human-readable names
    return {code: info.get("name", "") for code, info in conts.items()}

# ── 2. Load & enrich ────────────────────────────────────────────────────────────
df = load_city_data()
country_meta = load_country_meta()
cont_map     = build_cont_map()

# Merge in continent codes
df = df.merge(
    country_meta,
    left_on="countrycode",
    right_on="iso2",
    how="left"
)

# Human-readable continent column
df["continent"] = df["continentcode"].map(cont_map)

# ── 3. Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filter Markets")

# 3a. Hard-coded continent order
continents_order = [
    "Asia", "Africa", "Europe", "North America",
    "South America", "Australia", "Antarctica"
]
available = [c for c in continents_order if c in df["continent"].unique()]
sel_regions = st.sidebar.multiselect(
    "Region (Continent)",
    options=available,
    default=available
)

# 3b. GDP per Capita slider
gdp_min, gdp_max = float(df.gdp_per_capita.min()), float(df.gdp_per_capita.max())
gdp_lo, gdp_hi = st.sidebar.slider(
    "GDP per Capita",
    min_value=gdp_min,
    max_value=gdp_max,
    value=(gdp_min, gdp_max),
    step=(gdp_max - gdp_min) / 100
)

# 3c. Existing store-count slider
store_max = int(df.store_count.max())
store_range = st.sidebar.slider(
    "Existing Store Count",
    min_value=0,
    max_value=store_max,
    value=(0, store_max),
    step=1
)
store_lo, store_hi = store_range

# ── 4. Apply filters & pick top 10 ──────────────────────────────────────────────
filtered = df.query(
    "continent in @sel_regions and "
    "@gdp_lo <= gdp_per_capita <= @gdp_hi and "
    "@store_lo <= store_count <= @store_hi"
)
top10 = filtered.nlargest(10, "expansion_score")

# ── 5. Main page layout ─────────────────────────────────────────────────────────
st.title("GeoRetail AI: Retail Expansion Hotspots")

col_map, col_chart = st.columns((2, 1))

# — Map Column —
with col_map:
    st.header("Top 10 Expansion Cities Map")
    if top10.empty:
        st.info("No cities match the selected filters.")
    else:
        m = folium.Map(
            location=[top10.latitude.mean(), top10.longitude.mean()],
            zoom_start=2,
            tiles="cartodbpositron"
        )
        for _, city in top10.iterrows():
            folium.CircleMarker(
                [city.latitude, city.longitude],
                radius=6 + city.expansion_score * 50,
                popup=(
                    f"{city.name} ({city.countrycode})\n"
                    f"Econ Viability: {city.econ_viability:.3f}\n"
                    f"Stores: {city.store_count}\n"
                    f"Score: {city.expansion_score:.3f}"
                ),
                color="crimson",
                fill=True,
                fill_opacity=0.7
            ).add_to(m)
        st_folium(m, width="100%", height=450)

# — Chart Column —
with col_chart:
    st.header("Expansion Score Comparison")
    if top10.empty:
        st.info("No data to display.")
    else:
        fig, ax = plt.subplots(figsize=(5, 4))
        scores = top10.set_index("name")["expansion_score"] * 100
        bars = ax.bar(scores.index, scores.values, width=0.6)
        ax.set_ylabel("Expansion Score (%)")
        ax.set_ylim(0, scores.max() * 1.1)
        plt.xticks(rotation=45, ha="right")
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{bar.get_height():.2f}%",
                ha="center", va="bottom", fontsize=9
            )
        st.pyplot(fig)
