"""
Grounding layer — typed queries the agent calls as tools.

Same function shapes will be implemented against Fabric IQ later.
Each function returns rows + a `citations` block so the agent can
display "answer + source" the way Fabric IQ does.
"""

from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Any
import duckdb

DB_PATH = os.environ.get("DUCKDB_PATH", "inv.duckdb")


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH, read_only=True)


def _cite(rows: list[dict], table: str) -> dict[str, Any]:
    return {
        "rows": rows,
        "citations": [{"table": table, "row_id": r.get("id") or r.get("asset_id")} for r in rows[:10]],
    }


# ---------- tool functions ----------

def assets_by_alert_severity(severity: str = "Critical",
                             building: str | None = None,
                             floor: str | None = None,
                             hours: int = 24) -> dict[str, Any]:
    """Find assets with open alerts of a given severity, optionally filtered by building/floor."""
    con = _con()
    sql = """
        SELECT a.id, a.hostname, a.asset_type, l.building, l.floor, l.room,
               al.alert_type, al.severity, al.title, al.created_at
        FROM alerts al
        JOIN assets a    ON a.id = al.asset_id
        JOIN locations l ON l.id = a.location_id
        WHERE al.severity = ?
          AND al.is_resolved = FALSE
          AND al.created_at >= ?
    """
    params: list[Any] = [severity, datetime.utcnow() - timedelta(hours=hours)]
    if building:
        sql += " AND l.building = ?"; params.append(building)
    if floor:
        sql += " AND l.floor = ?"; params.append(floor)
    sql += " ORDER BY al.created_at DESC LIMIT 50"
    rows = con.execute(sql, params).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "alerts")


def stale_assets_by_department(department: str, days: int = 7) -> dict[str, Any]:
    """Laptops/desktops in a department that have not checked in for N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    con = _con()
    rows = con.execute("""
        SELECT id, hostname, assigned_user, department, last_check_in,
               operating_system, os_version
        FROM assets
        WHERE asset_type IN ('Laptop', 'Desktop')
          AND department = ?
          AND (last_check_in IS NULL OR last_check_in < ?)
          AND status = 'Active'
        ORDER BY last_check_in NULLS FIRST
        LIMIT 50
    """, [department, cutoff]).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "assets")


def assets_on_blueprint(blueprint_name_like: str) -> dict[str, Any]:
    """List assets placed on a blueprint matching a name fragment."""
    con = _con()
    rows = con.execute("""
        SELECT a.id, a.hostname, a.asset_type, a.online_state,
               a.blueprint_x, a.blueprint_y, b.name AS blueprint
        FROM assets a
        JOIN blueprints b ON b.id = a.blueprint_id
        WHERE b.name ILIKE ?
        ORDER BY a.hostname
        LIMIT 100
    """, [f"%{blueprint_name_like}%"]).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "assets")


def unsupported_os_by_location() -> dict[str, Any]:
    """Assets running OS/version combinations flagged as unsupported."""
    con = _con()
    rows = con.execute("""
        SELECT a.id, a.hostname, a.operating_system, a.os_version,
               l.building, l.floor, l.room, COUNT(*) OVER (PARTITION BY l.building) AS per_building
        FROM assets a
        JOIN locations l ON l.id = a.location_id
        JOIN alerts al   ON al.asset_id = a.id AND al.alert_type = 'OsUnsupported'
        WHERE al.is_resolved = FALSE
        ORDER BY l.building, a.hostname
        LIMIT 100
    """).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "assets")


def warranty_expiring(days_ahead: int = 90) -> dict[str, Any]:
    con = _con()
    rows = con.execute("""
        SELECT id, hostname, asset_type, manufacturer, model, warranty_end
        FROM assets
        WHERE warranty_end IS NOT NULL
          AND warranty_end <= (CURRENT_DATE + INTERVAL '%d days')
          AND warranty_end >= CURRENT_DATE
          AND status = 'Active'
        ORDER BY warranty_end
        LIMIT 100
    """ % int(days_ahead)).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "assets")


def disk_failure_pattern(days: int = 90) -> dict[str, Any]:
    """Servers with disk-failure alerts in the last N days, for procurement planning."""
    con = _con()
    rows = con.execute("""
        SELECT a.id, a.hostname, a.manufacturer, a.model, l.building, l.floor,
               al.created_at, al.severity
        FROM alerts al
        JOIN assets a    ON a.id = al.asset_id
        JOIN locations l ON l.id = a.location_id
        WHERE al.alert_type = 'DiskFailure'
          AND al.created_at >= ?
        ORDER BY al.created_at DESC
        LIMIT 100
    """, [datetime.utcnow() - timedelta(days=days)]).fetchdf().to_dict("records")
    con.close()
    return _cite(rows, "alerts")


def kpi_summary() -> dict[str, Any]:
    con = _con()
    row = con.execute("""
        SELECT
            (SELECT COUNT(*) FROM assets WHERE status='Active') AS active_assets,
            (SELECT COUNT(*) FROM assets WHERE online_state='Offline') AS offline_assets,
            (SELECT COUNT(*) FROM alerts WHERE severity='Critical' AND is_resolved=FALSE) AS open_critical,
            (SELECT COUNT(*) FROM alerts WHERE alert_type='WarrantyExpiring' AND is_resolved=FALSE) AS warranty_alerts
    """).fetchone()
    return {"rows": [{
        "active_assets": row[0], "offline_assets": row[1],
        "open_critical_alerts": row[2], "warranty_alerts": row[3],
    }], "citations": []}


# ---------- tool registry the LLM sees ----------

TOOLS = [
    {
        "type": "function", "function": {
            "name": "kpi_summary",
            "description": "Top-line counts: active assets, offline assets, open critical alerts, warranty alerts.",
            "parameters": {"type": "object", "properties": {}},
        }
    },
    {
        "type": "function", "function": {
            "name": "assets_by_alert_severity",
            "description": "Find assets with open alerts of a given severity in the last N hours. Optionally filter by building and floor.",
            "parameters": {"type": "object", "properties": {
                "severity": {"type": "string", "enum": ["Info", "Warning", "Critical"]},
                "building": {"type": "string"}, "floor": {"type": "string"},
                "hours":    {"type": "integer", "default": 24},
            }, "required": ["severity"]},
        }
    },
    {
        "type": "function", "function": {
            "name": "stale_assets_by_department",
            "description": "Laptops/desktops in a department that have not checked in for at least N days.",
            "parameters": {"type": "object", "properties": {
                "department": {"type": "string"}, "days": {"type": "integer", "default": 7},
            }, "required": ["department"]},
        }
    },
    {
        "type": "function", "function": {
            "name": "assets_on_blueprint",
            "description": "Assets placed on a blueprint whose name matches the given fragment.",
            "parameters": {"type": "object", "properties": {
                "blueprint_name_like": {"type": "string"},
            }, "required": ["blueprint_name_like"]},
        }
    },
    {
        "type": "function", "function": {
            "name": "unsupported_os_by_location",
            "description": "Assets running OS/version combinations flagged as unsupported (with location).",
            "parameters": {"type": "object", "properties": {}},
        }
    },
    {
        "type": "function", "function": {
            "name": "warranty_expiring",
            "description": "Active assets whose warranty expires within the next N days.",
            "parameters": {"type": "object", "properties": {
                "days_ahead": {"type": "integer", "default": 90},
            }},
        }
    },
    {
        "type": "function", "function": {
            "name": "disk_failure_pattern",
            "description": "Disk-failure alerts in the last N days — useful for procurement planning.",
            "parameters": {"type": "object", "properties": {
                "days": {"type": "integer", "default": 90},
            }},
        }
    },
]

CALLABLES = {
    "kpi_summary":              kpi_summary,
    "assets_by_alert_severity": assets_by_alert_severity,
    "stale_assets_by_department": stale_assets_by_department,
    "assets_on_blueprint":      assets_on_blueprint,
    "unsupported_os_by_location": unsupported_os_by_location,
    "warranty_expiring":        warranty_expiring,
    "disk_failure_pattern":     disk_failure_pattern,
}
