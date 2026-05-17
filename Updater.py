import sqlite3
import requests
import time
import math
from pathlib import Path
from datetime import datetime, timezone

from Config import (
    DB_PATH, ACLED_EMAIL, ACLED_PASSWORD,
    ACLED_AUTH_URL, ACLED_URL, ACLED_CLIENT_ID,
    ACLED_GRANT_TYPE, ACLED_SCOPE, ACLED_LIMIT,
    POLL_INTERVAL, PROXIMITY_RADIUS_KM
)

# --- STATE ---
USER_LAT = None
USER_LON = None
_access_token = None
_token_fetched_at = None
TOKEN_TTL = 82800  # 23 hours (refresh before 24hr expiry)


# --- AUTH ---

def get_access_token() -> str:
    """Fetch or reuse ACLED OAuth access token."""
    global _access_token, _token_fetched_at

    now = time.time()
    if _access_token and _token_fetched_at and (now - _token_fetched_at) < TOKEN_TTL:
        return _access_token

    response = requests.post(ACLED_AUTH_URL,
             headers={"Content-Type": "application/x-www-form-urlencoded"},
             data={
                 "username": ACLED_EMAIL,
                 "password": ACLED_PASSWORD,
                 "grant_type": ACLED_GRANT_TYPE,
                 "client_id": ACLED_CLIENT_ID,
                 "scope": ACLED_SCOPE,
             }, timeout=15)
    response.raise_for_status()
    _access_token = response.json()["access_token"]
    _token_fetched_at = now
    print("[Auth] New access token fetched.")
    return _access_token


# --- HELPERS ---

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_db():
    return sqlite3.connect(DB_PATH)


def fetch_acled_events(country: str) -> list:
    """Fetch latest conflict events from ACLED for a given country."""
    token = get_access_token()
    params = {
        "country": country,
        "limit": ACLED_LIMIT,
        "fields": "event_id_cnty|event_date|event_type|country|admin1|latitude|longitude|notes|fatalities",
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(ACLED_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"[ACLED] Fetch error: {e}")
        return []


def map_severity(event_type: str, fatalities: int) -> str:
    event_type = (event_type or "").lower()
    if fatalities > 10 or "battle" in event_type or "explosion" in event_type:
        return "critical"
    elif fatalities > 0 or "violence" in event_type or "airstrike" in event_type:
        return "high"
    elif "riot" in event_type or "protest" in event_type:
        return "medium"
    return "low"


def insert_events(events: list) -> int:
    conn = get_db()
    cursor = conn.cursor()
    added = 0
    fetched_at = datetime.now(timezone.utc).isoformat()

    for e in events:
        try:
            fatalities = int(e.get("fatalities", 0) or 0)
            severity = map_severity(e.get("event_type"), fatalities)
            cursor.execute("""
                INSERT OR REPLACE INTO conflict_events
                    (event_id, source, event_type, country, region,
                     latitude, longitude, timestamp, fetched_at, severity, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                e.get("event_id_cnty"),
                "ACLED",
                e.get("event_type"),
                e.get("country"),
                e.get("admin1"),
                float(e.get("latitude", 0)),
                float(e.get("longitude", 0)),
                e.get("event_date"),
                fetched_at,
                severity,
                e.get("notes"),
            ))
            if cursor.rowcount > 0:
                added += 1
        except Exception as ex:
            print(f"[DB] Insert error for event {e.get('event_id_cnty')}: {ex}")

    conn.commit()
    conn.close()
    return added


def log_fetch(source: str, events_added: int, status: str, error: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO fetch_log (fetched_at, source, events_added, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now(timezone.utc).isoformat(), source, events_added, status, error))
    conn.commit()
    conn.close()


def check_proximity(country: str) -> list:
    if USER_LAT is None or USER_LON is None:
        return []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, region, latitude, longitude, severity, description
        FROM conflict_events
        WHERE is_active = 1 AND country = ?
        ORDER BY timestamp DESC
        LIMIT 200
    """, (country,))
    rows = cursor.fetchall()
    conn.close()

    nearby = []
    for row in rows:
        event_type, region, lat, lon, severity, desc = row
        dist = haversine(USER_LAT, USER_LON, lat, lon)
        if dist <= PROXIMITY_RADIUS_KM:
            nearby.append({
                "event_type": event_type,
                "region": region,
                "distance_km": round(dist, 1),
                "severity": severity,
                "description": desc,
            })
    return nearby


def fire_notification(nearby_events: list):
    """Placeholder — replace with Streamlit toast or push notification."""
    print(f"\n⚠️  DANGER ALERT: {len(nearby_events)} active conflict event(s) near your location:")
    for e in nearby_events:
        print(f"  [{e['severity'].upper()}] {e['event_type']} in {e['region']} — {e['distance_km']} km away")


# --- MAIN LOOP ---

def run_updater(country: str):
    print(f"[Updater] Starting — polling ACLED every {POLL_INTERVAL // 60} min for: {country}")
    while True:
        print(f"\n[Updater] Fetching at {datetime.now().strftime('%H:%M:%S')}...")
        try:
            events = fetch_acled_events(country)
            if events:
                added = insert_events(events)
                log_fetch("ACLED", added, "success")
                print(f"[Updater] {added} new event(s) added.")
                nearby = check_proximity(country)
                if nearby:
                    fire_notification(nearby)
            else:
                log_fetch("ACLED", 0, "success")
                print("[Updater] No new events.")
        except Exception as e:
            log_fetch("ACLED", 0, "fail", str(e))
            print(f"[Updater] Error: {e}")

        time.sleep(POLL_INTERVAL)

# -------------------------------Place Holder for ReliefWeb Updater, Will Do After Approval --------------------
#
#
#
#
# -----------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    run_updater(country="Iran")