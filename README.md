# InventoryIQ

> A Microsoft Foundry agent for IT asset & datacenter reasoning, grounded in **Foundry IQ** over a live Azure AI Search knowledge source.

Built for the [Microsoft Agents League Hackathon](https://innovationstudio.microsoft.com/hackathons/Agents-League-Hackathon) — Enterprise Agents track, June 4–14 2026.

## What it does

Ask your IT estate anything in natural language and get a grounded, cited answer:

- *"Which servers in Building B / Floor 2 raised critical alerts in the last 24 hours?"*
- *"Show laptops assigned to the Finance department that haven't checked in for 7 days."*
- *"Which assets on the DC-East blueprint are in the cold-aisle zone?"*
- *"Which Windows assets are running unsupported OS versions, grouped by location?"*
- *"Draft a procurement ticket for replacement drives based on this quarter's failure pattern."*

Every answer is grounded in **Microsoft Foundry IQ** over an Azure AI Search knowledge source mirrored from the [InventoryMapper](https://github.com/juandresrodca/InventoryMaper) .NET 10 asset platform, with citations back to the source row.

## Architecture

```
 ┌─────────────────────┐    EF Core / SQL Server
 │  InventoryMapper    │──────────────┐
 │  (.NET 10 API)      │              │
 └─────────────────────┘              ▼
                              ┌───────────────────┐
                              │  grounding/       │  ingestion script
                              │  scripts/         │  (Python)
                              └─────────┬─────────┘
                                        ▼
   ┌──────────────────────────────────────────────────────┐
   │  Azure AI Search index  inv-index                    │
   │   685 docs: asset + alert                            │
   │   1536-dim vector embeddings (text-embedding-3-small)│
   │   semantic ranking enabled                           │
   └─────────────────────────┬────────────────────────────┘
                             ▼
                   ┌───────────────────┐
                   │  Foundry IQ       │  knowledge source
                   │  inv-knowledge    │  registered in the
                   │  (semantic mode)  │  inventoryiq project
                   └─────────┬─────────┘
                             ▼
                   ┌───────────────────┐
                   │ Foundry Agent     │  asst_v8Ye8v2iTPsBXRXWjDny8pRj
                   │ "InventoryIQ"     │  gpt-4o + instructions + grounding
                   │ (Foundry Agents)  │
                   └───────────────────┘

  ▼ Local fallback for judges without an Azure tenant
   ┌──────────────────────────────┐
   │  demo/  (Streamlit + DuckDB) │
   │  same schema, same questions │
   │  pastel themed UI            │
   └──────────────────────────────┘
```

## Repo layout

| Folder | What's in it |
|---|---|
| `agent/` | Declarative-agent manifest (`manifest.json`) + system-prompt instructions + action plugin definition. Used as documentation of the deployed agent and as a Copilot Studio import target if a Teams surface is added later. |
| `grounding/scripts/` | `01_index_inventorymapper.py` — ingests asset + alert rows into Azure AI Search with embeddings. |
| `api/` | (Reserved) .NET worker for real InventoryMapper → Search ingestion in production. |
| `demo/` | **Local-runnable Streamlit chat over DuckDB.** What reviewers without an Azure tenant use. Same schema, same questions, same answers. |
| `docs/` | Foundry setup guide + demo video script. |

## Microsoft IQ integration

This project integrates **Foundry IQ** as required by the hackathon rules.

| Layer | Where it lives |
|---|---|
| **Reasoning model** | Azure AI Foundry project `inventoryiq` — `gpt-4o` deployment for chat, `text-embedding-3-small` for vectors |
| **Knowledge source** | Azure AI Search index `inv-index` registered as Foundry knowledge source `inv-knowledge` (semantic mode) |
| **Grounding binding** | Configured directly on the Foundry agent — every reply pulls grounded passages from `inv-knowledge` and cites them |
| **Deployed agent** | `InventoryIQ` (`asst_v8Ye8v2iTPsBXRXWjDny8pRj`) — Foundry-hosted, GA on the same Foundry project, testable in the built-in playground |
| **Action skill (planned)** | `agent/actions/draft_procurement_ticket.json` — turns a finding into a ticket draft |

> **Why Foundry IQ over Fabric IQ:** Fabric trial provisioning is currently gated for tenants created from Azure free signups (the trial dialog returned `BadRequest` for our region pair). Foundry IQ runs entirely inside Azure AI Foundry on the same Azure credit and provides the same grounding contract — a real RAG index with semantic ranking and source citations. The repo's grounding shape is identical either way, so a future Fabric IQ swap is a one-day addition.

## Quick start — local demo (no Azure needed)

> ⚡ **This local demo version does NOT require an Azure tenant, M365 subscription, or API keys.** It is the primary way for judges to verify functionality if an Azure environment is unavailable.

```powershell
cd demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py            # builds inv.duckdb with ~500 assets, 30 days of monitoring, ~185 alerts
streamlit run app.py
```

Opens at <http://localhost:8501>.

### Step-by-step demo testing

1. **Setup environment** — From `demo/`, install dependencies: `pip install -r requirements.txt`.
2. **Generate mock data** — Run `python seed.py`. Builds the local `inv.duckdb` populated with ~500 assets, 30 days of monitoring history, ~185 alerts.
3. **Run the dashboard** — `streamlit run app.py` launches the local chat interface.
4. **Submit a query** — Use the sidebar to click a sample question, or type a free-form one (e.g., *"Which servers in Building B raised critical alerts?"*).
5. **Observe grounding**:
   - Cyan **tool-call chips** show which grounding function was invoked.
   - The **data tables** show the rows the agent grounded on.
   - The **📎 citations** expander shows the lakehouse table + row IDs.
6. **(Optional) Real LLM mode** — Set `AZURE_OPENAI_*` in `.env` (see `.env.example`). With keys set, sidebar questions trigger real `gpt-4o` tool-calling with conversational synthesis instead of deterministic routing.
7. **Theme toggle** — Sidebar **Theme** button switches between dark and light pastel themes.

## Quick start — Foundry IQ deployment

1. **Provision** Azure AI Foundry project + Azure AI Search Free + Azure OpenAI (see [`docs/foundry_setup.md`](docs/foundry_setup.md)). Total cost during the hackathon: < $5 of Azure free credit.
2. **Configure** `.env` from `.env.example` with your endpoints and keys.
3. **Index the data**:
   ```powershell
   python grounding/scripts/01_index_inventorymapper.py --rebuild
   ```
   Reads from `demo/inv.duckdb` (or your real InventoryMapper SQL Server) and pushes ~685 documents into `inv-index` with embeddings via `text-embedding-3-small`.
4. **Register** `inv-index` as a Foundry knowledge source: in the Foundry project → **Agentes → Create new** → add Azure AI Search as a knowledge source → pick `inv-index` → name `inv-knowledge` → semantic search mode.
5. **Configure the agent** with the instructions in `agent/instructions.md` and bind the knowledge source.
6. **Test** in the Foundry Agents playground — see `docs/demo_script.md` for the suggested 3-minute demo flow.

## Status

| Track | Status |
|---|---|
| Local demo over DuckDB | ✅ working |
| Mock lakehouse + seed (685 rows: 500 assets, 185 alerts, 30 locations, 9 blueprints) | ✅ working |
| Grounding tools + citations (Streamlit demo) | ✅ working |
| Streamlit chat with real `gpt-4o` tool-calling | ✅ working |
| Pastel UI with dark + light theme toggle | ✅ working |
| Declarative agent manifest (Copilot Studio compatible) | ✅ drafted |
| Azure AI Search index `inv-index` | ✅ deployed (685 docs indexed) |
| Foundry IQ knowledge source `inv-knowledge` | ✅ connected (semantic mode) |
| Foundry-hosted agent `InventoryIQ` | ✅ deployed + validated in playground |
| Demo video | 🟡 in progress |
| README + repo polish + GitHub push | ✅ deployed |


## Disclaimer

Built for demo purposes only. No confidential data. Schema, hostnames, users, alerts in this repo are synthetic. See [hackathon disclaimer](https://aka.ms/AgentsLeague_Disclaimer).

## License

MIT — see `LICENSE`.
