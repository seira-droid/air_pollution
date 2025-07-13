import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium
import random
import os

# --- CONFIG ---
st.set_page_config(page_title="Air Pollution Dashboard", layout="wide")

st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- API TOKEN & FILE ---
WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
aqi_log_file = "aqi_log.csv"

# --- FUNCTIONS ---

def get_user_location():
    try:
        data = requests.get("https://ipinfo.io").json()
        lat, lon = map(float, data["loc"].split(","))
        city = data.get("city", "Unknown")
        return lat, lon, city
    except:
        return 9.31575, 76.61513, "Chengannur"

def get_aqi_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    return requests.get(url).json()

def get_aqi_category(aqi):
    if aqi <= 50:
        return "🟢 Good", "#00e400"
    elif aqi <= 100:
        return "🟡 Moderate", "#ffd700"  # gold (soft yellow)
    elif aqi <= 150:
        return "🟠 Unhealthy for Sensitive Groups", "#ff7e00"
    elif aqi <= 200:
        return "🔴 Unhealthy", "#ff0000"
    elif aqi <= 300:
        return "🟣 Very Unhealthy", "#8f3f97"
    else:
        return "⚫ Hazardous", "#7e0023"

def get_health_tip(aqi):
    if aqi <= 50:
        return "✅ Air is clean. Great day to be outdoors!"
    elif aqi <= 100:
        return "☁️ Sensitive groups should reduce prolonged outdoor exertion."
    elif aqi <= 150:
        return "😷 Avoid heavy outdoor exercise. Consider wearing a mask."
    elif aqi <= 200:
        return "⚠️ Everyone should limit prolonged outdoor exertion."
    elif aqi <= 300:
        return "❌ Stay indoors and use air purifiers."
    else:
        return "🚨 Health emergency! Avoid all outdoor activities."

def log_aqi(city, aqi):
    today = datetime.date.today().isoformat()
    if not os.path.exists(aqi_log_file):
        pd.DataFrame(columns=["date", "city", "aqi"]).to_csv(aqi_log_file, index=False)
    df = pd.read_csv(aqi_log_file)
    if not ((df['date'] == today) & (df['city'] == city)).any():
        new_row = pd.DataFrame([{"date": today, "city": city, "aqi": aqi}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(aqi_log_file, index=False)

def get_random_tip():
    tips = [
        "💡 Use indoor plants like spider plant to improve air quality.",
        "🌀 Use HEPA filters to clean indoor air.",
        "🏃‍♀️ Exercise indoors on high AQI days.",
        "📱 Check AQI before outdoor plans!",
        "🪟 Close windows during high pollution times."
    ]
    return random.choice(tips)

def show_map(lat, lon, station_name):
    m = folium.Map(location=[lat, lon], zoom_start=10)
    folium.Marker([lat, lon], tooltip=station_name, icon=folium.Icon(color="blue")).add_to(m)
    st_folium(m, width=700, height=300)  # reduced height

# --- MAIN APP ---

st.title("🌍 Air Pollution Dashboard")
st.caption("Real-time AQI with insights, history, health tips, and more.")

with st.spinner("📡 Fetching location and AQI data..."):
    lat, lon, city = get_user_location()
    data = get_aqi_data(lat, lon)

if data["status"] == "ok":
    aqi = data["data"]["aqi"]
    station = data["data"]["city"]["name"]
    updated = data["data"]["time"]["s"]
    category, color = get_aqi_category(aqi)
    tip = get_health_tip(aqi)
    pollutant_data = data["data"].get("iaqi", {})

    log_aqi(city, aqi)

    st.markdown(f"""
    <div style='background-color:{color}; padding:20px; border-radius:10px'>
        <h2 style='color:white;'>📍 {city}</h2>
        <h1 style='color:white;'>🌫️ AQI: {aqi} - {category}</h1>
        <p style='color:white;'>Nearest station: {station} <br> Updated: {updated}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(tip)

    with st.expander("🧪 View Pollutant Levels"):
        for key, val in pollutant_data.items():
            st.write(f"**{key.upper()}**: {val['v']}")

    st.subheader("📍 Nearest AQI Station")
    show_map(lat, lon, station)

    st.success(f"🌱 Tip of the Day: {get_random_tip()}")

    # Historical Chart
    if os.path.exists(aqi_log_file):
        df = pd.read_csv(aqi_log_file)
        df_city = df[df["city"] == city]
        if not df_city.empty:
            st.subheader("📈 AQI Trend (Saved Daily)")
            fig = px.line(df_city, x="date", y="aqi", title="AQI Over Time", markers=True)
            st.plotly_chart(fig)
            st.download_button("⬇️ Download AQI History", data=df_city.to_csv(index=False),
                               file_name=f"{city}_aqi_history.csv")

else:
    st.error("❌ Could not load AQI data. Try again later.")

# --- CITY COMPARISON ---
st.markdown("---")
st.subheader("🏙️ Compare Two Cities")

city_coords = {
    "Chengannur": (9.31575, 76.61513),
    "Kochi": (9.9312, 76.2673),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946)
}

col1, col2 = st.columns(2)
with col1:
    city1 = st.selectbox("City 1", city_coords.keys())
with col2:
    city2 = st.selectbox("City 2", city_coords.keys(), index=1)

lat1, lon1 = city_coords[city1]
lat2, lon2 = city_coords[city2]

aqi1 = get_aqi_data(lat1, lon1)["data"]["aqi"]
aqi2 = get_aqi_data(lat2, lon2)["data"]["aqi"]
st.metric(label=f"{city1}", value=aqi1)
st.metric(label=f"{city2}", value=aqi2)
