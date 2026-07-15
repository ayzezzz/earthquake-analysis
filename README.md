# 🌍 Türkiye Earthquake Tracker

A real-time earthquake analysis dashboard built with Python and Streamlit, 
pulling live data from Kandilli Observatory (Boğaziçi University).

## Features
- Live data updated every 5 minutes (last 500 earthquakes)
- Interactive map with magnitude-based color coding
- Filter by magnitude, time range, and location
- Top 5 largest earthquakes display
- Magnitude distribution and depth vs magnitude analysis
- Top 10 most active regions
- Hourly earthquake distribution
- Export filtered data as CSV

## Tech Stack
Python, Pandas, Streamlit, Folium, Matplotlib, Seaborn, BeautifulSoup

## Live Demo
https://zez-earthquake-analysis.streamlit.app/

## How to Run
```bash
git clone https://github.com/ayzezzz/turkey-earthquake-tracker.git
cd turkey-earthquake-tracker
pip install -r requirements.txt
streamlit run app.py
```

## Data Source
[Kandilli Observatory — Boğaziçi University](http://www.koeri.boun.edu.tr/scripts/lst0.asp)
