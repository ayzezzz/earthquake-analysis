import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Turkey Earthquake Tracker", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    url = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"
    response = requests.get(url, timeout=10)
    response.encoding = "windows-1254"
    soup = BeautifulSoup(response.text, "html.parser")
    pre = soup.find("pre")
    lines = pre.text.strip().split("\n")
    data_lines = [line for line in lines if line.strip() and line[0:4].isdigit()]
    rows = []
    for line in data_lines:
        parts = line.split()
        if len(parts) >= 9:
            rows.append({
                "date": parts[0],
                "time": parts[1],
                "latitude": float(parts[2]),
                "longitude": float(parts[3]),
                "depth_km": float(parts[4]),
                "md": parts[5],
                "ml": parts[6],
                "mw": parts[7],
                "location": " ".join(parts[8:])
            })
    df = pd.DataFrame(rows)
    df["ml"] = pd.to_numeric(df["ml"], errors="coerce")
    df["mw"] = pd.to_numeric(df["mw"], errors="coerce")
    df["magnitude"] = df["ml"].fillna(df["mw"])
    return df

df = load_data()

st.title("🌍 Turkey Earthquake Tracker")
st.write("Live data from Kandilli Observatory — last 500 earthquakes")

col1, col2, col3 = st.columns(3)
col1.metric("Total Earthquakes", len(df))
col2.metric("Average Magnitude", f"{df['magnitude'].mean():.2f}")
col3.metric("Max Magnitude", f"{df['magnitude'].max():.2f}")

st.markdown("---")

min_mag = st.slider("Minimum Magnitude", 0.0, 7.0, 2.0, 0.1)
filtered = df[df["magnitude"] >= min_mag]
st.write(f"{len(filtered)} earthquakes found with magnitude ≥ {min_mag}")

m = folium.Map(location=[39.0, 35.0], zoom_start=6)
for _, row in filtered.iterrows():
    if pd.notna(row["magnitude"]):
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=row["magnitude"] * 2,
            color="red",
            fill=True,
            fill_opacity=0.5,
            popup=f"{row['location']} | M{row['magnitude']} | {row['date']}"
        ).add_to(m)

st_folium(m, width=1200, height=500)

st.subheader("Recent Earthquakes")
st.dataframe(filtered[["date", "time", "magnitude", "depth_km", "location"]].head(20))