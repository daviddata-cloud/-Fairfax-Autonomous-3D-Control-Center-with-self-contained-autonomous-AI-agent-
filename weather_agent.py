import os
import json
import time
import re
import threading
import requests
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

# 1. Instantiate local offline Llama configuration
#    format="json" forces Ollama to emit valid JSON so parsing doesn't fail.
llm = ChatOllama(
    model="llama3",
    temperature=0.1,
    base_url="http://127.0.0.1:11434",
    format="json",
)

CURRENT_STATE = "UNKNOWN"
LOG_DIR = "telemetry_logs"
LOOP_COUNT = 0

# Server endpoint the dashboard listens on
SERVER_URL = "http://127.0.0.1:5000/update-status"

# --- File-watch config (autonomous background-color feature) ---
WATCH_FILE = "sensor_input.json"     # the file the agent watches
_last_watch_content = None           # tracks last-seen file CONTENT (solid on all OSes)
HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

# Deterministic theme palette — code decides the color, not the model.
THEME_CRITICAL = "#2a0d0d"   # dark red
THEME_NORMAL   = "#0b1f2a"   # dark blue / teal
THEME_DEFAULT  = "#0b0f19"   # baseline dark

CRITICAL_WORDS = ("critical", "alarm", "alert", "hot", "heat", "overload",
                  "emergency", "fire", "storm", "danger", "warning", "fault")
NORMAL_WORDS   = ("normal", "calm", "ok", "okay", "safe", "clear",
                  "cool", "fine", "stable", "baseline")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def classify_theme(content: str) -> str:
    """Map file content to a guaranteed-valid dark hex color, deterministically."""
    text = content.lower()
    if any(w in text for w in CRITICAL_WORDS):
        return THEME_CRITICAL
    if any(w in text for w in NORMAL_WORDS):
        return THEME_NORMAL
    return THEME_DEFAULT

def get_automated_demo_weather():
    """Autonomous weather scenario generator matrix loop."""
    global LOOP_COUNT
    LOOP_COUNT += 1

    if (LOOP_COUNT // 3) % 2 == 1:
        print(f"\n📈 [Scenario Trigger] Step {LOOP_COUNT}: Automating CRITICAL HEATWAVE Scenario.")
        return {"temp": 96, "wind": 24, "text": "Excessive Heat Warning - Grid Load Warning"}
    else:
        print(f"\n📉 [Scenario Trigger] Step {LOOP_COUNT}: Automating SAFE BASELINE Scenario.")
        return {"temp": 72, "wind": 4, "text": "Clear Skies - Perfect Ambient Temp"}

prompt_template = """
You are a self-healing engineering agent working in Fairfax, VA.
Review environmental variables and output updated infrastructure settings if criteria are met.

[LIVE TELEMETRY]
Ambient Temp: {temp} °F
Wind Velocity: {wind} mph
Observation: {text}

[CRITERIA REQUIREMENTS]
- IF temp > 85°F: Trigger CRITICAL state. Output parameters: AIR_INTAKE = 'INTERNAL_RECIRCULATION' and MAX_THREADS = 8.
- IF temp <= 85°F: Revert to NORMAL state. Output parameters: AIR_INTAKE = 'EXTERNAL_FRESH_AIR' and MAX_THREADS = 64.

Output a single raw JSON structure matching this exact pattern. Do not include markdown wraps or conversational notes:
{{
    "mode": "CRITICAL" or "NORMAL",
    "reason": "One-line technical summary statement.",
    "fixed_code": "The full python assignment lines that must occupy 'server_config.py'."
}}
"""

def extract_and_parse_json(raw_text: str) -> dict:
    """Regex block extractor to handle output formatting variances safely."""
    if not raw_text or not raw_text.strip():
        raise ValueError("Model returned empty output.")

    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found. Raw output was: {raw_text[:200]!r}")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Found braces but JSON was invalid: {e}. Snippet: {match.group(0)[:200]!r}")

def build_config(mode: str) -> str:
    """Deterministic config generation — never trust the model for the actual state."""
    if mode == "CRITICAL":
        return "AIR_INTAKE = 'INTERNAL_RECIRCULATION'\nMAX_THREADS = 8"
    return "AIR_INTAKE = 'EXTERNAL_FRESH_AIR'\nMAX_THREADS = 64"

def check_watched_file():
    """If WATCH_FILE content changed, map it to a validated dark color and push it.

    Detection is CONTENT-based (not mtime) so it never misses a save, and the
    color is chosen deterministically so it always applies — no model flakiness.
    """
    global _last_watch_content

    if not os.path.exists(WATCH_FILE):
        return

    with open(WATCH_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # First time we see the file, just record it — don't fire on startup
    if _last_watch_content is None:
        _last_watch_content = content
        return
    if content == _last_watch_content:
        return  # genuinely unchanged

    _last_watch_content = content
    print(f"\n📂 [File Watch] '{WATCH_FILE}' changed.")

    color = classify_theme(content)

    # Safety net: guarantee we only ever send a valid hex
    if not HEX_RE.match(color):
        color = THEME_DEFAULT

    print(f"🎨 [File Watch] Applying background {color} (content: {content[:60]!r})")
    requests.post(SERVER_URL, json={"bg_color": color}, timeout=3)

def start_file_watcher_thread():
    """Run the file watcher in its OWN thread so theming responds within ~1.5s,
    completely independent of how slow the Llama telemetry loop is."""
    def _loop():
        print(f"👀 [File Watch] Thread started — polling '{WATCH_FILE}' every 1.5s")
        while True:
            try:
                check_watched_file()
            except Exception as e:
                print(f"⚠️ [File Watch] Handled error: {e}")
            time.sleep(1.5)
    threading.Thread(target=_loop, daemon=True).start()

def start_autonomous_engine():
    global CURRENT_STATE
    print(f"🤖 [Engine Init] 100% Autonomous loop engaged. Syncing logs into './{LOG_DIR}/'")

    while True:
        try:
            weather = get_automated_demo_weather()

            # Deterministic ground truth — do NOT let the model decide the threshold
            authoritative_mode = "CRITICAL" if weather["temp"] > 85 else "NORMAL"

            prompt = PromptTemplate.from_template(prompt_template)
            chain = prompt | llm

            print("🤖 Llama processing telemetry inputs...")
            response = chain.invoke({"temp": weather["temp"], "wind": weather["wind"], "text": weather["text"]})

            # Debug: uncomment to inspect exactly what the model returns
            # print("----- RAW MODEL OUTPUT -----")
            # print(repr(response.content))
            # print("----------------------------")

            result = extract_and_parse_json(response.content)

            # Trust code, not the model, for the actual state decision
            inferred_mode = authoritative_mode
            reason = result.get("reason", "Baseline operation profiles confirmed.")

            model_said = result.get("mode", "NORMAL")
            if model_said != authoritative_mode:
                print(f"⚠️ [Model Disagreement] Model claimed '{model_said}' but temp={weather['temp']}°F → forcing '{authoritative_mode}'")

            # Deterministic config generation (matches the authoritative mode)
            fixed_code = build_config(authoritative_mode)

            # --- AUTONOMOUS DRIFT AND SELF-HEALING ENFORCEMENT ---
            if inferred_mode != CURRENT_STATE:
                print(f"🚨 [STATE DRIFT INGESTED] Transitioning state: '{CURRENT_STATE}' -> '{inferred_mode}'")
                print(f"💡 Reason: {reason}")

                print("💾 Overwriting active production target file 'server_config.py'...")
                with open("server_config.py", "w", encoding="utf-8") as f:
                    f.write(fixed_code)

                timestamp_id = time.strftime("%Y%m%d_%H%M%S")
                log_filename = f"{LOG_DIR}/healed_config_{timestamp_id}_{inferred_mode}.py"
                print(f"📁 Creating historical log backup file on disk: {log_filename}")
                with open(log_filename, "w", encoding="utf-8") as f:
                    f.write(f"# Snapshot Logged: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Agent Self-Healing Reason: {reason}\n")
                    f.write(fixed_code)

                CURRENT_STATE = inferred_mode
            else:
                print(f"✅ [System In Alignment] State matches active baseline ({CURRENT_STATE}). No file write required.")

            # Push cleaned network payload frame straight to local server
            requests.post(SERVER_URL, json={
                "is_alert": (CURRENT_STATE == "CRITICAL"),
                "location": "Fairfax, VA (Autonomous Stream Engine)",
                "temperature": int(weather["temp"]),
                "wind_speed": int(weather["wind"]),
                "condition": str(weather["text"]),
                "current_code": str(fixed_code)
            }, timeout=3)

        except Exception as error:
            print(f"⚠️ Custom Engine Handled Exception: {error}")

        print("⏳ Sleeping for 5 seconds before checking next telemetry state...")
        time.sleep(5)

if __name__ == "__main__":
    start_file_watcher_thread()   # runs independently of the slow LLM loop
    start_autonomous_engine()