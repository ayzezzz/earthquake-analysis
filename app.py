import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

st.set_page_config(page_title="Türkiye Earthquake Tracker", layout="wide")

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
    df["magnitude"] = df["mw"].fillna(df["ml"])
    df["magnitude"] = df["magnitude"].fillna(0.0)
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

st.sidebar.header("Filter Options")

min_magnitude = st.sidebar.slider(
    "Minimum Magnitude",
    min_value=0.0,
    max_value=8.0,
    value=2.0,
    step=0.1
)

time_option = st.sidebar.selectbox(
    "Time Range",
    ["All Available Data", "Today", "Last 3 Days", "Last 7 Days"]
)

search_query = st.sidebar.text_input("Search Location (e.g. Mugla, Izmir)", "")

filtered_df = df[df["magnitude"] >= min_magnitude].copy()

if not filtered_df.empty and filtered_df["datetime"].notna().any():
    latest_time = filtered_df["datetime"].max()

    if time_option == "Today":
        start_date = latest_time.replace(hour=0, minute=0, second=0, microsecond=0)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]
    elif time_option == "Last 3 Days":
        start_date = latest_time - timedelta(days=3)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]
    elif time_option == "Last 7 Days":
        start_date = latest_time - timedelta(days=7)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]

if search_query:
    filtered_df = filtered_df[filtered_df["location"].str.contains(search_query, case=False, na=False)]

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Data")

csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")

st.sidebar.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="earthquake_data.csv",
    mime="text/csv",
    use_container_width=True
)

st.title("Türkiye Earthquake Tracker")
last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"🕐 Last updated: {last_updated}")
st.write("Real-time earthquake analysis dashboard powered by live data from Kandilli Observatory.")

if filtered_df.empty:
    st.warning("No earthquakes found for the selected filters. Try adjusting the filters.")
    st.stop()

st.subheader("Top 5 Largest Earthquakes")
top_5 = filtered_df.sort_values(by="magnitude", ascending=False).head(5)

cols = st.columns(5)
for idx, (_, row) in enumerate(top_5.iterrows()):
    loc_clean = row["location"].split("(")[0].strip()
    cols[idx].metric(
        label=loc_clean if len(loc_clean) < 25 else loc_clean[:22] + "...",
        value=f"M {row['magnitude']:.1f}",
        delta=f"Depth: {row['depth_km']} km",
        delta_color="inverse"
    )

st.markdown("---")
st.subheader("Earthquake Map")

m = folium.Map(location=[39.0, 35.0], zoom_start=6)

for _, row in filtered_df.iterrows():
    mag = row["magnitude"]

    if mag < 3.0:
        color = "#2ecc71"
    elif mag < 4.5:
        color = "#f1c40f"
    elif mag < 5.5:
        color = "#e67e22"
    else:
        color = "#e74c3c"

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=mag * 3,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=f"<b>Location:</b> {row['location']}<br><b>Magnitude:</b> M {mag}<br><b>Depth:</b> {row['depth_km']} km<br><b>Time:</b> {row['date']} {row['time']}"
    ).add_to(m)

st_folium(m, width="100%", height=500)

st.markdown("""
<div style="display:flex; align-items:center; gap:15px; margin:15px 0; font-family:sans-serif;">
    <b style="font-size:14px">Magnitude Scale:</b>
    <span style="color:#2ecc71; font-weight:bold;">● &lt; 3.0 (Minor)</span>
    <span style="color:#f1c40f; font-weight:bold;">● 3.0 - 4.4 (Light)</span>
    <span style="color:#e67e22; font-weight:bold;">● 4.5 - 5.4 (Moderate)</span>
    <span style="color:#e74c3c; font-weight:bold;">● ≥ 5.5 (Strong / Dangerous)</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Magnitude Distribution")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.histplot(
        filtered_df["magnitude"].dropna(),
        bins=15,
        kde=True,
        color="tomato",
        edgecolor="white",
        ax=ax
    )
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Number of Earthquakes")
    st.pyplot(fig)

with col_chart2:
    st.subheader("Depth vs Magnitude")
    fig3, ax3 = plt.subplots(figsize=(10, 4.5))
    sns.scatterplot(
        x="depth_km",
        y="magnitude",
        data=filtered_df,
        alpha=0.6,
        color="#8e44ad",
        s=80,
        ax=ax3
    )
    sns.regplot(
        x="depth_km",
        y="magnitude",
        data=filtered_df,
        scatter=False,
        color="red",
        ax=ax3
    )
    ax3.set_xlabel("Depth (km)")
    ax3.set_ylabel("Magnitude")
    st.pyplot(fig3)

st.markdown("---")

st.subheader("Top 10 Most Active Regions")
top_regions = filtered_df["location"].value_counts().head(10)

fig2, ax2 = plt.subplots(figsize=(12, 4))
sns.barplot(
    x=top_regions.values,
    y=top_regions.index,
    palette="mako",
    ax=ax2
)
ax2.set_xlabel("Number of Earthquakes")
ax2.set_ylabel("Region")
st.pyplot(fig2)

st.markdown("---")

st.subheader("Hourly Earthquake Distribution")
filtered_df["hour"] = filtered_df["datetime"].dt.hour
hourly = filtered_df.groupby("hour").size().reset_index(name="count")
fig4, ax4 = plt.subplots(figsize=(12, 4))
sns.barplot(x="hour", y="count", data=hourly, palette="coolwarm", ax=ax4)
ax4.set_xlabel("Hour of Day")
ax4.set_ylabel("Number of Earthquakes")
ax4.set_xticks(range(24))
st.pyplot(fig4)