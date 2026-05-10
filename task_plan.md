# CPA Upgrade And Backup Plan

## Goal
Prepare for and complete a CliProxyAPI upgrade by preserving the working server state, backing up the relevant remote projects to GitHub, documenting files likely to be changed by the one-click installer, and verifying the post-upgrade runtime path.

## Current Status
- [x] Confirmed current bugfix works in production path.
- [x] Started persistent planning notes for cleanup/backup/upgrade prep.
- [x] Inventory files and services that the CPA installer may change.
- [x] Verify GitHub access method without storing secrets.
- [x] Back up `/root/cliproxyapi` to `git@github.com:hpylsy/cliproxy.git`.
- [x] Back up `/root/pioneer-portal` to `git@github.com:hpylsy/pioneer-portal.git`.
- [x] Final verification and handoff notes before CPA upgrade.
- [x] Upgrade CliProxyAPI from 6.9.34 to 6.9.38.
- [x] Resolve installer-created root user service conflict on port `8317`.
- [x] Refresh and push sanitized post-upgrade `cliproxy` GitHub backup.
- [x] Verify post-upgrade model routing through port `8320`.

## Guardrails
- Do not print or store user-provided credentials.
- Prefer SSH GitHub access; GitHub account passwords are not suitable for git push.
- Do not run the CPA upgrade command until backup state is confirmed.
- Avoid committing bulky logs, caches, virtualenvs, secrets, or generated runtime state.

## Errors Encountered
| Time | Error | Resolution |
| --- | --- | --- |
| 2026-04-26 | Tar command used a `**/__pycache__` pattern that local zsh tried to expand | Re-ran with a portable tar exclude pattern: `--exclude='*/__pycache__'` |
| 2026-04-26 | CPA installer enabled a root user-level `cliproxyapi.service` that conflicted with the production system service on `8317` | Stopped and disabled the user-level service, then kept `/etc/systemd/system/cliproxyapi.service` active |
| 2026-04-26 | `/root/cliproxyapi/cli-proxy-api --version` exits nonzero because the binary does not define `--version`, though it prints version info | Use `/root/cliproxyapi/version.txt` and live request verification as the reliable checks |
