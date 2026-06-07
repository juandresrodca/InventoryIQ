# Demo script — 3-minute walkthrough

Target: 3:00 max. Practice once before recording.

## 0:00 — 0:20  Hook

> "IT operations teams sit on tons of asset data — but every question
> becomes a tab-juggling excavation. InventoryIQ is a Microsoft 365 Copilot
> agent that answers those questions in natural language, grounded in
> Microsoft Fabric IQ over your live asset lakehouse. Every claim is cited
> back to a row. Let me show you."

## 0:20 — 0:50  Question 1 — Critical alerts

In Teams → @InventoryIQ:

> *"Which servers in Building B raised critical alerts in the last 24 hours?"*

Show: short table, 3 rows, all rack R02. Citation block opens to show the
`alerts` table rows.

## 0:50 — 1:20  Question 2 — Cross-entity reasoning

> *"Of those, which are running unsupported OS versions?"*

Show: agent joins alerts + assets, returns 1 row, cites both tables.

## 1:20 — 1:50  Question 3 — Spatial

> *"Where are they on the floor plan?"*

Show: agent calls `assets_on_blueprint`, returns hostnames + (x, y), demo
opens the InventoryMapper UI in a split for visual reference.

## 1:50 — 2:30  Action

> *"Draft a procurement ticket for replacement drives based on this quarter's failure pattern."*

Show: agent calls `disk_failure_pattern`, then the `draftProcurementTicket`
action. Ticket text appears: subject, body, justification, vendor suggestion.

## 2:30 — 3:00  Architecture flash + close

Show the architecture diagram (`docs/architecture.png`).

> "InventoryMapper data is mirrored into a Fabric lakehouse. A semantic model
> exposes Asset, Location, Blueprint, Alert, Reading. Fabric IQ grounds the
> declarative agent. The agent runs anywhere M365 Copilot runs.
> Repo and Streamlit fallback in the description."

## B-roll

- 3 seconds of the InventoryMapper floor-plan editor with placed assets.
- 3 seconds of the Fabric lakehouse Tables view.
- 3 seconds of the Streamlit demo answering the same question, to prove the
  agent is grounded not improvised.
