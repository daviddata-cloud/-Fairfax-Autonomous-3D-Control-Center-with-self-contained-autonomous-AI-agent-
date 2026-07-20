# -Fairfax-Autonomous-3D-Control-Center-with-self-contained-autonomous-AI-agent-
An autonomous, offline AI agent that monitors telemetry, self-heals its own configuration, and drives a live 3D network dashboard — powered by a local Llama 3 model via Ollama. No cloud, no API keys, everything runs on your machine.
# 🌎 Fairfax Autonomous 3D Control Center

An autonomous, offline AI agent that monitors telemetry, self-heals its own configuration, and drives a live 3D network dashboard — powered by a **local Llama 3 model** via Ollama. No cloud, no API keys, everything runs on your machine.

---

## 📋 Description

This project is a self-contained **autonomous AI agent** built on two cooperating processes:

- **`weather_agent.py`** — the autonomous engine. It runs a continuous loop that ingests telemetry, asks a local Llama 3 model to reason about it, deterministically decides system state, rewrites its own production config file when the state drifts, keeps historical log backups, and watches an external file to dynamically re-theme the dashboard.
- **`server.py`** — a Flask web server hosting a real-time dashboard: a live streaming line chart, a status panel, and an interactive **3D network map of 6 Virginia locations** rendered with Three.js.

The agent is designed around one core safety principle: **the LLM reasons and narrates, but code makes every decision that matters.** Numeric thresholds, config generation, and color validation are all deterministic — the model never produces anything that gets executed or trusted blindly.

---

## 🌦️ Scenario: Intelligent Environmental Weather-Defense Agent

A great proof-of-concept extension: add a **real-time weather forecast tool** to the agent to make the demo more vivid and grounded in a real-world use case.

**Scenario setup**
The agent reads your local server config file (e.g. `server_config.py`) in real time while also calling a weather forecast API.

**Autonomous decision**
If extreme weather is detected locally (heavy rain, snowstorm, extreme heat, or typhoon), the agent autonomously judges that the server faces a **power-outage or cooling risk**, automatically edits the local code to switch on **"Energy-Saving / Backup Mode,"** and pushes the emergency state and the healed code to your local dashboard within seconds.

To keep the local small model (Llama) fast and stable, the codebase favors deterministic decisions in code and uses the LLM only for reasoning and summaries.

---

## ✨ Features

### Autonomous agent (`weather_agent.py`)
- **100% offline reasoning** using a local Llama 3 model (Ollama) — no external API calls.
- **Self-healing config loop** — detects state drift (NORMAL ⇄ CRITICAL) and automatically overwrites `server_config.py` with the correct settings.
- **Deterministic decision-making** — the CRITICAL/NORMAL threshold and the generated config are computed in code, not left to the LLM (prevents hallucinated states).
- **Model-disagreement detection** — logs a warning whenever Llama's suggested state differs from the code's authoritative decision.
- **Timestamped log backups** — every state transition is snapshotted to `telemetry_logs/`.
- **Robust JSON handling** — forces JSON output from Ollama and validates/parses it defensively.
- **Autonomous file watcher** — monitors `sensor_input.json` and re-themes the dashboard when it changes (see below).
- **(Optional) Weather-defense mode** — extend the loop with a live weather API to trigger energy-saving/backup mode on extreme forecasts.

### Live dashboard (`server.py`)
- **Interactive 3D network map** — 6 Virginia locations positioned geographically, each a temperature bar (height = temp, red > 85°F, teal otherwise), connected by a white/gray wireframe **net across the bar tops** that flexes with live data.
- **Auto-rotating + drag-to-rotate** 3D scene.
- **Live streaming line chart** — Fairfax temperature & wind over time.
- **Real-time status panel** — location, temperature, wind, condition, active config, and a CRITICAL/OPTIMAL badge.
- **Autonomous background theming** — background color updates on its own based on the watched file.

---

## 🧠 Core Logic

```
┌─────────────────────┐         ┌──────────────────────┐
│  weather_agent.py   │         │      server.py       │
│  (autonomous loop)  │         │   (Flask dashboard)  │
├─────────────────────┤         ├──────────────────────┤
│ 1. Read telemetry   │         │  /                   │  ← dashboard HTML
│ 2. Watch sensor file│──POST──▶│  /update-status      │  ← receives agent data
│ 3. Ask Llama (JSON) │         │  /api/history        │  ← line chart data
│ 4. Decide in CODE   │         │  /api/locations      │  ← 3D map data (6 cities)
│ 5. Heal config file │         │  /api/style          │  ← autonomous bg color
│ 6. Log + POST       │         └──────────────────────┘
└─────────────────────┘
```

**Decision flow each loop (~every 5s):**
1. Generate/ingest telemetry (temp, wind, condition).
2. Check `sensor_input.json` — if changed, ask Llama for a theme color, validate it, apply it.
3. Send telemetry to Llama for a reasoning summary (JSON output enforced).
4. **Code** decides `CRITICAL` if `temp > 85°F`, else `NORMAL` (model output is only used for the human-readable reason).
5. If state changed, overwrite `server_config.py` and save a timestamped backup log.
6. POST the frame to the dashboard.

---

## 🛠️ Installation
create p_agent folder 
### Prerequisites
- [Anaconda / Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- [Ollama](https://ollama.com/download) (for running Llama 3 locally)
 

### 1. Create the conda environment (Python 3.12)

```bash
conda create -n myenv312 python=3.12 -y
conda activate myenv312
```

### 2. Install Python dependencies

```bash
pip install flask requests langchain-ollama langchain-core
```

<details>
<summary>Full package list</summary>

| Package | Purpose |
|---|---|
| `flask` | Web server + dashboard |
| `requests` | Agent → server communication |
| `langchain-ollama` | Local Llama 3 chat interface |
| `langchain-core` | Prompt templating |

Chart.js and Three.js (r128) are loaded in the browser via CDN — no install needed.
</details>

### 3. (If you hit LangChain version errors) Upgrade the LangChain ecosystem

If you see dependency or version conflicts, upgrade everything to the LangChain **0.3.x** ecosystem so the latest tools co-exist cleanly:

```bash
pip install --upgrade "langchain>=0.3.0" "langchain-community>=0.3.0" "langchain-core>=0.3.0" langchain-ollama ollama
```

**Why this happens and what the fix does:** an older `langchain-community` (e.g. `0.2.6`) can act as a stubborn anchor that drags your install back to 2024-era versions. Upgrading everything to the `0.3.x` ecosystem clears those errors. You can safely ignore warnings about `pillow`, `gradio`, or `weaviate-client` — they do not affect the Flask + Ollama + LangChain scripts here.

### 4. Verify the environment

Create a file named `test_env.py`:

```python
import flask
import langchain_ollama
import requests
print("🎉 Success! Your Python environment is clean and ready for the 3D demo!")
```

Run it:

```bash
python test_env.py
```

If it prints the success message with no traceback, your environment is ready.

### 5. Install and start Ollama + pull Llama 3

```bash
# Start the Ollama service (leave running)
ollama serve

# In another terminal, pull the model
ollama pull llama3
```
<img width="1154" height="235" alt="image" src="https://github.com/user-attachments/assets/6f675d5e-4942-49d6-8822-64f7a17076ea" />


Verify the model is available and (optionally) test it interactively:

```bash
ollama list
ollama run llama3
```


---

## 🚀 How to Start

You need **three things running**: Ollama, the server, and the agent.

**Terminal 1 — Ollama** (if not already running as a service)

```bash
ollama serve
```

**Terminal 2 — Dashboard server**

```bash
conda activate myenv312
python server.py
```
<img width="1444" height="156" alt="image" src="https://github.com/user-attachments/assets/f8789857-cc32-4b52-b176-90c11b12b29d" />



**Terminal 3 — Autonomous agent**

```bash
conda activate myenv312
python weather_agent.py
```
<img width="1300" height="283" alt="image" src="https://github.com/user-attachments/assets/1e66dd36-1381-407c-b90c-0812e71e8ed3" />


Then open your browser to:

```
http://127.0.0.1:5000
```
<img width="1897" height="677" alt="image" src="https://github.com/user-attachments/assets/34d18e0a-1b7f-4393-b094-28390adcedc0" />



Within a few seconds the dashboard begins updating and the agent terminal prints `📡 [Web Server Ingest]` frames.

---

## 🛑 How to Stop

Stop the agent and server by pressing **`Ctrl + C`** in each of their terminals.

```bash
# In Terminal 2 and Terminal 3
Ctrl + C
```

To stop Ollama, press `Ctrl + C` in its terminal (or stop the Ollama background service).

To deactivate the environment:

```bash
conda deactivate
```

> **⚠️ Important:** `server.py` bakes its HTML in when it starts. After editing `server.py`, you **must fully stop it (`Ctrl+C`) and restart it** — a browser refresh alone will keep serving the old page. Hard-refresh the browser with `Ctrl+F5` afterward.

---

## 📂 `sensor_input.json` — Autonomous Theming

This file is the agent's external trigger. The agent **watches it automatically** and re-themes the dashboard whenever it changes — no restart required.

### How it works
1. Create the file in the project folder:
   ```json
   {"status": "normal", "note": "all systems calm"}
   ```
2. The agent polls the file's modification time every loop. On startup it records the file but does **not** fire (this avoids a false trigger).
3. When you **edit and save** the file, the agent detects the change, sends the contents to Llama, and asks for an appropriate **dark, readable background color**.
4. The returned color is **validated against a strict hex pattern** (`#RRGGBB`) before being applied — invalid output is rejected, never used.
5. The dashboard background updates live (polled every 2 seconds).

### Try it
Edit `sensor_input.json` and save:

```json
{"status": "critical", "note": "excessive heat alarm, grid overload"}
```

Within ~5 seconds the agent logs `📂 [File Watch]` and the background shifts to a **dark red** theme.
<img width="713" height="53" alt="image" src="https://github.com/user-attachments/assets/692b47d3-60bb-4ae2-a70e-be58abb625bf" />
<img width="427" height="258" alt="image" src="https://github.com/user-attachments/assets/0c1885b9-813f-4909-b56f-a73b72d5d627" />

Change it back to calm wording and the theme drifts back to a **cool blue/teal**.

> The model only ever produces a **value** (a color) that the code validates — it never generates or runs a script. This keeps the autonomous behavior safe.

---

## 📁 Project Structure

```
p_agent/
├── server.py              # Flask dashboard (3D map, chart, status, theming)
├── weather_agent.py       # Autonomous AI agent loop
├── server_config.py       # Auto-generated & overwritten by the agent (self-healing target)
├── sensor_input.json      # Watched file → autonomous background theming
├── test_env.py            # Quick environment sanity check
└── telemetry_logs/        # Timestamped config-healing backups (auto-created)
```

---

## 🔧 Configuration Notes

| Setting | Location | Default |
|---|---|---|
| Llama model | `weather_agent.py` → `ChatOllama(model=...)` | `llama3` |
| Ollama URL | `weather_agent.py` → `base_url` | `http://127.0.0.1:11434` |
| Server URL | `weather_agent.py` → `SERVER_URL` | `http://127.0.0.1:5000/update-status` |
| Watched file | `weather_agent.py` → `WATCH_FILE` | `sensor_input.json` |
| Loop interval | `weather_agent.py` → `time.sleep(5)` | 5 seconds |
| CRITICAL threshold | `weather_agent.py` → `build_config` / mode logic | `temp > 85°F` |

---

## 🩺 Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Blank page at `:5000` | `server.py` not running — start it in its own terminal. |
| Dashboard stuck on "Waiting for Agent heartbeat pulse..." | Agent can't reach the server — confirm `SERVER_URL` and that `server.py` is up. |
| `Could not find any JSON token blocks` | Ollama not returning JSON — ensure `format="json"` is set and `ollama serve` is running. |
| LangChain import / version errors | Run the `0.3.x` upgrade command in Installation step 3, then rerun `test_env.py`. |
| Chart / 3D not visible | Old server process — **restart `server.py`**, then `Ctrl+F5`. |
| Background never changes | Old server process (missing `/api/style`) — restart `server.py`. |
| Model picks wrong state | Fixed by design — code decides the threshold; watch for `⚠️ Model Disagreement` logs. |

---

## 📜 License

MIT — free to use, modify, and distribute.
