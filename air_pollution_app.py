import streamlit as st
import requests
import datetime
import folium
from streamlit_folium import st_folium
import random
import os
import streamlit.components.v1 as components
import json
from streamlit_lottie import st_lottie

# --- CONFIG ---
st.set_page_config(page_title="Clean Air Monitor", layout="wide")

# --- THEME-AWARE STYLING ---
theme = st.get_option("theme.base")

if theme == "dark":
    background_color = "#1e1e1e"
    text_color = "#f1f1f1"
    card_color = "#2a2a2a"
else:
    background_color = "#f4f6f9"
    text_color = "#2e2e2e"
    card_color = "white"

st.markdown(f"""
    <style>
    html, body {{
        background-color: {background_color};
        font-family: 'Segoe UI', sans-serif;
        color: {text_color};
    }}
    .main > div:first-child {{
        padding-top: 0rem;
    }}
    h1, h2, h3, h4 {{
        color: {text_color};
    }}
    .stButton>button {{
        background-color: #1f77d0;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
    }}
    .card {{
        background-color: {card_color};
        color: {text_color};
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOAD LOTTIE ANIMATION ---
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_air = load_lottie_url("https://lottie.host/64f76a6e-c002-4c2e-b2c1-fb2d09fdba3d/WnmzQZPtCk.json")
st_lottie(lottie_air, height=180, key="air-quality")

# --- AI CHATBOT (Mock Version) ---
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🤖 Ask AirBot - Your AQI Assistant")
user_question = st.text_input("Type your question about air quality or health")

if user_question:
    if "mask" in user_question.lower():
        st.info("😷 Yes, wearing a mask is recommended when AQI is above 100, especially if you have breathing issues.")
    elif "exercise" in user_question.lower():
        st.info("🏃‍♀️ It's best to avoid heavy outdoor exercise when AQI exceeds 150.")
    elif "good aqi" in user_question.lower():
        st.success("🟢 AQI between 0 and 50 is considered good and safe for outdoor activities.")
    else:
        st.info("💬 I'm still learning! Please ask about AQI levels, masks, or health tips.")
st.markdown("</div>", unsafe_allow_html=True)

# --- API KEYS ---
WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
OPENWEATHER_API_KEY = "19ad1b0624de0640e7b607d1a8b52314"

# --- HELPER FUNCTIONS ---
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
    if aqi <= 50:
        return "🟢 Good (0-50)", "#A8E6CF"
    elif aqi <= 100:
        return "🟡 Moderate (51-100)", "#FFD3B6"
    elif aqi <= 150:
        return "🟠 Unhealthy for Sensitive Groups (101-150)", "#FFAAA5"
    elif aqi <= 200:
        return "🔴 Unhealthy (151-200)", "#FF8C94"
    elif aqi <= 300:
        return "🟣 Very Unhealthy (201-300)", "#D291BC"
    else:
        return "⚫ Hazardous (301+)" , "#B5838D"

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

# --- LOCATION INPUT ---
st.title("🌍 Clean Air Monitor")
st.caption("Real-time AQI with insights, health tips, and weather.")

city_input = st.text_input("Enter city name (or leave blank for default)")
if city_input:
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "q": city_input},
            headers={"User-Agent": "air-pollution-app"},
            timeout=5
        )
        res.raise_for_status()
        geocode = res.json()
        if geocode:
            lat = float(geocode[0]['lat'])
            lon = float(geocode[0]['lon'])
            city = city_input
        else:
            st.error("City not found. Using default location.")
            lat, lon, city = 9.31575, 76.61513, "Chengannur"
    except:
        st.error("Location lookup failed. Using default.")
        lat, lon, city = 9.31575, 76.61513, "Chengannur"
else:
    lat, lon, city = 9.31575, 76.61513, "Chengannur"

# --- FETCH AND DISPLAY DATA ---
with st.spinner("Loading AQI and weather data..."):
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
    <div class='card'>
        <h2>📍 {city}</h2>
        <h1>🌫️ AQI: {aqi} - {category}</h1>
        <p>Nearest station: {station} <br> Updated: {updated}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📈 View Details"):
        st.info(tip)

        if weather.get("main"):
            st.subheader("🌦️ Current Weather")
            st.write(f"**Temperature:** {weather['main']['temp']} °C")
            st.write(f"**Condition:** {weather['weather'][0]['description'].capitalize()}")
            st.write(f"**Humidity:** {weather['main']['humidity']}%")
            st.write(f"**Wind Speed:** {weather['wind']['speed']} m/s")

        if forecast.get("list"):
            st.subheader("🔮 3-Day Forecast")
            forecast_by_day = {}
            for item in forecast["list"]:
                date = item["dt_txt"].split(" ")[0]
                forecast_by_day.setdefault(date, []).append(item)
            for i, (date, entries) in enumerate(forecast_by_day.items()):
                if i >= 3:
                    break
                avg_temp = sum(entry["main"]["temp"] for entry in entries) / len(entries)
                descs = [entry["weather"][0]["description"] for entry in entries]
                main_desc = max(set(descs), key=descs.count)
                st.write(f"📅 {date}: {main_desc.capitalize()}, 🌡️ Avg Temp: {avg_temp:.1f} °C")

        with st.expander("🧪 Pollutant Levels"):
            for key, val in pollutant_data.items():
                st.write(f"**{key.upper()}**: {val['v']}")

        st.subheader("📍 Nearest AQI Station")
        show_map(lat, lon, station)

    st.success(f"🌱 Tip of the Day: {get_random_tip()}")
else:
    st.error("❌ Could not load AQI data. Try again later.")
