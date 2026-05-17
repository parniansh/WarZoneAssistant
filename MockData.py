import sqlite3
from datetime import datetime, timezone
from Config import DB_PATH

# Current timestamp
NOW = datetime.now(timezone.utc).isoformat()
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

MOCK_EVENTS = [
    {
        "event_id": "MOCK_IR_001",
        "source": "ACLED",
        "event_type": "Explosion/Remote violence",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7448,
        "longitude": 51.3753,
        "timestamp": TODAY,
        "severity": "critical",
        "description": "An explosion was reported near a military checkpoint north of Tehran. Several casualties reported. Roads leading north blocked by security forces.",
    },
    {
        "event_id": "MOCK_IR_002",
        "source": "ACLED",
        "event_type": "Battles",
        "country": "Iran",
        "region": "Alborz",
        "latitude": 35.9167,
        "longitude": 50.9833,
        "timestamp": TODAY,
        "severity": "critical",
        "description": "Armed clashes reported between security forces and armed groups on the highway between Tehran and Karaj. Road is currently impassable.",
    },
    {
        "event_id": "MOCK_IR_003",
        "source": "ACLED",
        "event_type": "Violence against civilians",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7219,
        "longitude": 51.4141,
        "timestamp": TODAY,
        "severity": "high",
        "description": "Unidentified gunmen opened fire in the Narmak district of eastern Tehran. Residents advised to stay indoors.",
    },
    {
        "event_id": "MOCK_IR_004",
        "source": "ACLED",
        "event_type": "Riots",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6944,
        "longitude": 51.4215,
        "timestamp": TODAY,
        "severity": "high",
        "description": "Large riots broke out in central Tehran near Azadi Square. Security forces deployed tear gas. Several streets blocked.",
    },
    {
        "event_id": "MOCK_IR_005",
        "source": "ACLED",
        "event_type": "Protests",
        "country": "Iran",
        "region": "Isfahan",
        "latitude": 32.6546,
        "longitude": 51.6680,
        "timestamp": TODAY,
        "severity": "medium",
        "description": "Large protests reported in Isfahan city center. Demonstrators blocking main roads. Situation tense but no violence reported yet.",
    },
    {
        "event_id": "MOCK_IR_006",
        "source": "ACLED",
        "event_type": "Explosion/Remote violence",
        "country": "Iran",
        "region": "Mazandaran",
        "latitude": 36.5659,
        "longitude": 53.0601,
        "timestamp": TODAY,
        "severity": "critical",
        "description": "IED explosion reported on the coastal road near Sari in Mazandaran province. Road closed. Casualties unknown.",
    },
    {
        "event_id": "MOCK_IR_007",
        "source": "ACLED",
        "event_type": "Strategic developments",
        "country": "Iran",
        "region": "Qom",
        "latitude": 34.6416,
        "longitude": 50.8746,
        "timestamp": TODAY,
        "severity": "medium",
        "description": "Security forces established new checkpoints on all roads entering and leaving Qom. Heavy military presence reported.",
    },
    {
        "event_id": "MOCK_IR_008",
        "source": "ACLED",
        "event_type": "Battles",
        "country": "Iran",
        "region": "Gilan",
        "latitude": 37.2808,
        "longitude": 49.5832,
        "timestamp": TODAY,
        "severity": "high",
        "description": "Armed clashes reported in Rasht, Gilan. Multiple neighborhoods under curfew. Civilians advised to avoid the area.",
    },
]


def insert_mock_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0

    for e in MOCK_EVENTS:
        cursor.execute("""
            INSERT OR REPLACE INTO conflict_events
                (event_id, source, event_type, country, region,
                 latitude, longitude, timestamp, fetched_at, severity, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            e["event_id"], e["source"], e["event_type"], e["country"], e["region"],
            e["latitude"], e["longitude"], e["timestamp"], NOW,
            e["severity"], e["description"],
        ))
        if cursor.rowcount > 0:
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} mock events into warzone.db")


if __name__ == "__main__":
    insert_mock_data()