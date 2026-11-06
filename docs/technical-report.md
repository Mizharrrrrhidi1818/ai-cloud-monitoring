# Technical Project Report

**Project:** AI-Powered Cloud Infrastructure Monitoring and Anomaly Detection on Ubuntu VPS  
**Version:** 1.0 portfolio candidate  
**Primary data:** SumoPod Ubuntu VPS historical metrics snapshot  
**Language:** English

## 1. Background and Motivation

Cloud infrastructure needs continuous visibility into CPU load, memory pressure, and disk capacity. Manual checks are difficult to reproduce, and an isolated anomaly score is insufficient for operational alerting. This project explores a low-cost, self-hosted monitoring pipeline that combines structured measurements, anomaly detection, rule-based alerts, dashboards, and basic DevOps recovery practices.

## 2. Objectives and Scope

- Collect actual Ubuntu VPS host metrics approximately every five seconds.
- Persist observations and predictions in PostgreSQL.
- Use Isolation Forest to flag statistically unusual observations.
- Create critical alerts subject to resource thresholds and a five-minute cooldown.
- Expose a Streamlit dashboard through an SSH tunnel.
- Practice unit/integration testing, backups, deployment and rollback.

The project is a portfolio prototype, not a production-certified availability system. Windows is the development environment; the VPS is the **only main infrastructure-analysis subject**.

## 3. Infrastructure and Architecture

The Ubuntu host runs `psutil` collection under systemd. Docker Compose runs PostgreSQL 17, the AI detector, the alert manager and Streamlit. Host loopback port bindings protect the database and dashboard from direct public exposure. See [architecture](architecture.md).

## 4. Implementation Walkthrough

### 4.1 Local development

Create a Python virtual environment, install dependencies, implement `src/monitor.py` and `src/database.py`, and validate SQL inserts locally. Use `src/ml/train_model.py` for the initial baseline model, then run `src/ml/detect_anomaly.py` and `src/alerts/alert_manager.py`. Automated tests run through `unittest`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_alert*.py' -v
```

### 4.2 Database structure and SQL

The full executable schema is in **`schema.sql`**; examples below explain the actual analytical queries without replacing the authoritative schema.

```sql
SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
FROM system_metrics;

SELECT m.timestamp, m.cpu_percent, m.memory_percent,
       m.disk_percent, a.prediction, a.anomaly_score
FROM system_metrics AS m
JOIN anomaly_predictions AS a ON a.metric_id = m.id
WHERE a.prediction = -1
ORDER BY m.timestamp DESC
LIMIT 10;

SELECT COUNT(*)
FROM system_metrics AS m
LEFT JOIN anomaly_predictions AS a ON a.metric_id = m.id
WHERE a.id IS NULL;
```

### 4.3 Cloud deployment

Docker Engine and Docker Compose were installed on Ubuntu. PostgreSQL, the AI detector, alert manager, and dashboard were containerized; the collector stayed on the host for correct host metrics. Service configuration was validated before launch. Refer to [deployment](deployment.md) for the commands.

```bash
sudo docker compose -f compose.cloud.yaml config --quiet
sudo docker compose -f compose.cloud.yaml ps
sudo systemctl is-active ai-cloud-collector
sudo journalctl -u ai-cloud-collector -n 10 --no-pager
```

### 4.4 ML model implementation

The original model used `IsolationForest` with `n_estimators=200`, `contamination=0.03`, `random_state=42`. A later **Windows-trained candidate based on VPS data** used an end-to-end `Pipeline(StandardScaler(), IsolationForest(...))`, with chronological 80/20 train/test split. The pipeline ensures scaling is fitted only on training data.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

model = Pipeline([
    ('scaler', StandardScaler()),
    ('isolation_forest', IsolationForest(
        n_estimators=200, contamination=0.03,
        random_state=42, n_jobs=-1
    )),
])
model.fit(train_df[['cpu_percent', 'memory_percent', 'disk_percent']])
```

The **production model remained distinct** from the candidate; no verified deployment of the candidate was provided.

### 4.5 Alerting

Early confirmed implementation generated critical alerts when an AI anomaly coincided with CPU >=90%, RAM >=90%, or disk >=95%, using a five-minute cooldown. Controlled integration tests used temporary database tables and rollback. Later evaluation found a 99% disk synthetic sample classified normal; a threshold-independent critical alert design was proposed to prevent this failure. This report does not assert that the revised logic is live until the new tests and VPS deployment are verified.

## 5. VPS Data Collection Results

The validated CSV export contained **11,804 rows** from **2026-11-04 16:14:02** to **2026-11-05 08:58:02**, a span of **16 h 44 min**. No missing values, duplicate IDs or utilization values outside 0–100% were found. Median collection interval was **5.008872 seconds**, with one gap greater than 15 seconds.

| Utilization (%) | Mean | Standard deviation | Minimum | Maximum |
|---|---:|---:|---:|---:|
| CPU | 3.30 | 3.12 | 0.00 | 52.30 |
| Memory | 58.18 | 0.78 | 45.20 | 67.60 |
| Disk | 46.81 | 0.28 | 41.20 | 46.90 |

CPU mostly remained low and disk scarcely varied, limiting exposure to high-load and disk-near-full behavior. These are properties of this particular observation window, not general VPS performance claims.

## 6. Model Evaluation

The candidate was fitted on **9,443 earlier records** and evaluated on **2,361 later records**. It classified **2,289 normal** and **72 anomalous**, an **anomaly rate of 3.05%**. Six hand-defined scenarios produced **4/6 agreements**. A synthetic 99% disk reading was classified NORMAL; a 35% CPU reading was classified ANOMALY although labeled expected-normal. These observations motivate threshold-based criticality independent of the ML model.

**Limitations:** Ground-truth incident labels were unavailable. Therefore neither anomaly rate nor scenario agreement is a defensible estimate of production classification accuracy, precision, recall, or F1.

## 7. Testing and Reliability

Nine alert-rule tests, five cooldown tests, and four PostgreSQL integration tests (18 total) passed in earlier reported runs. Five controlled VPS alert integration tests passed using a temporary table and rollback. Six model compatibility tests passed on Windows. Docker service health and continuous collector writes were observed. Post-change threshold-only tests and a full reboot restore demonstration require separate verification; see [testing](testing.md).

## 8. Database Backup and Recovery

A scheduled `pg_dump` workflow was configured through systemd. Backup verification via archive inspection should be supplemented by restoration to a separately named database, record count comparisons and an off-server copy. Do not claim a completed disaster recovery drill without its results.

## 9. Challenges and Lessons Learned

- Repaired Docker Compose YAML syntax issues by validating the Compose configuration.
- Corrected `DataFrame.between` misuse by comparing feature columns against 0 and 100 separately.
- Repaired incorrect systemd unit sections and validated service loading.
- Kept the host collector outside Docker to monitor actual VPS resources.
- Used RAM constraints and staged deployments to avoid unnecessary service disruption on a roughly 2 GiB VPS.
- Discovered that anomaly detection and critical operational thresholds are not interchangeable.

## 10. Conclusion and Future Work

The project demonstrates an end-to-end monitoring pipeline and several practical DevOps operations: Linux services, Docker, PostgreSQL, Python automation, unit/integration testing, logging, backup and controlled deployment. The next release should verify the revised critical-alert policy in production, demonstrate a clean restore and reboot recovery, and gather labeled incidents before making accuracy claims. These items are **not asserted as already complete** in this report.
