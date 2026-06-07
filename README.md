# InventoryIQ

> A Microsoft 365 Copilot agent for IT asset & datacenter reasoning, grounded in **Foundry IQ**.

Built for the [Microsoft Agents League Hackathon](https://innovationstudio.microsoft.com/hackathons/Agents-League-Hackathon) — Enterprise Agents track, June 4–14 2026.

## What it does

Ask your IT estate anything from Teams, Outlook, or Microsoft 365 Chat:

- *"Which servers in Building B / Floor 2 raised critical alerts in the last 24 hours?"*
- *"Show laptops assigned to the Finance department that haven't checked in for 7 days."*
- *"Which assets on the DC-East blueprint are in the cold-aisle zone?"*
- *"Which Windows assets are running unsupported OS versions, grouped by location?"*
- *"Draft a procurement ticket for replacement drives based on this quarter's failure pattern."*

Every answer is grounded in **Microsoft Foundry IQ** over an Azure AI Search knowledge source mirrored from the [InventoryMapper](https://github.com/juandresrodca) .NET 10 asset platform, with citations back to the source row.

## Architecture

```
 ┌─────────────────────┐    EF Core / SQL Server
 │  InventoryMapper    │──────────────┐
 │  (.NET 10 API)      │              │
 └─────────────────────┘              ▼
                              ┌───────────────────┐
                              │  api/Ingest       │  (scheduled push)
                              │  .NET worker      │
                              └─────────┬─────────┘
                                        ▼
   ┌──────────────────────────────────────────────────────┐
   │  Azure AI Search index  (inv-index)                  │
   │   assets / locations / blueprints /                  │
   │   monitoring_records / alerts                        │
   │   + vector embeddings for hybrid retrieval           │
   └─────────────────────────┬────────────────────────────┘
                             ▼
                   ┌───────────────────┐
                   │  Foundry IQ       │  knowledge source
                   │  (Azure AI        │  registered in the
                   │   Foundry project)│  inventoryiq project
                   └─────────┬─────────┘
                             ▼
                   ┌───────────────────┐
                   │  M365 Copilot     │  declarative agent
                   │  declarative      │  (Teams / Outlook / M365 Chat)
                   │  agent            │
                   └───────────────────┘

  ▼ Local fallback for judges without an Azure tenant
   ┌──────────────────────────────┐
   │  demo/  (Streamlit + DuckDB) │
   │  same schema, same questions │
   └──────────────────────────────┘
```

## Repo layout

| Folder | What's in it |
|---|---|
| `agent/` | Microsoft 365 Copilot declarative agent — `manifest.json`, `instructions.md`, action plugins |
| `grounding/` | Foundry IQ side — ingestion script, index schema, Foundry project config |
| `api/` | .NET worker that mirrors InventoryMapper → Azure AI Search |
| `demo/` | **Local-runnable Streamlit chat over DuckDB.** What reviewers without an Azure tenant use. |
| `docs/` | Architecture diagrams, demo script, Foundry setup checklist |

## Microsoft IQ integration

This project integrates **Foundry IQ** as required by the hackathon rules.

| Layer | Where it lives |
|---|---|
| **Reasoning model** | Azure AI Foundry project `inventoryiq` — `gpt-4o-mini` deployment for chat, `text-embedding-3-small` for vectors |
| **Knowledge source** | Azure AI Search index `inv-index` registered as a Foundry knowledge source |
| **Grounding** | Configured in `agent/manifest.json` → `groundingSources[0]` points at the Foundry knowledge source |
| **Action skill** | `agent/actions/draft_procurement_ticket.json` — turns a finding into a ticket draft |

> Why Foundry IQ over Fabric IQ for this build: Fabric trial provisioning is gated for tenants created from Azure free signups, while Foundry IQ runs entirely inside Azure AI Foundry on the same Azure credit. The repo's grounding contract is identical either way — same tools, same citations — so a Fabric IQ swap is a one-day addition.

## Quick start — local demo (no Azure needed)

```powershell
cd demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py          # builds inv.duckdb with ~500 assets, 30 days of monitoring, ~50 alerts
streamlit run app.py
```

Opens at <http://localhost:8501>. Try one of the demo questions above.

##  Step-by-Step Demo Testing

> [!IMPORTANT]
> **This local demo version does NOT require an Azure tenant, M365 subscription, or API keys.** It is the primary way for judges to verify functionality if an Azure environment is unavailable.

1. **Setup Environment**: From the `demo/` folder, install dependencies: `pip install -r requirements.txt`.
2. **Generate Mock Data**: Run `python seed.py`. This builds the local `inv.duckdb` file populated with ~500 assets and 30 days of history.
3. **Run the Dashboard**: Execute `streamlit run app.py` to launch the local chat interface.
4. **Submit a Query**: Use the sidebar to click a sample question (e.g., *"Which servers in Building B raised critical alerts?"*).
5. **Observe Grounding**: 
   - Watch the **Tool Call** chips show the internal routing and database queries.
   - Inspect the **Data Tables** and **Citations** provided in the assistant's response to see how it justifies its answer using the local database.

## Quick start — Foundry IQ deployment

1. **Provision** Azure AI Foundry project + Azure AI Search Free + Azure OpenAI (see [`docs/foundry_setup.md`](docs/foundry_setup.md)).
2. **Configure** `.env` from `.env.example` with your endpoints and keys.
3. **Index** — run `python grounding/scripts/01_index_inventorymapper.py` to push the lakehouse schema into Azure AI Search.
4. **Register** the index as a knowledge source in your Foundry project.
5. **Deploy agent** — see [`agent/README.md`](agent/README.md) for the Copilot Studio import.

## Status

| Track | Status |
|---|---|
| Local demo over DuckDB | ✅ working |
| Mock lakehouse + seed | ✅ working |
| Grounding tools + citations | ✅ working |
| Declarative agent manifest | ✅ drafted |
| Azure AI Search index | 🟡 pending Azure provisioning |
| Foundry IQ knowledge source | 🟡 pending Azure provisioning |
| End-to-end Copilot Studio publish | ⚪ pending |
| Demo video | ⚪ pending |

## Disclaimer

Built for demo purposes only. No confidential data. Schema, hostnames, users, alerts in this repo are synthetic. See [hackathon disclaimer](https://aka.ms/AgentsLeague_Disclaimer).

## License

MIT — see `LICENSE`.
