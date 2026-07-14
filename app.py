import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

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
    df["magnitude"] = df["mw"].fillna(df["ml"])
    df["magnitude"] = df["magnitude"].fillna(0.0)
    
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Veri çekilirken bir hata oluştu: {e}")
    st.stop()

st.sidebar.header("Filtreleme Seçenekleri")

min_magnitude = st.sidebar.slider(
    "Minimum Büyüklük (Magnitude)", 
    min_value=0.0, 
    max_value=8.0, 
    value=2.0, 
    step=0.1
)

time_option = st.sidebar.selectbox(
    "Zaman Aralığı",
    ["Tüm Mevcut Veriler", "Bugün", "Son 3 Gün", "Son 7 Days"]
)
search_query = st.sidebar.text_input("Şehir  Ara (Örn: Mugla, Izmir)", "")

filtered_df = df[df["magnitude"] >= min_magnitude].copy()

if not filtered_df.empty and filtered_df["datetime"].notna().any():
    latest_time = filtered_df["datetime"].max()
    
    if time_option == "Bugün":
        start_date = latest_time.replace(hour=0, minute=0, second=0, microsecond=0)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]
    elif time_option == "Son 3 Gün":
        start_date = latest_time - timedelta(days=3)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]
    elif time_option == "Son 7 Days":
        start_date = latest_time - timedelta(days=7)
        filtered_df = filtered_df[filtered_df["datetime"] >= start_date]
if search_query:
    filtered_df = filtered_df[filtered_df["location"].str.contains(search_query, case=False, na=False)]

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Veriyi Dışa Aktar")

csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig') 

st.sidebar.download_button(
    label="Filtrelenmiş Veriyi CSV İndir",
    data=csv_data,
    file_name="filtrelenmis_deprem_verisi.csv",
    mime="text/csv",
    use_container_width=True
)
st.title("Türkiye Deprem Takip ve Analiz Paneli")
st.write("Kandilli Rasathanesi verileri kullanılarak anlık olarak güncellenen deprem analiz platformu.")

if filtered_df.empty:
    st.warning("Seçilen filtrelere uygun deprem verisi bulunamadı. Lütfen filtre ayarlarını gevşetin.")
    st.stop()

st.subheader("Son Dönemin En Büyük 5 Depremi")
top_5 = filtered_df.sort_values(by="magnitude", ascending=False).head(5)

cols = st.columns(5)
for idx, (_, row) in enumerate(top_5.iterrows()):
    loc_clean = row["location"].split("(")[0].strip()
    cols[idx].metric(
        label=loc_clean if len(loc_clean) < 25 else loc_clean[:22] + "...",
        value=f"M {row['magnitude']:.1f}",
        delta=f"Derinlik: {row['depth_km']} km",
        delta_color="inverse" 
    )

st.markdown("---")

st.subheader("Deprem Dağılım Haritası")

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
        popup=f"<b>Konum:</b> {row['location']}<br><b>Büyüklük:</b> M {mag}<br><b>Derinlik:</b> {row['depth_km']} km<br><b>Zaman:</b> {row['date']} {row['time']}"
    ).add_to(m)

st_folium(m, width="100%", height=500)

st.markdown("""
<div style="display:flex; align-items:center; gap:15px; margin:15px 0; font-family:sans-serif;">
    <b style="font-size:14px">Deprem Sınıfı Ölçeği:</b>
    <span style="color:#2ecc71; font-weight:bold;">● < 3.0 (Hafif)</span>
    <span style="color:#f1c40f; font-weight:bold;">● 3.0 - 4.4 (Hissedilir)</span>
    <span style="color:#e67e22; font-weight:bold;">● 4.5 - 5.4 (Orta/Şiddetli)</span>
    <span style="color:#e74c3c; font-weight:bold;">● ≥ 5.5 (Yıkıcı/Riskli)</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Deprem Büyüklük Dağılımı")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.histplot(
        filtered_df["magnitude"].dropna(), 
        bins=15, 
        kde=True, 
        color="tomato", 
        edgecolor="white", 
        ax=ax
    )
    ax.set_xlabel("Büyüklük (Magnitude)")
    ax.set_ylabel("Deprem Sayısı")
    st.pyplot(fig)

with col_chart2:
    st.subheader("Derinlik ve Büyüklük İlişkisi")
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
    ax3.set_xlabel("Derinlik (km)")
    ax3.set_ylabel("Büyüklük (Magnitude)")
    st.pyplot(fig3)

st.markdown("---")

st.subheader("En Çok Deprem Meydana Gelen 10 Bölge")
top_regions = filtered_df["location"].value_counts().head(10)

fig2, ax2 = plt.subplots(figsize=(12, 4))
sns.barplot(
    x=top_regions.values, 
    y=top_regions.index, 
    palette="mako", 
    ax=ax2
)
ax2.set_xlabel("Deprem Sayısı")
ax2.set_ylabel("Bölge")
st.pyplot(fig2)