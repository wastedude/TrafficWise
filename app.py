import streamlit as st
import requests
from datetime import datetime

# API Keys
GROQ_API_KEY = "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"
HERE_API_KEY = "Z-INy7MKiZwfH6mAchEr0QPFaYuuo5QKqGxSnHxcKTY"

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'location_history' not in st.session_state:
    st.session_state.location_history = []
if 'current_map' not in st.session_state:
    st.session_state.current_map = None

# Page configuration
st.set_page_config(
    page_title="TrafficWise AI Assistant",
    page_icon="🚦",
    layout="wide"
)
st.title("🚦 TrafficWise AI Assistant")

def geocode_address(address):
    """Convert address to coordinates using HERE Geocoding API"""
    url = f"https://geocode.search.hereapi.com/v1/geocode"
    params = {
        'q': address,
        'apiKey': HERE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['items']:
            position = data['items'][0]['position']
            address_label = data['items'][0].get('address', {}).get('label', address)
            return position['lat'], position['lng'], address_label
        return None, None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None, None

def get_traffic_incidents(lat, lon, radius=1000):
    """Fetch traffic incidents from HERE API"""
    url = "https://data.traffic.hereapi.com/v7/incidents"
    params = {
        'apiKey': HERE_API_KEY,
        'in': f"circle:{lat},{lon};r={radius}",
        'locationReferencing': 'polyline'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Note: Traffic data may be limited in this area")
        return None

import streamlit.components.v1 as components

def generate_traffic_map(center_lat=30.3753, center_lng=69.3451, tomtom_api_key="WTxGdKWBElQSCO0aIOzF0Ohrcjf4bmjj"):
    """Generate TomTom map with live traffic and incidents using Web SDK v6"""

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TomTom Traffic Map</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" type="text/css" href="https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.18.0/maps/maps.css" />
        <style>
            html, body, #map {{
                height: 100%;
                margin: 0;
                padding: 0;
            }}
            #map {{
                width: 100%;
                height: 100vh;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script src="https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.18.0/maps/maps-web.min.js"></script>
        <script src="https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.18.0/services/services-web.min.js"></script>
        <script>
            const map = tt.map({{
                key: "{tomtom_api_key}",
                container: "map",
                center: [{center_lng}, {center_lat}],
                zoom: 14,
                style: "https://api.tomtom.com/style/2/custom/style/dG9tdG9tQEBAR3pYS2c4bnV3Q0VqY2hRRDtDEtxJvltMQ4S2fXbinges/drafts/0.json?key=WTxGdKWBElQSCO0aIOzF0Ohrcjf4bmjj"
            }});
            
            map.addControl(new tt.FullscreenControl());
            map.addControl(new tt.NavigationControl());

            // Add traffic flow + incidents layer
            map.once('load', function () {{
                map.addLayer({{
                    'id': 'trafficIncidents',
                    'type': 'line',
                    'source': {{
                        'type': 'vector',
                        'url': 'https://api.tomtom.com/traffic/services/4/incidentTiles/flowSegmentData/relative0/{tomtom_api_key}/tile.json'
                    }},
                    'source-layer': 'incidents',
                    'layout': {{
                        'visibility': 'visible'
                    }},
                    'paint': {{
                        'line-color': '#ff0033',
                        'line-width': 3
                    }}
                }});
                map.showTrafficFlow();
                map.showTrafficIncidents();
            }});
        </script>
    </body>
    </html>
    """

    # Render in Streamlit
    components.html(html_code, height=600)


# Sidebar configuration
st.sidebar.title("🚦 TrafficWise AI Assistant")
st.sidebar.markdown("Your AI Assistant for Traffic & all things related to traffic routes and congestion solutions.")

# Previous locations section
if st.session_state.location_history:
    st.sidebar.subheader("Recent Searches")
    for idx, (loc, timestamp) in enumerate(reversed(st.session_state.location_history[-5:])):
        if st.sidebar.button(f"📍 {loc} ({timestamp})", key=f"prev_loc_{idx}"):
            coordinates = geocode_address(loc)
            if coordinates[0]:
                st.session_state.current_map = generate_traffic_map(coordinates[0], coordinates[1])

# Location input
st.sidebar.subheader("Search Location")
location_input = st.sidebar.text_input(
    "Enter city or address:",
    key="location_input",
    placeholder="e.g., London, New York, Tokyo"
)


if location_input:
    lat, lng, address_label = geocode_address(location_input)
    if lat and lng:
        # Update location history
        timestamp = datetime.now().strftime("%H:%M")
        if address_label not in [loc for loc, _ in st.session_state.location_history]:
            st.session_state.location_history.append((address_label, timestamp))
        # Generate and store map
        st.session_state.current_map = generate_traffic_map(lat, lng)
        st.sidebar.success(f"📍 Showing Map for: {address_label} on the main page")
    else:
        st.sidebar.error("Location not found. Please try another address.")



# Temperature slider
temperature = st.sidebar.slider(
    "AI Response Variation:",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05,
    help="Higher values provide more varied suggestions, lower values offer more consistent advice"
)

# Main chat interface

st.markdown("""
### Your AI Assistant for:
- 🚗 Traffic Route Optimization

- 🚦 Traffic Flow Analysis

""")

def chat_with_traffic_planner(user_message, temperature):
    """Send a message to Groq API's model and return the response."""
    enhanced_prompt = f"""You are a real-time traffic assistant designed to provide accurate uptodate traffic insights. alwaysprioritize the following while responding to user queries: 1. cross verify data from multiple trusted sources, 2. start with a concise summary of the traffic situation and tell them to check on the map which is located on the sidebar, 3. adjust responses based on time of day, 4.flag weather related disruptions, 5. avoid jargon, use plain language. now answer this traffic question: {user_message}
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": enhanced_prompt}],
        "temperature": temperature
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to connect to the API - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def clear_chat():
    st.session_state.chat_history = []

def submit_message():
    if st.session_state.user_input:
        user_message = st.session_state.user_input
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        with st.spinner('Analyzing traffic patterns...'):
            bot_response = chat_with_traffic_planner(user_message, temperature)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        st.session_state.user_input = ""


# Display chat history
for idx, message in enumerate(st.session_state.chat_history):
    role = message["role"]
    content = message["content"]
    if role == "user":
        st.markdown(f"👤 You:** {content}")
    else:
        st.markdown(f"🚦 TrafficWise:** {content}")
    st.markdown("---")

st.text_input(
    "Ask about traffic routes, or congestion solutions...",
    key="user_input",
    on_change=submit_message,
    placeholder="Example: What are the best routes to reduce congestion during peak hours?"
)

if st.button("🗑 Clear Chat"):
    clear_chat()

st.sidebar.markdown("""
### 🚗 Traffic Guidelines:
1. 🕒 Peak Hours
   - Morning: 7-9 AM
   - Evening: 4-7 PM

2. 🚸 Safety First
   - Follow speed limits
   - Watch for pedestrians

3. 🌍 Eco-Friendly Options
   - Consider public transport
   - Use carpooling

4. 🚦 Smart Route Planning
   - Check traffic updates
   - Use alternative routes

5. 📱 Stay Informed
   - Monitor traffic alerts
   - Check weather conditions
""")