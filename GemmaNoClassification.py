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


def get_resources_by_location(user_lat: float, user_lon: float, country: str) -> list:
    """Pull nearest static + dynamic resources sorted by distance."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Static resources
    cursor.execute("""
        SELECT osm_id, resource_type, name, region, latitude, longitude, address, phone
        FROM static_resources
        WHERE country = ?
    """, (country,))
    static_rows = cursor.fetchall()

    # Dynamic resources
    cursor.execute("""
        SELECT resource_id, resource_type, name, region, latitude, longitude, description
        FROM dynamic_resources
        WHERE country = ? AND is_active = 1
    """, (country,))
    dynamic_rows = cursor.fetchall()
    conn.close()

    resources = []

    for row in static_rows:
        osm_id, rtype, name, region, lat, lon, address, phone = row
        dist = haversine(user_lat, user_lon, lat, lon)
        resources.append({
            "name": name,
            "type": rtype,
            "region": region,
            "distance_km": round(dist, 1),
            "detail": address or "",
            "phone": phone or "",
            "source": "permanent",
        })

    for row in dynamic_rows:
        rid, rtype, name, region, lat, lon, desc = row
        dist = haversine(user_lat, user_lon, lat, lon)
        resources.append({
            "name": name,
            "type": rtype,
            "region": region,
            "distance_km": round(dist, 1),
            "detail": desc or "",
            "phone": "",
            "source": "wartime",
        })

    resources.sort(key=lambda x: x["distance_km"])
    return resources[:15]


def get_resources_by_country(country: str) -> list:
    """Pull resources country-wide when no GPS. Wartime resources prioritized."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT resource_type, name, region, latitude, longitude, description
        FROM dynamic_resources
        WHERE country = ? AND is_active = 1
        LIMIT 10
    """, (country,))
    dynamic_rows = cursor.fetchall()

    cursor.execute("""
        SELECT resource_type, name, region, latitude, longitude, address
        FROM static_resources
        WHERE country = ?
        LIMIT 5
    """, (country,))
    static_rows = cursor.fetchall()
    conn.close()

    resources = []
    for row in dynamic_rows:
        rtype, name, region, lat, lon, desc = row
        resources.append({"name": name, "type": rtype, "region": region, "detail": desc, "source": "wartime"})
    for row in static_rows:
        rtype, name, region, lat, lon, address = row
        resources.append({"name": name, "type": rtype, "region": region, "detail": address or "", "source": "permanent"})

    return resources


def build_conflict_context(events: list) -> str:
    if not events:
        return ""
    lines = ["[CONFLICT EVENTS]"]
    for e in events:
        location = f"{e['distance_km']} km away" if "distance_km" in e else e["region"]
        lines.append(
            f"- [{e['severity'].upper()}] {e['event_type']} in {e['region']} "
            f"({location}, {e['timestamp']}): {e['description']}"
        )
    return "\n".join(lines)


def build_resource_context(resources: list) -> str:
    if not resources:
        return ""
    lines = ["[NEARBY RESOURCES]"]
    for r in resources:
        dist = f"{r['distance_km']} km away — " if "distance_km" in r else ""
        tag = "⚡ WARTIME" if r["source"] == "wartime" else "🏥 PERMANENT"
        phone = f" | Phone: {r['phone']}" if r.get("phone") else ""
        lines.append(f"- [{tag}] {r['name']} ({r['type']}) in {r['region']} — {dist}{r['detail']}{phone}")
    return "\n".join(lines)


def query_gemma(user_query: str, user_lat: float = None, user_lon: float = None,
                country: str = None, has_internet: bool = True) -> str:
    """Send query to Gemma with all context injected — no classification."""
    system_prompt = load_system_prompt()
    warning = ""
    conflict_context = ""
    resource_context = ""

    if country:
        has_gps = user_lat is not None and user_lon is not None

        if has_gps and has_internet:
            events = get_events_by_location(user_lat, user_lon, country)
            resources = get_resources_by_location(user_lat, user_lon, country)
            conflict_context = build_conflict_context(events)
            resource_context = build_resource_context(resources)

        elif has_gps and not has_internet:
            last_updated = get_last_updated(country)
            warning = f"No internet connection. Showing last known data. Last updated: {last_updated}"
            events = get_events_by_location(user_lat, user_lon, country)
            resources = get_resources_by_location(user_lat, user_lon, country)
            conflict_context = build_conflict_context(events)
            resource_context = build_resource_context(resources)

        elif not has_gps and has_internet:
            warning = f"Location unavailable. Showing data for {country}."
            events = get_events_by_severity(country)
            resources = get_resources_by_country(country)
            conflict_context = build_conflict_context(events)
            resource_context = build_resource_context(resources)

    # Compose full prompt
    context_parts = [c for c in [conflict_context, resource_context] if c]
    full_context = "\n\n".join(context_parts)

    full_prompt = user_query
    if full_context:
        full_prompt = f"{full_context}\n\n[USER QUERY]\n{user_query}"

    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": full_prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        response_text = response.json().get("response", "No response from model.")
        if warning:
            return f"⚠️ {warning}\n\n{response_text}"
        return response_text
    except Exception as e:
        return f"Error communicating with Gemma: {e}"


if __name__ == "__main__":
    import time

    queries = [
        "Is it safe to move north right now?",
        "Where can I find water near me?",
        "My friend is bleeding badly, what do I do?",
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        start = time.time()
        reply = query_gemma(
            user_query=q,
            user_lat=35.6892,
            user_lon=51.3890,
            country="Iran"
        )
        elapsed = round(time.time() - start, 1)
        print(f"Response ({elapsed}s):\n{reply}")
        print("-" * 60)