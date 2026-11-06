# Public Repository Security Review

Before publishing, inspect `git diff --cached --name-only` and `git diff --cached` for secrets. Never commit `.env`, credentials, SSH private keys, PostgreSQL dump files, raw telemetry containing personal identifiers, production SQL exports, or pickled models without review. If a secret was ever committed, removing the file does not erase Git history; rotate the secret and remove it from history before publication.

For reproducibility provide `.env.example` with placeholders, not actual credentials. Keep Docker Compose localhost port bindings. Only publish screenshots after checking they do not expose public IPs, usernames, hostnames, account identifiers, access tokens or private dashboards.
