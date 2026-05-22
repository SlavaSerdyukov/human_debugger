# Human Debugger

Human Debugger is a privacy-first local web app for spotting repeated behavior patterns around focus, energy, stress, project friction, and stalled work. You add short daily entries and project logs; the app generates a deterministic debug report with hypotheses, signals, possible risks, and suggested patches.

All data is stored locally in SQLite.

## Important Note

This app is not medical advice. It is not a clinical service and does not make medical claims. Treat its output as lightweight personal telemetry, not as a verdict about you.

## Install

```bash
cd human-debugger
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If you use `uv`:

```bash
cd human-debugger
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Run

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

To load sample data, click **Load demo data** on the dashboard, open `http://127.0.0.1:8000/seed-demo`, or run:

```bash
curl -X POST http://127.0.0.1:8000/seed-demo
```

## Example Tags

Useful tags include:

- `deep-work`
- `stuck`
- `procrastination`
- `overwhelmed`
- `bored`
- `meeting-heavy`
- `context-switching`
- `planning`
- `shipping`

Tags are comma-separated.

## Debug Report

The report includes:

- 7-day and 30-day averages for mood, energy, focus, and stress
- rolling averages for recent focus, energy, stress, and mood signals
- trend labels: improving, declining, stable, or insufficient data
- correlations for sleep vs focus, stress vs focus, and energy vs project progress
- detected patterns such as sleep-focus coupling, focus slide, project drift, stress-delay loops, and architecture euphoria drop
- semantic memory summaries using local hash embeddings
- project abandonment risk from 0 to 100 based on stale logs, high friction, falling progress, low focus, low energy, and negative tags

The tone is friendly, direct, and lightly cyberpunk. The report uses wording like "possible", "signal", "pattern", and "hypothesis".

## Optional Ollama Layer

If Ollama is running locally at `http://localhost:11434`, the report page tries to polish the deterministic report with `llama3.1`. The app still works when Ollama is unavailable.

The LLM layer is only allowed to rephrase the deterministic report. It should not invent new facts.

Raw journal entries are not sent to the LLM layer. The pipeline is:

```text
entries -> deterministic analytics -> structured signals -> optional LLM summary
```

You can configure Ollama with environment variables:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1
export OLLAMA_TIMEOUT=30.0
```

Useful local checks:

```bash
ollama serve
ollama pull llama3.1
curl http://127.0.0.1:8000/api/llm-status
```

## Architecture

The app keeps the original routes and SQLite schema, but analytics and orchestration are split into smaller modules:

```text
app/
  analytics/
    metrics.py
    trends.py
    correlations.py
    patterns.py
    risk_engine.py
    report_builder.py
    semantic_memory.py
  llm/
    ollama_client.py
    prompts.py
    summarizer.py
  services/
    entry_service.py
    project_service.py
    analytics_service.py
```

## Endpoints

- `GET /` dashboard
- `GET /entries` entry history and entry form
- `POST /entries` create an entry
- `GET /projects` project list and project form
- `POST /projects` create a project
- `GET /projects/{id}` project detail and log form
- `POST /projects/{id}/logs` create a project log
- `GET /debug-report` HTML report
- `GET /api/debug-report` JSON report
- `GET /api/llm-status` Ollama availability and configured model status
- `GET /seed-demo` insert demo data if the database is empty, then redirect to the report
- `POST /seed-demo` same behavior for the dashboard button

## Tests

```bash
pytest
```

Coverage includes entry creation, project creation, metric averages, declining focus detection, silent project detection, abandonment risk scoring, empty data handling, and Ollama fallback.

## Roadmap

- export report as Markdown
- edit and delete entries
- project status update UI
- tag filters
- configurable risk thresholds
- local-only backup and restore
- richer charts without external tracking

## 👤 Author

**Slava Serdiukov**
Machine Learning / Backend Engineering Portfolio Project