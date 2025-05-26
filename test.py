import streamlit as st
import requests
import json

# Set your TomTom API Key
tomtom_key = "WTxGdKWBElQSCO0aIOzF0Ohrcjf4bmjj"

# Define coordinates for the default center (e.g., New York City)
default_center = {
    "lat": 40.7128,
    "lon": -74.0060
}

# Function to call TomTom Routing API
def get_route_data(origin, destination):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json?traffic=true&key={tomtom_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Function to call TomTom Incident Details API
def get_incidents(min_lat, min_lon, max_lat, max_lon):
    url = (
        f"https://api.tomtom.com/traffic/services/5/incidentDetails"
        f"?key={tomtom_key}"
        f"&bbox={min_lon},{min_lat},{max_lon},{max_lat}"
        f"&fields={{incidents{{type,geometry{{type,coordinates}},properties{{iconCategory}}}}}}"
        f"&language=en-GB&t=1111"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# UI
st.set_page_config(layout="wide")
st.title("📍 Real-Time Traffic Assistant with TomTom")

# Map display and chat interface
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Map View")
    html_code = f"""
    <script src='https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.15.0/maps/maps-web.min.js'></script>
    <script src='https://api.tomtom.com/maps-sdk-for-web/cdn/6.x/6.15.0/services/services-web.min.js'></script>
    <div id='map' style='width: 100%; height: 600px;'></div>
    <script>
      var map = tt.map({{
        key: '{tomtom_key}',
        container: 'map',
        center: [{default_center['lon']}, {default_center['lat']}],
        zoom: 12,
        style: 'https://api.tomtom.com/style/2/custom/style/dG9tdG9tQEBAR3pYS2c4bnV3Q0VqY2hRRDtDEtxJvltMQ4S2fXbinges/drafts/0.json?key=WTxGdKWBElQSCO0aIOzF0Ohrcjf4bmjj'
      }});
      var flowLayer = new tt.TrafficFlowTilesTier({{key: '{tomtom_key}'}});
      var incidentLayer = new tt.TrafficIncidentTier({{key: '{tomtom_key}'}});
      map.addTier(flowLayer);
      map.addTier(incidentLayer);
    </script>
    """
    st.components.v1.html(html_code, height=600)

with col2:
    st.subheader("🧠 Traffic Assistant Chat")
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about traffic, route or incidents"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Basic keyword detection
        answer = "I'm sorry, I didn't understand that. Try asking about a route or incidents."

        if "route" in prompt.lower():
            origin = st.text_input("Enter origin (lat,lon)", value="40.7128,-74.0060")
            destination = st.text_input("Enter destination (lat,lon)", value="40.730610,-73.935242")
            if origin and destination:
                data = get_route_data(origin, destination)
                if data:
                    summary = data["routes"][0]["summary"]
                    length_km = summary["lengthInMeters"] / 1000
                    eta_min = summary["travelTimeInSeconds"] / 60
                    answer = f"Distance: {length_km:.1f} km, Estimated travel time: {eta_min:.1f} minutes."
        elif "incidents" in prompt.lower():
            incidents_data = get_incidents(40.60, -74.10, 40.80, -73.90)
            if incidents_data and "incidents" in incidents_data:
                count = len(incidents_data["incidents"])
                answer = f"There are {count} traffic incidents in your selected area."

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
