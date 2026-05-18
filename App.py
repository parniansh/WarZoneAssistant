import streamlit as st
import folium
from streamlit_folium import st_folium
import sqlite3
import atexit
import subprocess

from Config import DB_PATH
from Gemma import query_gemma

from MockData import insert_mock_data
from MockResources import insert_mock_resources

insert_mock_data()
insert_mock_resources()

from utils.OllamaManager import ensure_ollama

with st.spinner("Starting AI model..."):
    result = ensure_ollama()
    if result["status"] == "started":
        st.toast("Gemma 4 model started", icon="✅")


def stop_ollama():
    subprocess.run(["ollama", "stop", "gemma4:e2b"])

atexit.register(stop_ollama)

st.set_page_config(
    page_title="WarZone Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@400;600;700&display=swap');

:root {
  --bg: #0a0c0f;
  --surface: #12161c;
  --border: #1f2933;
  --accent: #e63946;
  --accent2: #f4a261;
  --safe: #2a9d8f;
  --text: #e8eaf0;
  --muted: #6b7585;
  --mono: 'Share Tech Mono', monospace;
  --sans: 'Barlow', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

.app-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0 12px 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.app-header h1 {
  font-family: var(--mono);
  font-size: 1.3rem;
  color: var(--accent);
  margin: 0;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--safe);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.loc-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 12px;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--muted);
}

.msg-user {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px 12px 2px 12px;
  padding: 12px 16px;
  margin: 8px 0 8px 40px;
  color: var(--text);
}

.msg-assistant {
  background: #0f1a14;
  border: 1px solid #1a3322;
  border-left: 3px solid var(--safe);
  border-radius: 2px 12px 12px 12px;
  padding: 12px 16px;
  margin: 8px 40px 8px 0;
  color: var(--text);
  white-space: pre-wrap;
}

.msg-warning {
  background: #1a1200;
  border: 1px solid #3d2e00;
  border-left: 3px solid var(--accent2);
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 8px;
  color: var(--accent2);
  font-family: var(--mono);
  font-size: 0.85rem;
}

[data-testid="stButton"] button {
  background: var(--accent) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: var(--mono) !important;
  font-weight: 600 !important;
  letter-spacing: 1px !important;
}

[data-testid="stButton"] button:hover {
  background: #c1121f !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "messages": [],
    "show_map": False,
    "user_lat": 35.6892,
    "user_lon": 51.3890,
    "country": "Iran",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

SEVERITY_COLORS = {
    "critical": "#e63946",
    "high": "#f4a261",
    "medium": "#e9c46a",
    "low": "#2a9d8f",
}


def build_map(user_lat, user_lon, country):
    center_lat = user_lat or 35.6892
    center_lon = user_lon or 51.3890

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="CartoDB dark_matter",
    )

    if user_lat and user_lon:
        folium.CircleMarker(
            location=[user_lat, user_lon],
            radius=10,
            color="#ffffff",
            fill=True,
            fill_color="#4cc9f0",
            fill_opacity=0.9,
            popup="📍 You are here",
            tooltip="Your location",
        ).add_to(m)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_type, region, latitude, longitude, severity, description, timestamp
        FROM conflict_events WHERE is_active = 1 AND country = ?
        ORDER BY timestamp DESC LIMIT 100
    """, (country,))
    for event_type, region, lat, lon, severity, desc, ts in cursor.fetchall():
        color = SEVERITY_COLORS.get(severity, "#e63946")
        folium.CircleMarker(
            location=[lat, lon], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>[{severity.upper()}] {event_type}</b><br>{region}<br>{ts}<br><small>{desc[:200] if desc else ''}</small>",
                max_width=300,
            ),
            tooltip=f"⚠️ {event_type} — {region}",
        ).add_to(m)

    cursor.execute("""
        SELECT resource_type, name, region, latitude, longitude, address, phone
        FROM static_resources WHERE country = ?
    """, (country,))
    for rtype, name, region, lat, lon, address, phone in cursor.fetchall():
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"<b>🏥 {name}</b><br>{rtype}<br>{address or ''}<br>{phone or ''}", max_width=250),
            tooltip=f"🏥 {name}",
            icon=folium.Icon(color="blue", icon="plus-sign"),
        ).add_to(m)

    cursor.execute("""
        SELECT resource_type, name, region, latitude, longitude, description
        FROM dynamic_resources WHERE country = ? AND is_active = 1
    """, (country,))
    for rtype, name, region, lat, lon, desc in cursor.fetchall():
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"<b>⚡ {name}</b><br>{rtype}<br><small>{desc[:200] if desc else ''}</small>", max_width=250),
            tooltip=f"⚡ {name}",
            icon=folium.Icon(color="orange", icon="home"),
        ).add_to(m)

    conn.close()
    return m


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="status-dot"></div>
  <h1>⚡ WARZONE ASSISTANT</h1>
</div>
""", unsafe_allow_html=True)

# ── Status row ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])

with col1:
    st.markdown(
        f'<div class="loc-badge">📍 {st.session_state.user_lat:.4f}, {st.session_state.user_lon:.4f}</div>',
        unsafe_allow_html=True,
    )

with col2:
    if st.button("🗺 Map"):
        st.session_state.show_map = not st.session_state.show_map

# ── Map ────────────────────────────────────────────────────────────────────────
if st.session_state.show_map:
    m = build_map(st.session_state.user_lat, st.session_state.user_lon, st.session_state.country)
    st_folium(m, width="100%", height=430, returned_objects=[])

st.markdown("---")

# ── Chat history ───────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        if msg.get("warning"):
            st.markdown(f'<div class="msg-warning">⚠️ {msg["warning"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

# ── Chat input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask anything — first aid, safe routes, resources...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner(""):
        chat_text, warning = query_gemma(
            user_query=user_input,
            user_lat=st.session_state.user_lat,
            user_lon=st.session_state.user_lon,
            country=st.session_state.country,
            has_internet=True,
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": chat_text,
        "warning": warning,
    })

    location_keywords = ["safe", "hospital", "water", "shelter", "food", "route",
                         "move", "go", "north", "south", "east", "west", "where"]

    if st.session_state.user_lat and any(kw in user_input.lower() for kw in location_keywords):
        st.session_state.show_map = True

    st.rerun()