import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium
import random
import os

st.set_page_config(page_title="Air Pollution App", layout="wide")

st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

WAQI_TOKEN = "f1c44fa6a73e8ac0b6d9f23b3166481ff6a281d2"
aqi_log_file = "aqi_log.csv"

def get_aqi_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    return requests.get(url).json()

def get_aqi_category(aqi):
    if aqi <= 50:
        return "🟢 Good", "#66bb6a"
    elif aqi <= 100:
        return "🟡 Moderate", "#ffeb3b"
    elif aqi <= 150:
        return "🟠 Unhealthy for Sensitive Groups", "#ffb74d"
    elif aqi <= 200:
        return "🔴 Unhealthy", "#ef5350"
    elif aqi <= 300:
        return "🟣 Very Unhealthy", "#ba68c8"
    else:
        return "⚫ Hazardous", "#8d6e63"

def get_health_tip(aqi):
    if aqi <= 50:
        return "✅ Clean air today! Enjoy your outdoor activities."
    elif aqi <= 100:
        return "☁️ Sensitive groups should take it easy outdoors."
    elif aqi <= 150:
        return "😷 Try wearing a mask outdoors."
    elif aqi <= 200:
        return "⚠️ Everyone should reduce outdoor activities."
    elif aqi <= 300:
        return "❌ Stay indoors if possible."
    else:
        return "🚨 Avoid outdoor exposure completely."

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
        "💡 Keep indoor plants like peace lily or aloe vera.",
        "🌀 Use HEPA filters at home.",
        "📱 Check AQI before going out!",
        "🚴‍♀️ Use public transport on poor AQI days.",
    ]
    return random.choice(tips)

def show_map(lat, lon, name="Location"):
    m = folium.Map(location=[lat, lon], zoom_start=10)
    folium.Marker([lat, lon], tooltip=name, icon=folium.Icon(color="blue")).add_to(m)
    st_folium(m, width=700, height=300)

# --- APP START ---
st.title("🌍 Real-Time Air Pollution Dashboard")
st.caption("Track AQI, pollutants, health risks, and more.")

st.markdown("### 📍 Enter Your Location Coordinates")

lat = st.number_input("Latitude", value=9.3157, format="%.6f")
lon = st.number_input("Longitude", value=76.6151, format="%.6f")

if st.button("🔍 Get Air Quality Data"):
    with st.spinner("Fetching AQI data..."):
        data = get_aqi_data(lat, lon)

    if data["status"] == "ok":
        aqi = data["data"]["aqi"]
        station = data["data"]["city"]["name"]
        updated = data["data"]["time"]["s"]
        city = station.split(",")[0]
        pollutant_data = data["data"].get("iaqi", {})

        category, color = get_aqi_category(aqi)
        tip = get_health_tip(aqi)

        log_aqi(city, aqi)

        st.markdown(f"""
        <div style='background-color:{color}; padding:20px; border-radius:10px'>
            <h2 style='color:white;'>📍 {city}</h2>
            <h1 style='color:white;'>🌫️ AQI: {aqi} - {category}</h1>
            <p style='color:white;'>Station: {station} <br> Updated: {updated}</p>
        </div>
        """, unsafe_allow_html=True)

        st.info(tip)
        st.success(f"🌱 Tip of the Day: {get_random_tip()}")

        with st.expander("🧪 Pollutants Detected"):
            for key, val in pollutant_data.items():
                st.write(f"**{key.upper()}**: {val['v']}")

        st.subheader("📍 Map View")
        show_map(lat, lon, station)

        # Historical Chart
        if os.path.exists(aqi_log_file):
            df = pd.read_csv(aqi_log_file)
            df_city = df[df["city"] == city]
            if not df_city.empty:
                st.subheader("📈 AQI Trend (Local History)")
                fig = px.line(df_city, x="date", y="aqi", title=f"AQI Trend for {city}", markers=True)
                st.plotly_chart(fig)
                st.download_button("⬇️ Download AQI Data", data=df_city.to_csv(index=False), file_name=f"{city}_aqi_history.csv")
    else:
        st.error("❌ Could not retrieve AQI data for this location.")

