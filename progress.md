# Progress

## 2026-04-26
- Created persistent cleanup/backup plan.
- Confirmed the next phase is inventory + GitHub access verification before running any CPA upgrade.
- Inspected installer behavior without executing it.
- Verified remote server lacks GitHub SSH auth, while local machine has GitHub SSH auth.
- Confirmed target GitHub repositories are reachable from local SSH.
- Created full server-side pre-upgrade rollback archive at `/root/pre-upgrade-backups/pre-cpa-upgrade-20260425222741.tar.gz`.
- Staged sanitized GitHub backups locally under `/home/hpy/github-backups/`.
- Pushed sanitized `cliproxy` backup to GitHub `main`.
- Pushed sanitized `pioneer-portal` backup to GitHub `main`.
- Verified remote refs match local commit hashes and services remain active.
- Ran the one-click CPA installer on the remote server after backup.
- Upgraded CliProxyAPI from `6.9.34` to `6.9.38`.
- Resolved the installer-created root user service conflict by stopping/disabling the user-level service and keeping the system service active on `8317`.
- Created post-upgrade full rollback archive at `/root/pre-upgrade-backups/post-cpa-upgrade-20260425223958.tar.gz`.
- Refreshed the local sanitized `cliproxy` backup and pushed GitHub commit `677dfa7`.
- Verified the post-upgrade runtime path on `8320`: `gpt-5.4-mini`, `gpt-5.2`, and `gpt-5.5` all returned HTTP 200 with expected routed models.
