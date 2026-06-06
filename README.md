**CONFLICT ZONE ASSISTANT**

AI-Powered Civilian Survival Assistant
Powered by Gemma 4 (fully offline) | Google Hackathon Submission

**Project Overview**

conflict zone Assistant is an offline-first AI application designed to help civilians survive and navigate active conflict zones. It runs entirely on-device using Google's Gemma 4 language model via Ollama, requiring no internet connection for its core functionality.
The application addresses three critical survival needs that civilians face in conflict zones: immediate medical response, situational safety awareness, and finding essential resources like water, food, and shelter.

**Problem Statement**

Civilians caught in conflict zones face life-threatening situations with limited access to information, communication, and professional assistance. Key challenges include:
• No reliable internet or communication infrastructure in active conflict areas
• Language barriers: affected civilians may not speak the dominant language of aid organizations
• No real-time awareness of nearby threats, safe routes, or available resources
• No immediate medical guidance when professional help is unavailable
• Psychological trauma and panic that impairs decision-making

**Solution**

conflict zone Assistant is a mobile-accessible web application that provides AI-driven, language-agnostic survival guidance. It operates in three functional modes:
Mode 1: First Aid
Provides immediate, step-by-step first aid protocols following WHO Emergency Care and TCCC (Tactical Combat Casualty Care) guidelines. Covers trauma injuries, environmental emergencies, chemical/blast exposure, and psychological first aid. Gemma 4's extensive medical training knowledge is used directly and no pre-loaded data required.
Mode 2: Safe Place Finding
Aggregates real-time conflict event data from ACLED (Armed Conflict Location & Event Data) API and displays it on an interactive map. The system polls for updates every 10 minutes when online, stores data in a local SQLite database, and provides proximity-based danger alerts when conflict events are detected near the user's location.
Mode 3: Resource Finding
Helps users locate critical resources including hospitals, pharmacies, water distribution points, emergency shelters, field hospitals, and food aid distribution. Combines permanent location data from OpenStreetMap with dynamic conflict time resource data from ReliefWeb's humanitarian API.

**Key Features**

Offline-First Architecture
The core AI model (Gemma 4) runs entirely offline via Ollama. All data is cached in a local SQLite database. The app functions without internet and connectivity only needed for data updates.
Multilingual Support
Gemma 4's multilingual capabilities allow the app to detect the user's language automatically and respond in the same language. Conflict and resource data in English is translated inline. No configuration required.
Geometric Path Conflict Detection
A novel feature that uses computational geometry to detect conflict events along the route between the user and a target resource and not just nearby. The perpendicular distance from each conflict point to the user-to-resource line segment is calculated, warning users if their route passes through danger zones.
Real-Time Conflict Intelligence
Integrates with ACLED API for conflict event data, classified by severity (critical, high, medium, low) and displayed on an interactive Folium map with color-coded markers. Proximity alerts fire immediately when new events are detected near the user.
Voice Input
Web Speech API integration allows users to speak queries in any language, critical in high-stress situations where typing is difficult or impossible.
Context-Aware AI Responses
Every Gemma query is enriched with relevant conflict events and resource locations from the local database, giving the model real situational context to provide actionable advice rather than generic guidance.

**Technical Architecture**

Stack

AI Model Gemma 4 (gemma4:e2b) via Ollama
Backend Python 3.x
Frontend Streamlit (mobile-accessible via WiFi)
Database SQLite (OS-agnostic, runs on Android via Termux)
Maps Folium + streamlit-folium
Conflict Data ACLED API (OAuth token-based)
Resource Data ReliefWeb API + OpenStreetMap
Voice Input Web Speech API (browser-native)

File Structure

Config.py — credentials, paths, model config (.env based)
DatabaseSchema.py — SQLite schema (conflict_events, static_resources, dynamic_resources, fetch_log)
Updater.py — background ACLED polling every 10 minutes + proximity alerts
Gemma.py — Gemma 4 integration, context injection, query handling
PathConflict.py — geometric path conflict detection
SystemPrompt.txt — unified system prompt for all three modes
app.py — Streamlit UI (chat + map + voice)
MockData.py — test conflict events with path conflict scenarios
MockResources.py — test static and dynamic resource locations

Gemma 4 Integration

Gemma 4 is served locally via Ollama and called through its REST API. Each query includes:
• A unified system prompt covering all three modes
• Injected conflict events sorted by proximity to the user
• Injected resource locations (permanent + conflict time) sorted by proximity
• Path conflict warnings computed geometrically before sending to the model
• User query in any language

The model responds in the user's language, translating injected English data inline. Thinking mode is disabled for faster response times.

Data Sources

ACLED Armed Conflict Location & Event Data — real-time conflict events with lat/lon, event type, severity, fatality counts
ReliefWeb UN OCHA humanitarian platform — wartime aid distribution points, field hospitals, emergency shelters
OpenStreetMap Permanent location data — hospitals, pharmacies, water points, supermarkets
Gemma 4 WHO/TCCC first aid protocols, general survival knowledge, multilingual response

Path Conflict Detection — Technical Detail

One of the novel contributions of this project is geometric path conflict detection. Standard proximity searches only detect danger near the user's current location. This system detects danger along the user's intended route.
For each resource location, the system computes the minimum perpendicular distance from every active conflict event to the line segment between the user's coordinates and the resource coordinates. If any conflict falls within a configurable threshold (default 0.5 km), a path warning is generated and injected into the Gemma context.
This means Gemma can reason about statements like: 'The field hospital is 2 km south but your route passes through an active battle zone 0.3 km from the path and seek an alternative route.'

Offline Behavior

The application handles three connectivity states gracefully:
GPS + Internet Full functionality: closest events and resources, real-time data, no warnings
GPS + No Internet Local db data with 'last updated' timestamp warning, path conflict detection still works
No GPS + Internet Country-wide highest severity events, 'location unavailable' warning shown to user

Why This Matters
According to UNHCR, over 120 million people were forcibly displaced in 2024. The majority of civilian casualties in conflict zones occur not from direct violence but from lack of access to medical care, clean water, and safe shelter. conflict zone Assistant directly addresses this gap by putting AI-powered survival guidance in the hands of anyone with a smartphone, no internet, no language barriers, no technical knowledge required.
By combining Gemma 4's frontier AI capabilities with real-time humanitarian data and novel geometric safety analysis, this project demonstrates that on-device AI can have immediate, measurable humanitarian impact.
