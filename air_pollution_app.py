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
st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    body {
        background-color: #f5f7fa;
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3, h4, h5 {
        color: #222;
    }
    .stButton>button {
        background-color: #3c91e6;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1f77d0;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #ddd;
    }
    </style>
""", unsafe_allow_html=True)

# --- API KEYS ---
WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
OPENWEATHER_API_KEY = "19ad1b0624de0640e7b607d1a8b52314"

# --- AQI CATEGORY RANGES ---
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

# --- RANDOM TIP ---
def get_random_tip():
    tips = [
        "💡 Use indoor plants like spider plant to improve air quality.",
        "🌀 Use HEPA filters to clean indoor air.",
        "🏃‍♀️ Exercise indoors on high AQI days.",
        "📱 Check AQI before outdoor plans!",
        "🪟 Close windows during high pollution times."
    ]
    return random.choice(tips)

# --- POLLUTANT EXPLANATIONS ---
pollutant_info = {
    "pm25": "Fine Particles (PM2.5) – Can penetrate lungs and enter bloodstream. Major health risk.",
    "pm10": "Coarse Particles (PM10) – Irritates nose, throat, and lungs.",
    "no2": "Nitrogen Dioxide (NO₂) – From vehicles and power plants. Can cause asthma and lung issues.",
    "so2": "Sulfur Dioxide (SO₂) – Comes from burning coal and oil. Irritates eyes and lungs.",
    "o3": "Ozone (O₃) – Forms in sunlight. Bad at ground level; causes chest pain and coughing.",
    "co": "Carbon Monoxide (CO) – From incomplete burning. Dangerous in high amounts.",
    "nh3": "Ammonia (NH₃) – From agriculture and cleaning products. Can irritate eyes and lungs."
}

# --- CACHED API CALLS ---
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

# --- LOCATION FETCH ---
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

# --- FOLIUM MAP ---
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
                "http://api.openweathermap.org/geo/1.0/direct",
                params={"q": city_input, "limit": 1, "appid": OPENWEATHER_API_KEY},
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
            city = geocode[0].get("name", city_input)
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

    st.markdown(f"""
    <div style='background-color:{color}; padding:25px; border-radius:15px; border: 2px solid black;'>
        <div style='background-color: rgba(255,255,255,0.85); padding: 15px; border-radius: 10px;'>
            <h2 style='color:black;'>📍 {city}</h2>
            <h1 style='color:black;'>🌫️ AQI: {aqi} - {category}</h1>
            <p style='color:black;'>Nearest station: {station} <br> Updated: {updated}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info(tip)

    if weather.get("main"):
        st.subheader("🌦️ Local Weather Conditions")
        temp = weather["main"]["temp"]
        desc = weather["weather"][0]["description"].capitalize()
        humidity = weather["main"]["humidity"]
        wind = weather["wind"]["speed"]
        icon_code = weather["weather"][0]["icon"]
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        st.image(icon_url, width=80)
        st.write(f"**Temperature:** {temp} °C")
        st.write(f"**Weather:** {desc}")
        st.write(f"**Humidity:** {humidity}%")
        st.write(f"**Wind Speed:** {wind} m/s")

    if forecast.get("list"):
        st.subheader("🔮 3-Day Weather Forecast")
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
            avg_temp = sum(entry["main"]["temp"] for entry in entries) / len(entries)
            descs = [entry["weather"][0]["description"] for entry in entries]
            most_common_desc = max(set(descs), key=descs.count).capitalize()
            st.write(f"📅 {date}: {most_common_desc}, 🌡️ Avg Temp: {avg_temp:.1f} °C")
            count += 1

    if pollutant_data:
        st.subheader("🧪 View Pollutant Levels")
        for key, val in pollutant_data.items():
            explanation = pollutant_info.get(key.lower(), "No info available.")
            with st.expander(f"**{key.upper()}**: {val['v']}"):
                st.markdown(f"🔍 {explanation}")

    st.subheader("📍 Nearest AQI Station")
    show_map(lat, lon, station)

    st.success(f"🌱 Tip of the Day: {get_random_tip()}")

else:
    st.error("❌ Could not load AQI data. Try again later.")
