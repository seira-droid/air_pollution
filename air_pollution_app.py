import streamlit as st
import requests
import datetime
import folium
from streamlit_folium import st_folium
import random
import os
import streamlit.components.v1 as components
import json

# --- CONFIG ---
st.set_page_config(page_title="Clean Air Monitor", layout="wide")

# --- AUTO DETECT SYSTEM THEME ---
def get_system_theme():
    return st.get_option("theme.base") or "light"

system_theme = get_system_theme()

if system_theme == "dark":
    background_color = "#1e1e1e"
    text_color = "#f1f1f1"
    card_color = "#2a2a2a"
    nav_color = "#2e2e2e"
else:
    background_color = "#f4f6f9"
    text_color = "#2e2e2e"
    card_color = "white"
    nav_color = "#ffffff"

st.markdown(f"""<style>
html, body {{ background-color: {background_color}; color: {text_color}; font-family: 'Segoe UI'; }}
.main > div:first-child {{ padding-top: 4rem; }}
h1, h2, h3 {{ color: {text_color}; }}
.stButton>button {{ background-color: #1f77d0; color: white; border-radius: 10px; padding: 0.6em 1.2em; font-weight: bold; border: none; }}
.card {{ background-color: {card_color}; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }}
@media screen and (max-width: 768px) {{ .card {{ padding: 1rem; }} }}
.navbar {{ position: fixed; top: 0; width: 100%; background-color: {nav_color}; display: flex; justify-content: center; gap: 1.5rem; padding: 0.7rem 1rem; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
.navbar a {{ color: {text_color}; text-decoration: none; font-weight: 500; font-size: 1rem; padding: 0.3rem 0.6rem; transition: all 0.2s; }}
.navbar a:hover {{ color: #1f77d0; }}
</style>
<div class="navbar">
<a href="#home">🏠 Home</a>
<a href="#aqi">🌫️ AQI</a>
<a href="#weather">🌦️ Weather</a>
<a href="#map">🗺️ Map</a>
<a href="#tips">💡 Tips</a>
</div>""", unsafe_allow_html=True)

# --- API KEYS ---
WAQI_TOKEN = " f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2
"
OPENWEATHER_API_KEY = "19ad1b0624de0640e7b607d1a8b52314"

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

def get_aqi_category(aqi):
    if aqi <= 50: return "🟢 Good (0-50)", "#A8E6CF"
    elif aqi <= 100: return "🟡 Moderate (51-100)", "#FFD3B6"
    elif aqi <= 150: return "🟠 Sensitive (101-150)", "#FFAAA5"
    elif aqi <= 200: return "🔴 Unhealthy (151-200)", "#FF8C94"
    elif aqi <= 300: return "🟣 Very Unhealthy (201-300)", "#D291BC"
    else: return "⚫ Hazardous (301+)" , "#B5838D"

def get_health_tip(aqi):
    if aqi <= 50: return "✅ Air is clean. Great day to be outdoors!"
    elif aqi <= 100: return "☁️ Sensitive groups should reduce prolonged outdoor exertion."
    elif aqi <= 150: return "😷 Avoid heavy outdoor exercise. Consider wearing a mask."
    elif aqi <= 200: return "⚠️ Everyone should limit prolonged outdoor exertion."
    elif aqi <= 300: return "❌ Stay indoors and use air purifiers."
    else: return "🚨 Health emergency! Avoid all outdoor activities."

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

# --- APP UI ---
st.title("🌍 Clean Air Monitor")
st.caption("Real-time AQI with insights, tips, and weather forecast.")

st.markdown("<a name='home'></a>", unsafe_allow_html=True)
use_gps = st.button("📡 Use My Location")

if use_gps:
    st.info("GPS access requires custom implementation or parameters.")
    lat, lon, city = 9.31575, 76.61513, "Default"
else:
    city_input = st.text_input("Enter city name (optional)")
    if city_input:
        try:
            res = requests.get("https://nominatim.openstreetmap.org/search", params={"format": "json", "q": city_input}, headers={"User-Agent": "air-app"}, timeout=5)
            geocode = res.json()
            lat = float(geocode[0]['lat'])
            lon = float(geocode[0]['lon'])
            city = city_input
        except:
            st.error("Could not locate city. Using default.")
            lat, lon, city = 9.31575, 76.61513, "Default"
    else:
        lat, lon, city = 9.31575, 76.61513, "Default"

st.markdown("<a name='aqi'></a>", unsafe_allow_html=True)
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

    st.markdown(f"""
    <div class='card' style='background-color:{color}'>
        <h2>📍 {city}</h2>
        <h1>🌫️ AQI: {aqi} - {category}</h1>
        <p>Station: {station} | Updated: {updated}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<a name='weather'></a>", unsafe_allow_html=True)
    st.subheader("🌦️ Current Weather")
    if weather.get("main"):
        st.write(f"**Temp:** {weather['main']['temp']} °C")
        st.write(f"**Desc:** {weather['weather'][0]['description'].capitalize()}")
        st.write(f"**Humidity:** {weather['main']['humidity']}%")
        st.write(f"**Wind:** {weather['wind']['speed']} m/s")

    if forecast.get("list"):
        st.subheader("🔮 3-Day Forecast")
        days = {}
        for item in forecast["list"]:
            date = item["dt_txt"].split()[0]
            days.setdefault(date, []).append(item)
        for i, (d, entries) in enumerate(days.items()):
            if i == 3: break
            temps = [e["main"]["temp"] for e in entries]
            descs = [e["weather"][0]["description"] for e in entries]
            st.write(f"📅 {d}: {max(set(descs), key=descs.count).capitalize()} | Avg Temp: {sum(temps)/len(temps):.1f} °C")

    st.markdown("<a name='map'></a>", unsafe_allow_html=True)
    st.subheader("📍 AQI Station Map")
    show_map(lat, lon, station)

    st.markdown("<a name='tips'></a>", unsafe_allow_html=True)
    st.success(f"💡 Tip of the Day: {get_random_tip()}")

    with st.expander("📊 View Pollutants"):
        for k, v in pollutant_data.items():
            st.write(f"**{k.upper()}**: {v['v']}")

else:
    st.error("❌ Failed to fetch AQI data. Try again later.")
