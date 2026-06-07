# grounding/scripts

Pushes InventoryMapper data into the Foundry IQ knowledge source
(an Azure AI Search index).

## Scripts

| Script | Purpose |
|---|---|
| `01_index_inventorymapper.py` | Read `demo/inv.duckdb` (or InventoryMapper SQL Server), embed every row, push to `inv-index` in Azure AI Search. |

## Run

After `.env` is populated (see `docs/foundry_setup.md`):

```powershell
cd grounding/scripts
..\..\demo\.venv\Scripts\Activate.ps1
pip install azure-search-documents azure-identity
python 01_index_inventorymapper.py --rebuild
```

`--rebuild` drops and recreates the index. Omit it to upsert.

## After indexing

In the Azure AI Foundry portal → your `inventoryiq` project → **Data + indexes →
Knowledge sources → + Add** → pick the search index `inv-index` → name it
`inv-knowledge`. That's what the declarative agent grounds on.
