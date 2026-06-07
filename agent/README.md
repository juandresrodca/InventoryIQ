# Agent — InventoryIQ declarative agent for Microsoft 365 Copilot

This folder is the **deployable** declarative agent. It targets the M365
Copilot v1.2 declarative-agent schema and grounds on **Foundry IQ**.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | The agent definition (name, capabilities, grounding sources, actions). |
| `instructions.md` | The system prompt the agent runs with. |
| `actions/draft_procurement_ticket.json` | Action plugin for drafting ticket text. |
| `icons/` | 32×32 + 192×192 icons (TODO — placeholder until brand). |

## Deploy

1. Finish the Foundry IQ setup in `docs/foundry_setup.md` (Azure AI Foundry project + Azure AI Search index registered as a knowledge source).
2. Replace `${AZURE_AI_FOUNDRY_*}` / `${AZURE_SEARCH_*}` placeholders in `manifest.json` with your real values, or leave them as env-var references and let Copilot Studio resolve them at import time.
3. In **Copilot Studio** (`copilotstudio.microsoft.com`) → **Create → New agent → Import** → upload `manifest.json`.
4. Validate → Publish to your tenant.
5. Test in **Microsoft 365 Chat** (`copilot.microsoft.com`) → Agents → InventoryIQ.

## Local validation (before publishing)

The manifest follows the public schema at
<https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.2/schema.json>.
Validate with any JSON-schema validator, or use the **Teams Toolkit** preview.
