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

# --- GLOBAL STYLING ---
st.markdown("""
    <style>
    html, body {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', sans-serif;
        color: #2e2e2e;
    }
    .main > div:first-child {
        padding-top: 0rem;
    }
    h1, h2, h3, h4 {
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #1f77d0;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- API KEYS ---
WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
OPENWEATHER_API_KEY = "19ad1b0624de0640e7b607d1a8b52314"

# --- AQI CATEGORIES ---
def get_aqi_category(aqi):
    if aqi <= 50:
        return "🟢 Good (0–50)", "#A8E6CF"
    elif aqi <= 100:
        return "🟡 Moderate (51–100)", "#FFD3B6"
    elif aqi <= 150:
        return "🟠 Unhealthy for Sensitive Groups (101–150)", "#FFAAA5"
    elif aqi <= 200:
        return "🔴 Unhealthy (151–200)", "#FF8C94"
    elif aqi <= 300:
        return "🟣 Very Unhealthy (201–300)", "#D291BC"
    else:
        return "⚫ Hazardous (301+)", "#B5838D"

# --- HEALTH TIP ---
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

# --- RANDOM TIPS ---
def get_random_tip():
    tips = [
        "💡 Use indoor plants like spider plant to improve air quality.",
        "🌀 Use HEPA filters to clean indoor air.",
        "🏃‍♀️ Exercise indoors on high AQI days.",
        "📱 Check AQI before outdoor plans!",
        "🪟 Close windows during high pollution times."
    ]
    return random.choice(tips)

pollutant_info = {
    "pm25": "PM2.5 - Fine particles that can enter bloodstream.",
    "pm10": "PM10 - Can irritate lungs and throat.",
    "no2": "NO₂ - Common in vehicle exhaust.",
    "so2": "SO₂ - Comes from coal burning.",
    "o3": "O₃ - Ground-level ozone, harmful.",
    "co": "CO - Carbon Monoxide, dangerous in high amounts.",
    "nh3": "NH₃ - Ammonia, irritating to eyes and lungs."
}

# --- API CALLS ---
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

# --- LOCATION ---
def get_browser_location():
    location_param = st.query_params.get("location")
    if not location_param:
        components.html("""
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
        """, height=0)
        st.info("🔄 Attempting to fetch GPS location... please allow it in your browser.")
        st.stop()
    try:
        coords = json.loads(location_param[0])
        return coords['latitude'], coords['longitude'], "Live GPS"
    except:
        return None, None, None

# --- MAP ---
def show_map(lat, lon, station_name):
    m = folium.Map(location=[lat, lon], zoom_start=10)
    folium.Marker([lat, lon], tooltip=station_name, icon=folium.Icon(color="blue")).add_to(m)
    st_folium(m, width=700, height=300)

# --- MAIN APP ---
st.title("🌍 Clean Air Monitor")
st.caption("Real-time AQI with weather, tips, and pollutant insights")

st.sidebar.title("Navigation")
st.sidebar.markdown("- 📍 Location Input\n- 🌫️ AQI Info\n- 🌦️ Weather\n- 🧪 Pollutants\n- 💡 Tips\n- 🗺️ Map")

use_gps = st.button("📡 Use My Location")
if use_gps:
    lat, lon, city = get_browser_location()
else:
    city_input = st.text_input("Enter city name")
    if city_input:
        res = requests.get("http://api.openweathermap.org/geo/1.0/direct",
                          params={"q": city_input, "limit": 1, "appid": OPENWEATHER_API_KEY})
        geocode = res.json()
        if geocode:
            lat = geocode[0]['lat']
            lon = geocode[0]['lon']
            city = geocode[0]['name']
        else:
            lat, lon, city = 9.31575, 76.61513, "Chengannur"
    else:
        lat, lon, city = 9.31575, 76.61513, "Chengannur"

with st.spinner("Fetching data..."):
    aqi_data = get_aqi_data(lat, lon)
    weather = get_weather_data(lat, lon)
    forecast = get_forecast_data(lat, lon)

if aqi_data["status"] == "ok":
    aqi = aqi_data["data"]["aqi"]
    station = aqi_data["data"]["city"]["name"]
    updated = aqi_data["data"]["time"]["s"]
    category, color = get_aqi_category(aqi)
    tip = get_health_tip(aqi)
    pollutant_data = aqi_data["data"].get("iaqi", {})

    st.markdown(f"<div class='card'><h2>📍 {city}</h2><h3 style='color:{color}'>🌫️ AQI: {aqi} - {category}</h3><p>Station: {station} | Updated: {updated}</p></div>", unsafe_allow_html=True)
    st.success(f"🧠 Health Tip: {tip}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🌦️ Current Weather")
        st.write(f"**Temperature:** {weather['main']['temp']} °C")
        st.write(f"**Condition:** {weather['weather'][0]['description'].capitalize()}")
        st.write(f"**Humidity:** {weather['main']['humidity']}%")
        st.write(f"**Wind Speed:** {weather['wind']['speed']} m/s")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔮 3-Day Forecast")
        forecast_by_day = {}
        for item in forecast["list"]:
            date = item["dt_txt"].split(" ")[0]
            if date not in forecast_by_day:
                forecast_by_day[date] = []
            forecast_by_day[date].append(item)
        count = 0
        for date, entries in forecast_by_day.items():
            if count == 3:
                break
            temps = [e['main']['temp'] for e in entries]
            avg_temp = sum(temps) / len(temps)
            descs = [e['weather'][0]['description'] for e in entries]
            common_desc = max(set(descs), key=descs.count).capitalize()
            st.write(f"📅 {date}: {common_desc}, Avg Temp: {avg_temp:.1f} °C")
            count += 1
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🧪 Pollutant Details")
    for key, val in pollutant_data.items():
        if key.lower() in pollutant_info:
            with st.expander(f"{key.upper()} - {val['v']}"):
                st.write(pollutant_info[key.lower()])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📍 AQI Monitoring Station")
    show_map(lat, lon, station)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🌱 Tip of the Day")
    st.success(get_random_tip())
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("❌ Could not load AQI data. Try again later.")
