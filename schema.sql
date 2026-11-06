
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    cpu_percent DOUBLE PRECISION NOT NULL
        CHECK (cpu_percent BETWEEN 0 AND 100),
    memory_percent DOUBLE PRECISION NOT NULL
        CHECK (memory_percent BETWEEN 0 AND 100),
    disk_percent DOUBLE PRECISION NOT NULL
        CHECK (disk_percent BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
ON system_metrics(timestamp);

CREATE TABLE IF NOT EXISTS anomaly_predictions (
    id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL UNIQUE
        REFERENCES system_metrics(id),
    prediction INTEGER NOT NULL
        CHECK (prediction IN (-1, 1)),
    anomaly_score DOUBLE PRECISION NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_alerts (
    id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL UNIQUE
        REFERENCES system_metrics(id),
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
