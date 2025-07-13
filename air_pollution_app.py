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

# --- FUNCTIONS ---
@st.cache_data(ttl=600)
def get_aqi_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def get_forecast_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
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
st.caption("Real-time AQI with insights, health tips, and weather.")

use_gps = st.button("📡 Use My Location")

if use_gps:
    lat, lon, city = get_browser_location()
else:
    city_input = st.text_input("Enter city name (optional)")
    if city_input:
        try:
            res = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "json", "q": city_input},
                headers={"User-Agent": "air-pollution-app-seira"},
                timeout=5
            )
            res.raise_for_status()
            geocode = res.json()
        except requests.exceptions.RequestException as e:
            st.error(f"🌐 Geolocation request failed: {e}")
            geocode = []
        except ValueError:
            st.error("⚠️ Invalid response from location service.")
            geocode = []

        if geocode:
            lat = float(geocode[0]['lat'])
            lon = float(geocode[0]['lon'])
            city = city_input
        else:
            st.error("City not found. Using default location.")
            lat, lon, city = 9.31575, 76.61513, "Chengannur"
    else:
        lat, lon, city = 9.31575, 76.61513, "Chengannur"

with st.spinner("Loading AQI and Weather Data..."):
    data = get_aqi_data(lat, lon)
    weather = get_weather_data(lat, lon)
    forecast = get_forecast_data(lat, lon)

if data["status"] == "ok":
    aqi = data["data"]["aqi"]
    station = data["data"]["city"]["name"]
    updated = data["data"]["time"]["s"]
    category, color = get_aqi_category(aqi)
    tip = get_health_tip(aqi)
    pollutant_data = data["data"].get("iaqi", {})

    with st.container():
        st.markdown(f"""
        <div style='background-color:{color}; padding:20px; border-radius:10px'>
            <h2 style='color:black;'>📍 {city}</h2>
            <h1 style='color:black;'>🌫️ AQI: {aqi} - {category}</h1>
            <p style='color:black;'>Nearest station: {station} <br> Updated: {updated}</p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📈 View Details"):
        st.info(tip)

        if weather.get("main"):
            st.subheader("🌦️ Local Weather Conditions")
            temp = weather["main"]["temp"]
            desc = weather["weather"][0]["description"].capitalize()
            humidity = weather["main"]["humidity"]
            wind = weather["wind"]["speed"]

            st.write(f"**Temperature:** {temp} °C")
            st.write(f"**Weather:** {desc}")
            st.write(f"**Humidity:** {humidity}%")
            st.write(f"**Wind Speed:** {wind} m/s")

        if forecast.get("list"):
            st.subheader("🔮 3-Day Weather Forecast")
            forecast_list = forecast["list"][:24*3:8]  # Every 8th entry ≈ 24 hours
            for item in forecast_list:
                date = item["dt_txt"].split(" ")[0]
                temp = item["main"]["temp"]
                desc = item["weather"][0]["description"].capitalize()
                st.write(f"📅 {date}: {desc}, 🌡️ {temp} °C")

        with st.expander("🧪 View Pollutant Levels"):
            for key, val in pollutant_data.items():
                st.write(f"**{key.upper()}**: {val['v']}")

        st.subheader("📍 Nearest AQI Station")
        show_map(lat, lon, station)

    st.success(f"🌱 Tip of the Day: {get_random_tip()}")
else:
    st.error("❌ Could not load AQI data. Try again later.")
