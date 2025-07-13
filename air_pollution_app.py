import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium
import random
import os
import streamlit.components.v1 as components
import json

# --- CONFIG ---
st.set_page_config(page_title="Clean Air Monitor", layout="wide")

st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- API TOKEN & FILE ---
WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
OPENWEATHER_API_KEY = "your_openweather_api_key"
aqi_log_file = "aqi_log.csv"

# --- FUNCTIONS ---
@st.cache_data(ttl=600)
def get_aqi_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    return requests.get(url).json()

def get_browser_location():
    location_param = st.query_params.get("location")
    if not location_param:
        components.html(
            """
            <script>
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const coords = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    const message = JSON.stringify(coords);
                    window.parent.postMessage(message, '*');
                }
            );
            </script>
            """,
            height=0
        )
        st.info("🔄 Attempting to fetch GPS location... please allow it in your browser.")
        st.stop()

    try:
        coords = json.loads(location_param[0])
        return coords['latitude'], coords['longitude'], "Live GPS"
    except:
        return None, None, None

def get_aqi_category(aqi):
    if aqi <= 50:
        return "🟢 Good", "#A8E6CF"
    elif aqi <= 100:
        return "🟡 Moderate", "#FFD3B6"
    elif aqi <= 150:
        return "🟠 Unhealthy for Sensitive Groups", "#FFAAA5"
    elif aqi <= 200:
        return "🔴 Unhealthy", "#FF8C94"
    elif aqi <= 300:
        return "🟣 Very Unhealthy", "#D291BC"
    else:
        return "⚫ Hazardous", "#B5838D"

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
    st_folium(m, width=700, height=300)

# --- MAIN APP ---

st.title("🌍 Clean Air Monitor")
st.caption("Real-time AQI with insights, history, health tips, and weather.")
