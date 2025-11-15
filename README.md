
# Multi-Agent Academic Paper Assistant

This ![generated-image](https://github.com/user-attachments/assets/52f7f2c2-cf00-45b5-83bb-69e765650d4b)
workspace contains a Jupyter notebook `agent.ipynb` and a runnable script `agent_app.py` that demonstrate a multi-agent system for academic paper drafting: Research -> Writer -> Editor -> Plagiarism estimation.

Files
- `agent.ipynb`: The notebook implementing agents and workflow (demo). Depending on your environment, executing the notebook programmatically may fail if the notebook JSON contains formatting issues; use `agent_app.py` for a reliable run.
- `agent_app.py`: Standalone Python runner that executes the same workflow and saves session output in `sessions/`.
- `requirements.txt`: Python packages required.

Quick start (PowerShell)
1. (Optional) Create a virtual environment and activate it:

```
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```
2. Install dependencies:

```
python -m pip install -r requirements.txt
```
3. (Optional) Set your API key environment variable to use Google Gemini (`google.generativeai`) for improved drafts. Example:

```
$env:GEMINI_API_KEY = 'YOUR_KEY_HERE'
```
4. Run the canonical script (recommended):

```
# Multi-Agent Academic Paper Assistant

This repository demonstrates a simple multi-agent pipeline to help generate academic-style drafts from a paper title. It is intended as an educational capstone example (Research → Writer → Editor → Plagiarism).

Files of interest
- `agent.ipynb` — Notebook implementation (demo). May require a notebook UI to inspect cell outputs.
- `agent.executed.ipynb` — Executed copy of the notebook (saved after running here).
- `agent_app.py` — Canonical, standalone runner that executes the full workflow and saves session outputs to `sessions/`.
- `app.py` — Minimal Flask web UI (submit title, background-run workflow, live logs, result page).
- `requirements.txt` — Python dependencies.

Quick start (Windows PowerShell)
1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. (Optional) If you have a Google Gemini API key and want the WriterAgent to use it, set the env var before running:

```powershell
$env:GEMINI_API_KEY = 'YOUR_KEY_HERE'
```

Run the canonical script

```powershell
python agent_app.py
```

This will run the Research→Writer→Editor→Plagiarism pipeline and write a JSON session file into the `sessions/` directory (e.g., `sessions/example_session.json`).

Run the web UI (optional)

```powershell
python app.py
```

Open http://127.0.0.1:5000/ in your browser, submit a paper title, watch live logs on the status page, and view results when complete.

Notes
- `agent_app.py` is the most reliable way to run the workflow programmatically.
- The notebook (`agent.ipynb`) is available for exploration and teaching; `agent.executed.ipynb` is an executed output produced during development.
- The plagiarism check is a simple heuristic (difflib-based) comparing the draft to retrieved abstracts. For production, replace this with embedding + nearest-neighbor search (e.g., `sentence-transformers` + FAISS) or a dedicated plagiarism API.

Where outputs are saved
- Sessions and logs: `sessions/<session_id>.json` and `sessions/<session_id>.log`.
<img width="3750" height="2250" alt="workflow" src="https://github.com/user-attachments/assets/c52f23bb-4d68-446c-8183-0369f7b45b11" />

Next recommended improvements
- Add vector memory and semantic plagiarism (embeddings + FAISS).
- Support background jobs with status API (already basic support in `app.py`).
- Add Dockerfile for easy deployment.

If you want, I can add a `Dockerfile` and a one-line start script, or implement semantic plagiarism next. Open an issue or request a feature and I will implement it.
