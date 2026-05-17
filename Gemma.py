import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timezone

from Config import DB_PATH, OLLAMA_URL, OLLAMA_MODEL
from Updater import haversine

SYSTEM_PROMPT_PATH = Path(__file__).parent / "systemPrompt.txt"
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def get_last_updated(country: str) -> str:
    """Get the most recent successful fetch timestamp from fetch_log."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fetched_at FROM fetch_log
        WHERE source = 'ACLED' AND status = 'success'
        ORDER BY fetched_at DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "unknown"


def get_events_by_location(user_lat: float, user_lon: float, country: str) -> list:
    """Pull events sorted by distance from user. Used for cases 1 and 2."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, region, latitude, longitude, severity, description, timestamp
        FROM conflict_events
        WHERE is_active = 1 AND country = ?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (country,))
    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        event_type, region, lat, lon, severity, desc, timestamp = row
        dist = haversine(user_lat, user_lon, lat, lon)
        events.append({
            "event_type": event_type,
            "region": region,
            "distance_km": round(dist, 1),
            "severity": severity,
            "description": desc,
            "timestamp": timestamp,
        })

    events.sort(key=lambda x: x["distance_km"])
    return events[:15]


def get_events_by_severity(country: str) -> list:
    """Pull 15 most severe country-wide events. Used for case 3 (no GPS)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, region, severity, description, timestamp
        FROM conflict_events
        WHERE is_active = 1 AND country = ?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (country,))
    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        event_type, region, severity, desc, timestamp = row
        events.append({
            "event_type": event_type,
            "region": region,
            "severity": severity,
            "description": desc,
            "timestamp": timestamp,
        })

    events.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))
    return events[:15]


def build_context(events: list, warning: str = "") -> str:
    """Format conflict events into a context string for the prompt."""
    if not events:
        return "No conflict events found in the database."

    lines = []
    if warning:
        lines.append(f"⚠️ {warning}\n")
    lines.append("Conflict events:\n")

    for e in events:
        location = f"{e['distance_km']} km away" if "distance_km" in e else e["region"]
        lines.append(
            f"- [{e['severity'].upper()}] {e['event_type']} in {e['region']} "
            f"({location}, {e['timestamp']}): {e['description']}"
        )
    return "\n".join(lines)


def query_gemma(user_query: str, user_lat: float = None, user_lon: float = None,
                country: str = None, has_internet: bool = True) -> str:
    """Send a query to Gemma via Ollama with conflict context injected."""
    system_prompt = load_system_prompt()
    context = ""
    warning = ""

    if country:
        has_gps = user_lat is not None and user_lon is not None

        if has_gps and has_internet:
            # Case 1: GPS + internet — closest events, no warning
            events = get_events_by_location(user_lat, user_lon, country)
            context = build_context(events)

        elif has_gps and not has_internet:
            # Case 2: GPS + no internet — closest events from stale db, warn
            last_updated = get_last_updated(country)
            warning = f"No internet connection. Showing last known data. Last updated: {last_updated}"
            events = get_events_by_location(user_lat, user_lon, country)
            context = build_context(events)

        elif not has_gps and has_internet:
            # Case 3: No GPS + internet — most severe country-wide events, warn
            warning = f"Location unavailable. Showing highest severity events for {country}."
            events = get_events_by_severity(country)
            context = build_context(events)

    # Compose full prompt
    full_prompt = user_query
    if context:
        full_prompt = f"[CONFLICT DATA]\n{context}\n\n[USER QUERY]\n{user_query}"
    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": full_prompt,
        "stream": False,
        "think": True
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=220)
        response.raise_for_status()
        response_text = response.json().get("response", "No response from model.")
        if warning:
            return f"⚠️ {warning}\n\n{response_text}"
        return response_text

    except Exception as e:
        return f"Error communicating with Gemma: {e}"


if __name__ == "__main__":
    # Quick test
    reply = query_gemma(
        user_query="Is it safe to move north right now?",
        # user_query="میخوام به سمت شمال برم. امن هست؟",
        user_lat=35.6892,
        user_lon=51.3890,
        country="Iran",
        has_internet=False

    )
    print(reply)