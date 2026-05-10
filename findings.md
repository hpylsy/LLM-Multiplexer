# Findings

## Working Fix
- The production fix is in `/root/pioneer-portal/scripts/vision_preprocess_proxy.py`.
- It normalizes text-only Responses `content` lists into strings for `gpt-5.4-mini` only.
- Verified with real HTTP: `gpt-5.4-mini` now reaches `deepseek-ai/deepseek-v4-pro` and returns HTTP 200 for the formerly failing `content: [{type:"input_text"}]` shape.

## CPA Upgrade Risk Inventory
- Installer source: `https://raw.githubusercontent.com/brokechubb/cliproxyapi-installer/refs/heads/master/cliproxyapi-installer`
- Installer uses `INSTALL_DIR="$HOME/cliproxyapi"`, so as root it targets `/root/cliproxyapi`.
- Files/directories the installer may create or change:
  - `/root/cliproxyapi/config_backup/config_YYYYmmdd_HHMMSS.yaml` by backing up current `config.yaml`.
  - `/root/cliproxyapi/<new-version>/` by extracting the latest release.
  - `/root/cliproxyapi/cli-proxy-api` by copying the new release binary.
  - `/root/cliproxyapi/config.yaml` by restoring from backup during upgrade.
  - `/root/cliproxyapi/cliproxyapi.service` by regenerating a service template.
  - `/root/cliproxyapi/version.txt` by writing the latest version.
  - Old version dirs matching `/root/cliproxyapi/*.*.*` may be removed, keeping latest two.
  - `$HOME/.config/systemd/user/cliproxyapi.service` may be created/updated.
- Current production service is system-level `/etc/systemd/system/cliproxyapi.service`, not the user-level service used by the installer.
- Current vision wrapper service is `/etc/systemd/system/pioneer-vision-preprocess.service`; installer should not manage it.
- Important non-installer state:
  - `/root/pioneer-portal/scripts/vision_preprocess_proxy.py`
  - `/etc/pioneer-portal/vision-preprocess.json`
  - `/var/cache/pioneer-vision-preprocess/cache.json`

## GitHub Backup Notes
- Remote server has no GitHub SSH key configured; `git@github.com` fails with publickey denied.
- Local machine has SSH access to GitHub as `hpylsy`.
- Backup path should be remote -> local temporary mirror -> GitHub push from local.
- GitHub account password should not be used for git push; use SSH or a PAT.
- Pushed `git@github.com:hpylsy/cliproxy.git` branch `main` at commit `17634713f4121c7c3989a63fb6e87ee2d22d9fad`.
- Pushed `git@github.com:hpylsy/pioneer-portal.git` branch `main` at commit `96d8a7ca0468367f7aaa92a2e4ac9d0a7c016f20`.
- Full server-side rollback archive: `/root/pre-upgrade-backups/pre-cpa-upgrade-20260425222741.tar.gz`.
- Final service check before handoff: `cliproxyapi.service` active and `pioneer-vision-preprocess.service` active.

## Post-Upgrade Results
- CliProxyAPI upgraded from `6.9.34` to `6.9.38`.
- Current release marker: `/root/cliproxyapi/version.txt` contains `6.9.38`.
- Upgrade binary info printed: `CLIProxyAPI Version: 6.9.38, Commit: 2c626efc, BuiltAt: 2026-04-25T13:41:11Z`.
- The installer created/enabled the root user-level service at `/root/.config/systemd/user/cliproxyapi.service`.
- Production should continue using the system-level service at `/etc/systemd/system/cliproxyapi.service`.
- Current service state after cleanup:
  - system `cliproxyapi.service`: active
  - `pioneer-vision-preprocess.service`: active
  - root user `cliproxyapi.service`: inactive and disabled
  - `8317`: `cli-proxy-api`
  - `8320`: Python vision preprocess proxy
- Post-upgrade rollback archive: `/root/pre-upgrade-backups/post-cpa-upgrade-20260425223958.tar.gz`.
- Post-upgrade sanitized `cliproxy` backup pushed to GitHub commit `677dfa7`.
- Post-upgrade real request verification through `http://127.0.0.1:8320/v1/responses`:
  - `gpt-5.4-mini` with list-style text content and `reasoning_effort: xhigh` returned HTTP 200 as `deepseek-ai/deepseek-v4-pro`.
  - `gpt-5.2` with list-style text content and `reasoning_effort: xhigh` returned HTTP 200 as `minimaxai/minimax-m2.7`.
  - `gpt-5.5` with string input returned HTTP 200 as `gpt-5.5`.
