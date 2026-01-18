import streamlit as st
import cv2
import numpy as np
import requests
import time
import base64

# 1. Setup Page Configuration
st.set_page_config(page_title="AR Weather HUD", layout="wide")

# 2. Inject CSS (full-screen video & weather overlay)
st.markdown("""
    <style>
    /* Remove Streamlit default padding/margins */
    body, html, .stApp, .block-container, .css-18e3th9, .css-1d391kg {
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    /* Fullscreen video container */
    .video-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        z-index: 0;
    }
    .video-feed {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover; /* cover entire container */
        z-index: 1;
    }

    /* Weather overlay */
    .weather-overlay {
        position: absolute;
        bottom: 20px;
        right: 20px;
        z-index: 2;
        pointer-events: auto;
    }

    #weather-widget {
        width: 320px;
        background: rgba(255,255,255,0.6);
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        text-align: center;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: black;
    }
    #weather-widget div, #weather-widget span, #weather-widget b {
        color: black;
    }

    /* SVG & Animation Styles */
    .sun-core { fill: #FFD54A; }
    .sun-rays { fill: #FFD54A; opacity: 0.85; transform-origin: 50% 50%; animation: spin 12s linear infinite; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .cloud { fill: rgba(255,255,255,0.96); stroke: rgba(0,0,0,0.06); stroke-width: 1; }

    #temp { font-size: 48px; font-weight: 300; margin: 0; color: black; }

    .hours { display: flex; justify-content: space-between; margin-top: 14px; gap: 8px; }
    .hour-item { 
        flex: 1; background: rgba(255,255,255,0.28); border-radius: 10px; 
        padding: 6px; font-size: 12px; display: flex; flex-direction: column; 
        color: black;
    }
    </style>
""", unsafe_allow_html=True)


# 3. Weather Fetcher
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=49.2593&longitude=-123.2475&hourly=temperature_2m,precipitation_probability,wind_speed_10m&forecast_days=1"
    try:
        r = requests.get(url)
        data = r.json()
        return {
            "temp": int(data["hourly"]["temperature_2m"][0]),
            "precip": int(data["hourly"]["precipitation_probability"][0]),
            "wind": int(data["hourly"]["wind_speed_10m"][0]),
            "next_hours": [int(t) for t in data["hourly"]["temperature_2m"][1:6]]
        }
    except:
        return None

weather = get_weather()
container = st.empty()

# 4. Camera Setup
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # 0 or 1 depending on your camera
# Set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# 5. Main Loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Encode the image
    _, buffer = cv2.imencode('.jpg', frame)
    img_str = base64.b64encode(buffer).decode()

    # Create the dynamic hour items
    hour_html = ""
    if weather:
        for i, t in enumerate(weather['next_hours']):
            hour_html += f'<div class="hour-item"><span>+{i+1}h</span><b>{t}°</b></div>'

    # HUD HTML
    hud_content = f"""
    <div class="video-container">
        <img class="video-feed" src="data:image/jpeg;base64,{img_str}">
        <div class="weather-overlay">
            <div id="weather-widget">
                <div id="temp">{weather['temp'] if weather else '--'}°C</div>
                <div id="details">
                    <div>{weather['precip'] if weather else '--'}% rain</div>
                    <div>{weather['wind'] if weather else '--'} km/h wind</div>
                </div>
                <div class="hours">
                    {hour_html}
                </div>
            </div>
        </div>
    </div>
    """
    
    container.markdown(hud_content, unsafe_allow_html=True)
    
    time.sleep(0.01)

cap.release()
