"""
Build a realistic mock IT-asset lakehouse in DuckDB.

Mirrors the InventoryMapper schema (assets, locations, blueprints,
monitoring_records, alerts) so the same queries / semantic model
work locally and against Fabric IQ later.

Run: python seed.py [--db inv.duckdb] [--assets 500] [--days 30]
"""

from __future__ import annotations
import argparse
import os
import random
import uuid
from datetime import datetime, timedelta, date

import duckdb
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

ASSET_TYPES = ["Server", "Laptop", "Desktop", "NetworkSwitch", "Router", "Firewall", "Printer"]
OS_BY_TYPE = {
    "Server":        [("Windows Server", ["2016", "2019", "2022", "2025"]),
                      ("Ubuntu",          ["20.04", "22.04", "24.04"]),
                      ("RHEL",            ["8", "9"])],
    "Laptop":        [("Windows", ["10", "11"]), ("macOS", ["13", "14", "15"])],
    "Desktop":       [("Windows", ["10", "11"])],
    "NetworkSwitch": [("Cisco IOS", ["15.2", "16.9", "17.6"])],
    "Router":        [("Cisco IOS", ["15.2", "16.9", "17.6"])],
    "Firewall":      [("PAN-OS",    ["10.2", "11.0", "11.1"])],
    "Printer":       [("Printer FW", ["1.0", "2.1"])],
}
DEPARTMENTS = ["Finance", "Engineering", "Sales", "Marketing", "HR", "Operations", "Security", "IT"]
ALERT_TYPES = ["Offline", "HighTemp", "DiskFailure", "UnauthorizedAccess", "WarrantyExpiring", "OsUnsupported"]
UNSUPPORTED_OS = {("Windows Server", "2016"), ("Windows", "10"), ("Ubuntu", "20.04")}


def build_locations() -> list[dict]:
    locs = []
    # Three physical buildings, multiple floors / rooms / racks
    for building in ["Building A", "Building B", "Building C"]:
        for floor in ["Floor 1", "Floor 2", "Floor 3"]:
            for room in ["Server Room", "Office Area", "Cold Aisle"]:
                locs.append({
                    "id": str(uuid.uuid4()),
                    "name": f"{building} / {floor} / {room}",
                    "location_type": "Physical",
                    "building": building,
                    "floor": floor,
                    "room": room,
                    "rack": random.choice(["R01", "R02", "R03", None]),
                    "site": "HQ",
                    "cloud_provider": None,
                    "cloud_region": None,
                })
    # Cloud locations
    for provider, region in [("Azure", "westeurope"), ("Azure", "eastus2"), ("AWS", "us-east-1")]:
        locs.append({
            "id": str(uuid.uuid4()),
            "name": f"{provider} {region}",
            "location_type": "Cloud",
            "building": None, "floor": None, "room": None, "rack": None,
            "site": None,
            "cloud_provider": provider, "cloud_region": region,
        })
    return locs


def build_blueprints(locations: list[dict]) -> list[dict]:
    bps = []
    physical = [loc for loc in locations if loc["location_type"] == "Physical"]
    # One blueprint per (building, floor)
    seen = set()
    for loc in physical:
        key = (loc["building"], loc["floor"])
        if key in seen:
            continue
        seen.add(key)
        bps.append({
            "id": str(uuid.uuid4()),
            "name": f"{loc['building']} – {loc['floor']} Floor Plan",
            "description": f"Floor plan for {loc['building']} {loc['floor']}",
            "location_id": loc["id"],
        })
    return bps


def build_assets(n: int, locations: list[dict], blueprints: list[dict]) -> list[dict]:
    assets = []
    for _ in range(n):
        atype = random.choices(ASSET_TYPES, weights=[3, 5, 2, 1, 1, 1, 1])[0]
        os_family, versions = random.choice(OS_BY_TYPE[atype])
        os_version = random.choice(versions)
        # Laptops/desktops more likely in office areas; servers in server rooms
        if atype in ("Server", "NetworkSwitch", "Router", "Firewall"):
            loc = random.choice([item for item in locations if item["room"] in ("Server Room", "Cold Aisle") or item["location_type"] == "Cloud"])
        else:
            loc = random.choice([item for item in locations if item["location_type"] == "Physical"])

        # Maybe placed on a blueprint matching this location's building+floor
        bp = next((b for b in blueprints if b["location_id"] == loc["id"]), None)
        if bp is None and loc["location_type"] == "Physical":
            # Find a blueprint for the same building+floor (any room)
            same_floor_locs = [item["id"] for item in locations
                               if item["building"] == loc["building"] and item["floor"] == loc["floor"]]
            bp = next((b for b in blueprints if b["location_id"] in same_floor_locs), None)

        last_checkin_delta_hours = random.choices(
            [random.uniform(0, 1), random.uniform(1, 24), random.uniform(24, 24 * 14)],
            weights=[60, 30, 10],
        )[0]
        last_check_in = datetime.utcnow() - timedelta(hours=last_checkin_delta_hours)

        warranty_end = date.today() + timedelta(days=random.randint(-180, 1500))

        assets.append({
            "id": str(uuid.uuid4()),
            "hostname": f"{atype[:3].lower()}-{fake.unique.lexify(text='????').lower()}-{random.randint(10, 99)}",
            "ip_address": fake.ipv4_private(),
            "mac_address": fake.mac_address(),
            "serial_number": fake.bothify(text="SN-########").upper(),
            "asset_type": atype,
            "manufacturer": random.choice(["Dell", "HP", "Lenovo", "Cisco", "Palo Alto", "Apple"]),
            "model": fake.bothify(text="Model-####"),
            "operating_system": os_family,
            "os_version": os_version,
            "organizational_unit": random.choice(["OU=Workstations", "OU=Servers", "OU=Mobile"]),
            "assigned_user": fake.name() if atype in ("Laptop", "Desktop") else None,
            "department": random.choice(DEPARTMENTS) if atype in ("Laptop", "Desktop") else random.choice(["IT", "Operations"]),
            "status": random.choices(["Active", "InMaintenance", "Decommissioned"], weights=[92, 5, 3])[0],
            "online_state": random.choices(["Online", "Offline", "Degraded", "Unknown"], weights=[80, 10, 7, 3])[0],
            "last_check_in": last_check_in,
            "last_ping_at": last_check_in,
            "is_monitored": True,
            "monitoring_method": "Agent" if atype in ("Server", "Laptop", "Desktop") else "SNMP",
            "location_id": loc["id"],
            "blueprint_id": bp["id"] if bp else None,
            "blueprint_x": random.uniform(50, 1800) if bp else None,
            "blueprint_y": random.uniform(50, 1000) if bp else None,
            "warranty_end": warranty_end,
            "notes": None,
        })
    return assets


def build_monitoring(assets: list[dict], days: int) -> list[dict]:
    records = []
    now = datetime.utcnow()
    for a in assets:
        if a["status"] == "Decommissioned" or not a["is_monitored"]:
            continue
        for d in range(days):
            for h in range(0, 24, 2):   # one check every 2 hours
                checked = now - timedelta(days=days - d, hours=24 - h)
                # Mostly success; occasional failures for degraded/offline assets
                success_prob = {"Online": 0.99, "Degraded": 0.7, "Offline": 0.05, "Unknown": 0.6}[a["online_state"]]
                success = random.random() < success_prob
                records.append({
                    "id": str(uuid.uuid4()),
                    "asset_id": a["id"],
                    "state": a["online_state"] if success else "Offline",
                    "method": a["monitoring_method"],
                    "checked_at": checked,
                    "response_time_ms": random.uniform(0.5, 200) if success else None,
                    "success": success,
                    "details": None if success else "Timeout",
                })
    return records


def build_alerts(assets: list[dict]) -> list[dict]:
    alerts = []
    now = datetime.utcnow()
    for a in assets:
        # Offline alert
        if a["online_state"] == "Offline":
            alerts.append(_alert(a, "Offline", "Critical",
                                 f"{a['hostname']} is offline",
                                 f"No response from {a['hostname']} since {a['last_check_in']:%Y-%m-%d %H:%M} UTC.", now))
        # OS unsupported
        if (a["operating_system"], a["os_version"]) in UNSUPPORTED_OS:
            alerts.append(_alert(a, "OsUnsupported", "Warning",
                                 f"Unsupported OS on {a['hostname']}",
                                 f"{a['operating_system']} {a['os_version']} is past end-of-support.",
                                 now - timedelta(days=random.randint(1, 20))))
        # Warranty
        if a["warranty_end"] and 0 <= (a["warranty_end"] - date.today()).days <= 90:
            alerts.append(_alert(a, "WarrantyExpiring", "Info",
                                 f"Warranty ending for {a['hostname']}",
                                 f"Warranty expires {a['warranty_end']}.", now - timedelta(days=random.randint(0, 7))))
        # High temp / disk failure (random scatter on servers)
        if a["asset_type"] == "Server" and random.random() < 0.08:
            t = random.choice(["HighTemp", "DiskFailure"])
            alerts.append(_alert(a, t, "Critical",
                                 f"{t} on {a['hostname']}",
                                 f"Telemetry threshold exceeded on {a['hostname']}.",
                                 now - timedelta(hours=random.randint(0, 48))))
    return alerts


def _alert(asset: dict, atype: str, severity: str, title: str, msg: str, created_at: datetime) -> dict:
    resolved = random.random() < 0.25
    return {
        "id": str(uuid.uuid4()),
        "asset_id": asset["id"],
        "alert_type": atype,
        "severity": severity,
        "title": title,
        "message": msg,
        "is_read": resolved or random.random() < 0.5,
        "is_resolved": resolved,
        "resolved_at": created_at + timedelta(hours=random.randint(1, 24)) if resolved else None,
        "resolved_by": "ops-bot" if resolved else None,
        "created_at": created_at,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.environ.get("DUCKDB_PATH", "inv.duckdb"))
    p.add_argument("--assets", type=int, default=500)
    p.add_argument("--days", type=int, default=30)
    args = p.parse_args()

    if os.path.exists(args.db):
        os.remove(args.db)

    con = duckdb.connect(args.db)
    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r", encoding="utf-8") as f:
        con.execute(f.read())

    print("Building locations...")
    locations = build_locations()
    con.executemany(
        "INSERT INTO locations(id,name,location_type,building,floor,room,rack,site,cloud_provider,cloud_region) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(loc["id"], loc["name"], loc["location_type"], loc["building"], loc["floor"], loc["room"],
          loc["rack"], loc["site"], loc["cloud_provider"], loc["cloud_region"]) for loc in locations],
    )

    print("Building blueprints...")
    blueprints = build_blueprints(locations)
    con.executemany(
        "INSERT INTO blueprints(id,name,description,location_id) VALUES (?,?,?,?)",
        [(b["id"], b["name"], b["description"], b["location_id"]) for b in blueprints],
    )

    print(f"Building {args.assets} assets...")
    assets = build_assets(args.assets, locations, blueprints)
    con.executemany(
        """INSERT INTO assets(
            id,hostname,ip_address,mac_address,serial_number,asset_type,manufacturer,model,
            operating_system,os_version,organizational_unit,assigned_user,department,status,
            online_state,last_check_in,last_ping_at,is_monitored,monitoring_method,
            location_id,blueprint_id,blueprint_x,blueprint_y,warranty_end,notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(a["id"], a["hostname"], a["ip_address"], a["mac_address"], a["serial_number"],
          a["asset_type"], a["manufacturer"], a["model"], a["operating_system"], a["os_version"],
          a["organizational_unit"], a["assigned_user"], a["department"], a["status"],
          a["online_state"], a["last_check_in"], a["last_ping_at"], a["is_monitored"],
          a["monitoring_method"], a["location_id"], a["blueprint_id"],
          a["blueprint_x"], a["blueprint_y"], a["warranty_end"], a["notes"]) for a in assets],
    )

    print(f"Building monitoring history ({args.days} days)...")
    monitoring = build_monitoring(assets, args.days)
    con.executemany(
        "INSERT INTO monitoring_records(id,asset_id,state,method,checked_at,response_time_ms,success,details) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [(m["id"], m["asset_id"], m["state"], m["method"], m["checked_at"],
          m["response_time_ms"], m["success"], m["details"]) for m in monitoring],
    )

    print("Building alerts...")
    alerts = build_alerts(assets)
    con.executemany(
        "INSERT INTO alerts(id,asset_id,alert_type,severity,title,message,is_read,is_resolved,resolved_at,resolved_by,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(a["id"], a["asset_id"], a["alert_type"], a["severity"], a["title"], a["message"],
          a["is_read"], a["is_resolved"], a["resolved_at"], a["resolved_by"], a["created_at"]) for a in alerts],
    )

    counts = {
        "locations":          con.execute("SELECT count(*) FROM locations").fetchone()[0],
        "blueprints":         con.execute("SELECT count(*) FROM blueprints").fetchone()[0],
        "assets":             con.execute("SELECT count(*) FROM assets").fetchone()[0],
        "monitoring_records": con.execute("SELECT count(*) FROM monitoring_records").fetchone()[0],
        "alerts":             con.execute("SELECT count(*) FROM alerts").fetchone()[0],
    }
    con.close()
    print("Seed complete:")
    for k, v in counts.items():
        print(f"  {k:<20} {v:>7}")
    print(f"DuckDB file: {args.db}")


if __name__ == "__main__":
    main()
