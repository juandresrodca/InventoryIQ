# Foundry IQ setup — InventoryIQ

One-time provisioning of the Azure side. ~25 minutes start to finish.
Everything below stays within the Azure free credit.

## 1. Tenant prerequisites

- Microsoft Entra tenant (work/school identity, not personal MSA).
- Azure subscription with credit available (free tier or pay-as-you-go).
- You signed into the Azure portal as `juan@juanrod112hotmail.onmicrosoft.com` (or your equivalent native AAD user).

## 2. Resource group

- portal.azure.com → **+ Create a resource → Resource group**
- Name: `inventoryiq-rg`
- Region: **East US 2** *(widest model availability)* or **Sweden Central**
- Create.

## 3. Azure OpenAI

- **+ Create a resource → Azure OpenAI**
- Resource group: `inventoryiq-rg`
- Name: `inventoryiq-openai`
- Pricing tier: **Standard S0**
- Network: All networks (simplifies the demo).
- Create. ~2 minutes.
- After deployment → **Go to Azure AI Foundry portal** (button on the resource overview) → in the Foundry portal:
  - **Deployments → + Deploy model → gpt-4o-mini** → Deployment name `gpt-4o-mini` → Default options → Create.
  - **Deployments → + Deploy model → text-embedding-3-small** → Deployment name `text-embedding-3-small` → Create.
- Back in the Azure portal resource → **Keys and Endpoint** → copy:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY` (KEY 1)

## 4. Azure AI Search

- **+ Create a resource → Azure AI Search**
- Resource group: `inventoryiq-rg`
- Service name: `inventoryiq-search-<random>` (must be globally unique)
- Pricing tier: **Free (F)** — 50 MB, 3 indexes, plenty for the hackathon
- Region: same as Azure OpenAI
- Create. ~3 minutes.
- After deployment → **Keys** → copy:
  - `AZURE_SEARCH_ENDPOINT` (the `Url` on the Overview page)
  - `AZURE_SEARCH_API_KEY` (admin key, KEY 1)

## 5. Azure AI Foundry project (the IQ layer)

- portal.azure.com → search **"Azure AI Foundry"** → **+ Create**
- Resource group: `inventoryiq-rg`
- Hub name: `inventoryiq-hub`
- Project name: `inventoryiq`
- Region: same as the others.
- Connect: select the Azure OpenAI resource (`inventoryiq-openai`) and the Search resource (`inventoryiq-search-*`) you just created.
- Create.
- Open the Foundry project → copy:
  - `AZURE_AI_FOUNDRY_ENDPOINT`
  - `AZURE_AI_FOUNDRY_PROJECT` (= `inventoryiq`)

## 6. Fill `.env`

Copy `.env.example` to `.env` at the repo root and paste all the values:

```dotenv
GROUNDING=foundry

AZURE_AI_FOUNDRY_ENDPOINT=https://<foundry>.services.ai.azure.com/api/projects/inventoryiq
AZURE_AI_FOUNDRY_PROJECT=inventoryiq

AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_INDEX=inv-index
AZURE_SEARCH_API_KEY=...

AZURE_OPENAI_ENDPOINT=https://<openai>.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-10-21
```

## 7. Index the data

```powershell
cd grounding/scripts
..\..\demo\.venv\Scripts\Activate.ps1
pip install azure-search-documents azure-identity
python 01_index_inventorymapper.py
```

Pushes the rows from `demo/inv.duckdb` (or your real InventoryMapper DB) into the `inv-index` Azure AI Search index with vector embeddings.

## 8. Register the index as a Foundry knowledge source

- In Azure AI Foundry portal → your `inventoryiq` project → **Data + indexes → Knowledge sources → + Add**.
- Type: **Azure AI Search**.
- Pick `inventoryiq-search-*` → index `inv-index`.
- Description: *"InventoryMapper assets, locations, blueprints, monitoring records, alerts."*
- Save. Name it `inv-knowledge`.
- Copy the knowledge-source ID — drop it into `agent/manifest.json` if your Copilot Studio import requires a fully-qualified resource ID.

## 9. Wire the agent

- Open `agent/manifest.json`. Confirm the `${AZURE_SEARCH_ENDPOINT}` / `${AZURE_SEARCH_INDEX}` / `${AZURE_AI_FOUNDRY_*}` placeholders all point at your values.
- In **Copilot Studio** (`copilotstudio.microsoft.com`) → **Create → New agent → Import** → upload `manifest.json`.
- Validate → Publish.

## 10. Test

In M365 Chat → Agents → InventoryIQ → ask:

> *"Which servers in Building B raised critical alerts in the last 24 hours?"*

Expected: short table + citations referencing the `alerts` and `assets` documents in `inv-index`.

## Estimated cost during hackathon

| Resource | Tier | Hackathon cost (8 days) |
|---|---|---|
| Azure OpenAI gpt-4o-mini | Standard S0 | ~$1–3 (pay per token) |
| Azure OpenAI text-embedding-3-small | Standard S0 | < $0.50 (one-time index build) |
| Azure AI Search | **Free** | $0 |
| Azure AI Foundry hub | Standard | $0 (hub is free; only its compute costs) |
| **Total** | | **< $5 of your $200 credit** |
