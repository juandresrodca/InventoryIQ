# InventoryIQ — local demo

A Streamlit chat over a DuckDB mock lakehouse that mirrors the Fabric lakehouse
schema. Use this when you don't have an M365 tenant handy.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
streamlit run app.py
```

App opens at <http://localhost:8501>.

## Configure the LLM (optional but  recommended)

Without an LLM the app still works in **deterministic routing** mode — each
sidebar question maps to one grounding tool and you see real lakehouse rows.
But the conversational answer + multi-tool reasoning needs Azure OpenAI.

Create a `.env` from the repo root `.env.example` and set:

```
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

## What the agent grounds on :

All answers come from these typed tools (see `grounding.py`):

| Tool | Purpose |
|---|---|
| `kpi_summary` | Estate-wide health counters |
| `assets_by_alert_severity` | Open alerts by severity / building / floor / time window |
| `stale_assets_by_department` | Devices that stopped checking in |
| `assets_on_blueprint` | Spatial reasoning over floor plans |
| `unsupported_os_by_location` | Lifecycle planning |
| `warranty_expiring` | Procurement planning |
| `disk_failure_pattern` | Failure trends for procurement tickets |

Each tool returns rows **and** citations (`{table, row_id}`) so the answer is
always traceable — same contract the Fabric IQ semantic model exposes.

## Swap to Fabric IQ

Set in `.env`:

```
GROUNDING=fabric
FABRIC_WORKSPACE_ID=<guid>
FABRIC_LAKEHOUSE_ID=<guid>
```

`grounding.py` will then route the same functions through OneLake (planned —
see `../grounding/notebooks/01_ingest_inventorymapper.ipynb`).
