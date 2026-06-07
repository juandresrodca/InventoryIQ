-- InventoryIQ lakehouse schema (DuckDB mock — mirrors Fabric lakehouse tables).
-- Mirrors the InventoryMapper EF Core entities: Asset, Location, Blueprint,
-- MonitoringRecord, AlertNotification.

CREATE TABLE IF NOT EXISTS locations (
    id              UUID PRIMARY KEY,
    name            VARCHAR NOT NULL,
    location_type   VARCHAR NOT NULL,   -- Physical | Virtual | Cloud
    building        VARCHAR,
    floor           VARCHAR,
    room            VARCHAR,
    rack            VARCHAR,
    site            VARCHAR,
    cloud_provider  VARCHAR,
    cloud_region    VARCHAR,
    is_default      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blueprints (
    id              UUID PRIMARY KEY,
    name            VARCHAR NOT NULL,
    description     VARCHAR,
    location_id     UUID REFERENCES locations(id),
    canvas_width    DOUBLE DEFAULT 1920,
    canvas_height   DOUBLE DEFAULT 1080,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id                   UUID PRIMARY KEY,
    hostname             VARCHAR NOT NULL,
    ip_address           VARCHAR,
    mac_address          VARCHAR,
    serial_number        VARCHAR,
    asset_type           VARCHAR NOT NULL,   -- Server | Laptop | Desktop | NetworkSwitch | Router | Firewall | Printer | Other
    manufacturer         VARCHAR,
    model                VARCHAR,
    operating_system     VARCHAR,
    os_version           VARCHAR,
    organizational_unit  VARCHAR,
    assigned_user        VARCHAR,
    department           VARCHAR,
    status               VARCHAR NOT NULL,   -- Active | Decommissioned | InMaintenance | Lost
    online_state         VARCHAR NOT NULL,   -- Online | Offline | Unknown | Degraded
    last_check_in        TIMESTAMP,
    last_ping_at         TIMESTAMP,
    is_monitored         BOOLEAN DEFAULT TRUE,
    monitoring_method    VARCHAR DEFAULT 'Ping',  -- Ping | Agent | SNMP
    location_id          UUID REFERENCES locations(id),
    blueprint_id         UUID REFERENCES blueprints(id),
    blueprint_x          DOUBLE,
    blueprint_y          DOUBLE,
    warranty_end         DATE,
    notes                VARCHAR,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monitoring_records (
    id                 UUID PRIMARY KEY,
    asset_id           UUID NOT NULL REFERENCES assets(id),
    state              VARCHAR NOT NULL,   -- Online | Offline | Degraded
    method             VARCHAR NOT NULL,
    checked_at         TIMESTAMP NOT NULL,
    response_time_ms   DOUBLE,
    success            BOOLEAN NOT NULL,
    details            VARCHAR
);

CREATE TABLE IF NOT EXISTS alerts (
    id            UUID PRIMARY KEY,
    asset_id      UUID REFERENCES assets(id),
    alert_type    VARCHAR NOT NULL,   -- Offline | HighTemp | DiskFailure | UnauthorizedAccess | WarrantyExpiring | OsUnsupported
    severity      VARCHAR NOT NULL,   -- Info | Warning | Critical
    title         VARCHAR NOT NULL,
    message       VARCHAR NOT NULL,
    is_read       BOOLEAN DEFAULT FALSE,
    is_resolved   BOOLEAN DEFAULT FALSE,
    resolved_at   TIMESTAMP,
    resolved_by   VARCHAR,
    created_at    TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assets_location    ON assets(location_id);
CREATE INDEX IF NOT EXISTS idx_assets_blueprint   ON assets(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_assets_dept        ON assets(department);
CREATE INDEX IF NOT EXISTS idx_mon_asset_checked  ON monitoring_records(asset_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_alerts_severity    ON alerts(severity, is_resolved);
