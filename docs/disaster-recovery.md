# Backup and Disaster Recovery

## Implemented approach

A `pg_dump -Fc` backup script was configured with a daily systemd timer (`ai-cloud-backup.timer`) and local retention. A backup timer was reported operational. Backups live outside the public GitHub repository.

## Verify local backup

```bash
sudo systemctl is-active ai-cloud-backup.timer
systemctl list-timers --all ai-cloud-backup.timer
sudo ls -lh /var/backups/ai-cloud-monitoring/
```

Custom-format archives can be inspected via `pg_restore -l`. **This is not a full restore test.**

## Safe restore verification

1. Copy a verified archive off the VPS over SSH.
2. Compare SHA-256 checksums at source and destination.
3. Create a **new, empty** PostgreSQL database, e.g. `cloud_monitoring_restore_test` on a local workstation.
4. Restore with `pg_restore --no-owner --no-privileges --exit-on-error`.
5. Compare schema and snapshot record counts; verify foreign keys and a few timestamps.
6. Delete isolated test resources only after preserving evidence.

Never test restore by overwriting the production database. A copy left only on the same VPS does not protect against loss of the whole VPS.

## Known gaps

A completed off-server restore and a full reboot recovery test were not confirmed in the available terminal outputs; treat them as pending until evidence exists.
