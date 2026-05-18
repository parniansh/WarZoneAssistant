import subprocess
import time
import requests
import streamlit as st

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e2b"

def _ollama_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

@st.cache_resource
def ensure_ollama():
    """Start Ollama if not already running. Runs once per app session."""
    if _ollama_running():
        return {"status": "already_running"}

    # Launch ollama serve as a background process
    proc = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 15s for it to come up
    for _ in range(15):
        time.sleep(1)
        if _ollama_running():
            return {"status": "started", "pid": proc.pid}

    raise RuntimeError("Ollama failed to start within 15 seconds.")