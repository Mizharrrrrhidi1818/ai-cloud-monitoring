# Deployment Guide — Ubuntu VPS

> Commands are illustrative of the verified project layout. Confirm your actual Dockerfile, schema and environment variable names before using them on any server. Never commit server credentials.

## Core services

- Host Ubuntu Python collector managed by `ai-cloud-collector.service`.
- Docker Compose services: `postgres`, `ai-detector`, `alert-manager`, `dashboard`.
- PostgreSQL listen binding: `127.0.0.1:15432:5432`.
- Streamlit listen binding: `127.0.0.1:8502:8501`.

## Preflight and observation

```bash
cd ~/ai-cloud-monitoring
sudo docker compose -f compose.cloud.yaml config --quiet
sudo docker compose -f compose.cloud.yaml ps
sudo systemctl status ai-cloud-collector --no-pager
sudo docker compose -f compose.cloud.yaml logs --tail=30 ai-detector
sudo docker compose -f compose.cloud.yaml logs --tail=30 alert-manager
free -h
```

## Windows SSH dashboard tunnel

```powershell
ssh -N -L 8503:127.0.0.1:8502 ubuntu@YOUR_VPS_IP
```

Open `http://localhost:8503/` while the SSH connection remains open.

## Minimal-risk service deployment

1. Keep a dated backup of the service source and model artifact.
2. Validate Python syntax and the full expected test suite locally.
3. Transfer only reviewed files via SCP to staging.
4. Verify staging filenames and Python compilation.
5. Build only the affected Docker Compose service.
6. Recreate that service using `--no-deps`.
7. Inspect logs, container state, CPU/RAM/disk collection and database record growth.
8. Roll back using the backed-up files if verification fails.

Example for alert-manager **only after tests pass**:

```bash
sudo docker compose -f compose.cloud.yaml build alert-manager
sudo docker compose -f compose.cloud.yaml up -d --no-deps --force-recreate alert-manager
sudo docker compose -f compose.cloud.yaml logs --tail=30 alert-manager
```

Do not run `docker compose down -v`: that can remove persistent database volumes. Do not represent a build as proof of running health.
