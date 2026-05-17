import sqlite3
from datetime import datetime, timezone
from Config import DB_PATH

NOW = datetime.now(timezone.utc).isoformat()
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# --- STATIC RESOURCES (OSM permanent locations) ---
STATIC_RESOURCES = [
    {
        "osm_id": "OSM_IR_H001",
        "resource_type": "hospital",
        "name": "Imam Khomeini Hospital",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6944,
        "longitude": 51.3319,
        "address": "Keshavarz Blvd, Tehran",
        "phone": "+98 21 6658 0000",
    },
    {
        "osm_id": "OSM_IR_H002",
        "resource_type": "hospital",
        "name": "Milad Hospital",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7461,
        "longitude": 51.3728,
        "address": "Hemmat Expressway, Tehran",
        "phone": "+98 21 8160 0000",
    },
    {
        "osm_id": "OSM_IR_H003",
        "resource_type": "hospital",
        "name": "Loghman Hakim Hospital",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6576,
        "longitude": 51.3882,
        "address": "South Karegar St, Tehran",
        "phone": "+98 21 5541 5000",
    },
    {
        "osm_id": "OSM_IR_P001",
        "resource_type": "pharmacy",
        "name": "Central Pharmacy Tehran",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6892,
        "longitude": 51.3890,
        "address": "Valiasr St, Tehran",
        "phone": None,
    },
    {
        "osm_id": "OSM_IR_W001",
        "resource_type": "water_point",
        "name": "Laleh Park Water Station",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7061,
        "longitude": 51.4018,
        "address": "Laleh Park, Tehran",
        "phone": None,
    },
    {
        "osm_id": "OSM_IR_W002",
        "resource_type": "water_point",
        "name": "Mellat Park Water Station",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7598,
        "longitude": 51.4132,
        "address": "Mellat Park, Tehran",
        "phone": None,
    },
    {
        "osm_id": "OSM_IR_S001",
        "resource_type": "supermarket",
        "name": "Hyperstar Tehran",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7219,
        "longitude": 51.3764,
        "address": "Chamran Expressway, Tehran",
        "phone": None,
    },
    {
        "osm_id": "OSM_IR_H004",
        "resource_type": "hospital",
        "name": "Karaj Central Hospital",
        "country": "Iran",
        "region": "Alborz",
        "latitude": 35.8356,
        "longitude": 50.9988,
        "address": "Karaj, Alborz Province",
        "phone": "+98 26 3444 0000",
    },
]

# --- DYNAMIC RESOURCES (ReliefWeb wartime temporary locations) ---
DYNAMIC_RESOURCES = [
    {
        "resource_id": "RW_IR_001",
        "source": "ReliefWeb",
        "resource_type": "field_hospital",
        "name": "ICRC Emergency Field Hospital - Tehran North",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7601,
        "longitude": 51.3456,
        "description": "ICRC field hospital set up to handle trauma cases. Capacity 50 beds. Open 24/7. Accepts all civilians regardless of affiliation.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_002",
        "source": "ReliefWeb",
        "resource_type": "aid_distribution",
        "name": "WFP Food Distribution Point - Azadi Square",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6997,
        "longitude": 51.3375,
        "description": "WFP distributing emergency food rations. Distribution hours: 8AM-4PM daily. Bring ID if available but not required.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_003",
        "source": "ReliefWeb",
        "resource_type": "emergency_shelter",
        "name": "Emergency Shelter - Tehran University Campus",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.7008,
        "longitude": 51.3929,
        "description": "University campus converted to emergency shelter. Capacity 2000 civilians. UNHCR supervised. Water and basic food provided.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_004",
        "source": "ReliefWeb",
        "resource_type": "water_distribution",
        "name": "UNICEF Water Distribution - Karaj",
        "country": "Iran",
        "region": "Alborz",
        "latitude": 35.8401,
        "longitude": 50.9701,
        "description": "UNICEF water trucking point. Safe drinking water available. Hours: 7AM-7PM. Bring containers.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_005",
        "source": "ReliefWeb",
        "resource_type": "medical_supplies",
        "name": "MSF Medical Supply Point - Southern Tehran",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6512,
        "longitude": 51.4201,
        "description": "Médecins Sans Frontières distributing first aid kits, bandages, and basic medications. Open to all civilians.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_006",
        "source": "ReliefWeb",
        "resource_type": "emergency_shelter",
        "name": "Emergency Shelter - Imam Khomeini Mosque",
        "country": "Iran",
        "region": "Tehran",
        "latitude": 35.6731,
        "longitude": 51.4215,
        "description": "Mosque converted to emergency shelter. Capacity 500 civilians. Food and water available. All welcome.",
        "valid_from": TODAY,
        "valid_until": None,
    },
    {
        "resource_id": "RW_IR_007",
        "source": "ReliefWeb",
        "resource_type": "aid_distribution",
        "name": "Red Crescent Aid Distribution - Isfahan",
        "country": "Iran",
        "region": "Isfahan",
        "latitude": 32.6601,
        "longitude": 51.6674,
        "description": "Iranian Red Crescent distributing blankets, food, and hygiene kits. Open 9AM-5PM.",
        "valid_from": TODAY,
        "valid_until": None,
    },
]


def insert_mock_resources():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    static_added = 0
    for r in STATIC_RESOURCES:
        cursor.execute("""
            INSERT OR IGNORE INTO static_resources
                (osm_id, resource_type, name, country, region,
                 latitude, longitude, address, phone, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["osm_id"], r["resource_type"], r["name"], r["country"], r["region"],
            r["latitude"], r["longitude"], r["address"], r["phone"], NOW,
        ))
        if cursor.rowcount > 0:
            static_added += 1

    dynamic_added = 0
    for r in DYNAMIC_RESOURCES:
        cursor.execute("""
            INSERT OR IGNORE INTO dynamic_resources
                (resource_id, source, resource_type, name, country, region,
                 latitude, longitude, description, valid_from, valid_until, fetched_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            r["resource_id"], r["source"], r["resource_type"], r["name"],
            r["country"], r["region"], r["latitude"], r["longitude"],
            r["description"], r["valid_from"], r["valid_until"], NOW,
        ))
        if cursor.rowcount > 0:
            dynamic_added += 1

    conn.commit()
    conn.close()
    print(f"Inserted {static_added} static resources and {dynamic_added} dynamic resources into warzone.db")


if __name__ == "__main__":
    insert_mock_resources()