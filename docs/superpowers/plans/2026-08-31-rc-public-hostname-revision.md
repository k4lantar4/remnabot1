# RC public hostname plan revision

> **Status 2026-08-31:** Authority patches from this file are **applied** in `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md`. Do not re-introduce `staging-host-*` as RC env URLs. This file remains the revision batch record, not a second architecture spec.

**Goal:** Replace the invented `staging-host-*` RC public identity with the live RC identity already working on this host: `/opt/remnabot1/.env` + Caddy `panel.rookari.com`.

**Architecture:** Do not change the running remnabot1 compose or `/opt/remnabot1/.env`. Patch the MVP plan and the M1-T3 rehearsal artifacts so they copy the live RC public URLs. Keep two stacks distinct: the **running sandbox** (`remnawave_bot` + `http://remnawave:3000` + `panel.rookari.com`) versus the **isolated rehearsal compose** (not started; `rehearsal_rw` docker-internal only). Do not execute M1-T4 as written (no new `staging-host-*` Caddy, no HTTP-01).

**Tech Stack:** Markdown plan/rule, gitignored env, Docker Compose `config` (no `up`), Caddy already live at `/opt/caddy/Caddyfile`.

## Global Constraints

- Single authority after Task 1: `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md`.
- Work tree: `/opt/remnabot1` branch `prod-cutover`. Do not push. Do not retarget `origin` to `k4lantar4/remnabot`.
- Never print secret values. Chat/git: key names + 16-hex sha256 fingerprints only. Never commit `.env`, `.env.rehearsal`, `.env.rehearsal-rw`, `.env.cutover`, or card numbers.
- Do not modify `/opt/remnabot1/.env` (live running container env). Do not restart the live remnabot1 stack as part of this revision.
- Do not `docker compose up` rehearsal. Do not restore. Do not `alembic upgrade`/`stamp` on dumps. Do not start `rehearsal_bot`.
- Do not edit live `/opt/caddy/Caddyfile`. Do not HTTP-01. Do not add production names (`cabinet.rookari.com`, `hooks.rookari.com`, `master.rookari.com`, `sub.rookari.com`, `miniapp.rookari.com`) to RC Caddy.
- Production cutover names that **move** stay: `cabinet`, `hooks`, `master`, `sub`, `miniapp`. Names that **must not** be treated as production cutover stay: `panel`, `rw`, `config`, `admin*`, apex `rookari.com`.
- M1-T2 token guard stays. `PRODUCTION_BOT_TOKEN_FINGERPRINT` stays the production fingerprint. RC continues to use the existing **test** token (do not copy production `BOT_TOKEN`).
- Dirty WT must not be committed: `docker-compose.yml`, Russian→English `docs/*.md`, `locales/`, `uv.lock`, deleted `docs/superpowers/plans/2026-08-31-plan-update-handoff.md`.
- Do not guess a new P1 chat id. Live RC has `C2C_ENABLED=true` and empty `C2C_ADMIN_CHAT_ID` — match that in rehearsal env. G8 isolated-chat PASS remains a later MVP gate, not this batch.
- Fingerprint algorithm: first 16 hex of sha256(utf-8), same as `app.custom.safety.token_guard.token_fingerprint`.

---

## Binding facts (verified 2026-08-31, this host)

Operator correction (binding): **staging is not the operational RC.** Correct variables are in `/opt/remnabot1/.env`. The container already running is the working RC.

| Fact | Value | Class |
|---|---|---|
| Live RC public cabinet/API | `https://panel.rookari.com` (`/opt/caddy/Caddyfile`: `/api/*` → `remnawave_bot:8080`, else `cabinet_frontend`) | VERIFIED |
| Live bot env | `/opt/remnabot1/.env` — `CABINET_URL=https://panel.rookari.com`, `WEBHOOK_URL=panel.rookari.com`, `BOT_RUN_MODE=polling`, `WEB_API_ALLOWED_ORIGINS=*`, `CABINET_ALLOWED_ORIGINS=*`, `REMNAWAVE_API_URL=http://remnawave:3000`, `C2C_ENABLED=true`, `C2C_ADMIN_CHAT_ID` empty | VERIFIED |
| Live RC Remnawave env | `/opt/remnawave/.env` — `PANEL_DOMAIN=rw.rookari.com`, `FRONT_END_DOMAIN=*`, `SUB_PUBLIC_DOMAIN=config.rookari.com/sub` | VERIFIED |
| RC Caddy `staging-host-*` blocks | **absent** | VERIFIED |
| `getent`/`dig` A for `staging-host-{hooks,cabinet,miniapp,sub,master}.rookari.com` | all `91.107.144.95` (this host) | VERIFIED |
| `staging.rookari.com` / random `asdfxyz.rookari.com` | no A record (not a zone wildcard) | VERIFIED |
| Production app names | `cabinet`/`hooks`/`master`/`sub`/`miniapp` → `91.107.249.43` | VERIFIED |
| M1.2 HEAD at plan write | `prod-cutover` @ `a1b4c59f` | VERIFIED |

**How to read the DNS vs operator conflict:** A records named `staging-host-*` currently point at RC, but they have **no Caddy site** and are **not** what the running bot uses. Do not put those names in env, matrix, or M1-T4. Do not delete Cloudflare records in this batch (P2 still UNKNOWN).

**Two stacks (do not conflate):**

| Stack | Env | Panel URL inside Docker | Public hostname | Start? |
|---|---|---|---|---|
| Live remnabot1 sandbox | `/opt/remnabot1/.env` | `http://remnawave:3000` | `panel.rookari.com` | already running — do not touch |
| Isolated rehearsal compose | `.env.rehearsal` (gitignored) | `http://rehearsal_rw:3000` | same **public** URLs as live `.env` (`panel.rookari.com`) | do not `up` `rehearsal_bot` until M4-T0 |

---

## File structure

| File | Responsibility |
|---|---|
| `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md` | Single authority. Replace `staging-host-*` RC public identity with live `panel` / `rw` / `config`. Rewrite M1-T3/M1-T4/M1-T5/G9 text. |
| `.cursor/rules/10-remnabot-migration.mdc` | §9 Caddy RC hostnames line — match the patched plan. |
| `docs/superpowers/evidence/2026-08-31-env-matrix.md` | Amend M1-T3 matrix RC URL rows + verification. Fingerprints only. |
| `docker-compose.rehearsal.yml` | `WEB_API_ALLOWED_ORIGINS` and Vite bot username — match live RC, not `staging-host-cabinet`. |
| `.env.rehearsal` | Gitignored. Public URLs + CORS + C2C flag from live `.env`. Keep `REMNAWAVE_API_URL=http://rehearsal_rw:3000` and `PRODUCTION_BOT_TOKEN_FINGERPRINT`. Do not commit. |
| `.env.rehearsal-rw` | Gitignored. `PANEL_DOMAIN=rw.rookari.com`, `SUB_PUBLIC_DOMAIN=config.rookari.com/sub`, `FRONT_END_DOMAIN=*` matching live `/opt/remnawave/.env`. Keep generated JWTs. Do not commit. |

Do **not** create `deploy/caddy/` in this batch.

---

### Task 1: Patch the MVP plan + migration rule (authority)

- **ID:** REV-T1 · **WEIGHT:** 3 · **RISK:** Low · **DEPENDENCIES:** none
- **GOAL:** The single-authority plan no longer tells executors to use `staging-host-*` as RC public URLs.
- **FILES:** Modify `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md`; Modify `.cursor/rules/10-remnabot-migration.mdc`

- [ ] **Step 1: Confirm live HEAD and that you will not edit `.env`**

```bash
cd /opt/remnabot1
git branch --show-current
git rev-parse --short HEAD
git status -sb
test -f /opt/remnabot1/.env && echo "live env present (do not edit)"
```

Expected: branch `prod-cutover`; HEAD is a descendant of `a1b4c59f` (re-check live; do not chase a remembered SHA). Dirty WT may exist — leave it.

- [ ] **Step 2: In the MVP plan, replace identity 5 RC hostname phrase**

Find the Six identities table cell for identity 5 that contains `staging-host-*`. Replace that hostname phrase with: test Telegram token · public hostname `panel.rookari.com` (live `/opt/remnabot1/.env`). Isolated rehearsal compose is a separate stack (not started until M4-T0). Current remnabot1 compose is the **working RC sandbox**.

- [ ] **Step 3: Replace E5 body** so M1-T4 is not “add staging-host Caddy”

Replace the `### E5. Production Caddy staging-host-*` section with:

```markdown
### E5. RC public hostname is `panel.rookari.com` (not `staging-host-*`)

**VERIFIED 2026-08-31:** Bot `/opt/caddy-remnawave/Caddyfile` has `staging-host-{hooks,cabinet,miniapp,sub}` server blocks. RC `/opt/caddy/Caddyfile` has **no** those blocks. RC **does** serve `https://panel.rookari.com` (`/api/*` → `remnawave_bot:8080`, else cabinet).

**Operator binding:** staging is not the operational RC. Live bot env `/opt/remnabot1/.env` is the RC public-URL source (`CABINET_URL=https://panel.rookari.com`, `WEBHOOK_URL=panel.rookari.com`, polling).

DNS A records named `staging-host-*` currently resolve to RC (`91.107.144.95`) but have no RC Caddy site. Do **not** put those names in RC env. Do **not** HTTP-01 them. Do **not** duplicate Bot’s staging blocks.

M1-T4 as originally written (**author `staging-host-*` on RC**) is **cancelled**. Leave live RC Caddy unchanged in M1. Public RC name remains `panel.rookari.com`. Production application names stay off RC Caddy until M8.
```

- [ ] **Step 4: Replace Environment class B public-URL rows**

In `### Environment classes (A–E)`, replace the class B table rows for webhook/cabinet/CORS/C2C/RW domains with:

```markdown
| Variable | RC value shape |
|---|---|
| `BOT_TOKEN` | existing **test** token only (live `/opt/remnabot1/.env`) |
| `BOT_RUN_MODE` | `polling` (live `.env`; do not switch to webhook unless the user asks) |
| `WEBHOOK_URL` | `panel.rookari.com` (live `.env`). Never `https://hooks.rookari.com` |
| `WEBHOOK_SECRET_TOKEN` | empty while polling |
| `CABINET_URL` | `https://panel.rookari.com` |
| `WEB_API_ALLOWED_ORIGINS` | `*` (live `.env`; working RC) |
| `CABINET_ALLOWED_ORIGINS` | `*` (live `.env`) |
| `C2C_ENABLED` | `true` (live `.env`). `C2C_ADMIN_CHAT_ID` empty. Do not copy a production admin chat id |
| Remnawave `PANEL_DOMAIN` | `rw.rookari.com` (live `/opt/remnawave/.env`) |
| Remnawave `FRONT_END_DOMAIN` | `*` (live RW env) |
| Remnawave `SUB_PUBLIC_DOMAIN` | `config.rookari.com/sub` (live RW env) |
| `IS_TELEGRAM_NOTIFICATIONS_ENABLED` | `false` unless a **non-production** RW Telegram token exists |
| `REMNAWAVE_API_URL` | live sandbox: `http://remnawave:3000`. Isolated rehearsal compose only: `http://rehearsal_rw:3000` |
```

Keep the class A / C / D / E prose. Class E still forbids production `BOT_TOKEN`, production `https://hooks.rookari.com` as RC webhook, production `C2C_ADMIN_CHAT_ID`, production payment tokens.

- [ ] **Step 5: Replace Telegram isolation RC webhook sentence**

Replace the sentence that says RC webhook only `https://staging-host-hooks.rookari.com` with: RC uses **polling** and `WEBHOOK_URL=panel.rookari.com` per live `.env`. Never `setWebhook` / `getUpdates` with the production token. `WEBHOOK_IP` unset.

- [ ] **Step 6: Replace G9, M1-T3, M1-T4, M1-T5, M5-T1 hostname text**

- G9 Must show: `https://panel.rookari.com` login/API; FA; Toman. Not `staging-host-cabinet`.
- M1-T3 RC overrides list: same URLs as Step 4. `WEB_API_ALLOWED_ORIGINS=*`. `C2C_ENABLED=true` matching live `.env`.
- M1-T4: first line after GOAL: **CANCELLED as written.** Do not author `staging-host-*`. Do not HTTP-01. Do not copy live Caddy into `deploy/caddy/` in this revision. Checkpoint M1.3 is **not** opened by this file.
- M1-T5 CORS line: `WEB_API_ALLOWED_ORIGINS=*` matching live `.env` (overrides the earlier staging-host CORS pin).
- M5-T1 / any `staging-host-cabinet` / `staging-host-sub` verification strings: `panel.rookari.com` / `config.rookari.com` as applicable.

Add a one-line banner under the existing “Plan updated 2026-08-31” note: **RC public hostname revision 2026-08-31:** operational RC is `panel.rookari.com` + live `/opt/remnabot1/.env`, not `staging-host-*`.

- [ ] **Step 7: Patch the migration rule Caddy paragraph**

In `.cursor/rules/10-remnabot-migration.mdc` section 9, replace `RC hostnames: staging-host-* only until cutover.` with:

```markdown
RC public hostname: `panel.rookari.com` (live `/opt/remnabot1/.env` + `/opt/caddy/Caddyfile`). Do not invent `staging-host-*` env URLs. Production names absent from RC Caddy until M8.
```

- [ ] **Step 8: Grep the two patched files for leftover RC-as-staging-host instructions**

```bash
cd /opt/remnabot1
grep -n 'staging-host' docs/superpowers/plans/2026-08-28-production-cutover-mvp.md .cursor/rules/10-remnabot-migration.mdc
```

Expected leftover uses (OK): E5 explaining Bot’s unused Caddy blocks; DNS “must not move” list that still names `staging-host-*` as **not** a production cutover name; M7-T5 “do not move staging-host unless runbook says”. **Not OK:** any remaining instruction that RC env or M1-T4 **must use** `staging-host-cabinet` / `staging-host-hooks` as the working URL. Fix those before commit.

- [ ] **Step 9: Commit**

```bash
cd /opt/remnabot1
git add docs/superpowers/plans/2026-08-28-production-cutover-mvp.md .cursor/rules/10-remnabot-migration.mdc
git commit -m "$(cat <<'EOF'
docs(plan): RC public hostname is panel.rookari.com

EOF
)"
```

Do not `git add -A`. Do not push.

---

### Task 2: Align M1-T3 artifacts with live `.env` (no live `.env` edit)

- **ID:** REV-T2 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** REV-T1
- **GOAL:** `.env.rehearsal` / matrix / rehearsal compose CORS match the running RC public identity. Isolated docker DNS `rehearsal_rw` stays for the unstarted rehearsal stack only.
- **FILES:** Modify `docs/superpowers/evidence/2026-08-31-env-matrix.md`; Modify `docker-compose.rehearsal.yml`; Modify gitignored `.env.rehearsal` and `.env.rehearsal-rw` (do not commit env).

- [ ] **Step 1: Read live non-secret RC shapes (do not print secrets)**

```bash
python3 - <<'PY'
from pathlib import Path

def load(path):
    vals = {}
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, _, v = s.partition('=')
        vals[k.strip()] = v.strip().split('#')[0].strip().strip('"').strip("'")
    return vals

keys = [
    'BOT_RUN_MODE', 'WEBHOOK_URL', 'WEBHOOK_PATH', 'CABINET_URL',
    'CABINET_ALLOWED_ORIGINS', 'WEB_API_ALLOWED_ORIGINS', 'C2C_ENABLED',
    'REMNAWAVE_API_URL', 'MINIAPP_CUSTOM_URL', 'CABINET_ENABLED',
]
live = load('/opt/remnabot1/.env')
for k in keys:
    print(f'{k}={live.get(k, "ABSENT")}')
print('C2C_ADMIN_CHAT_ID_empty', live.get('C2C_ADMIN_CHAT_ID', 'ABSENT') == '')
rw = load('/opt/remnawave/.env')
for k in ('PANEL_DOMAIN', 'FRONT_END_DOMAIN', 'SUB_PUBLIC_DOMAIN'):
    print(f'RW {k}={rw.get(k, "ABSENT")}')
PY
```

Expected (must match; if not, **stop** with `PLAN REVISION REQUIRED: live .env public URLs changed`):

```
BOT_RUN_MODE=polling
WEBHOOK_URL=panel.rookari.com
WEBHOOK_PATH=/webhook
CABINET_URL=https://panel.rookari.com
CABINET_ALLOWED_ORIGINS=*
WEB_API_ALLOWED_ORIGINS=*
C2C_ENABLED=true
REMNAWAVE_API_URL=http://remnawave:3000
MINIAPP_CUSTOM_URL=panel.rookari.com
CABINET_ENABLED=true
C2C_ADMIN_CHAT_ID_empty True
RW PANEL_DOMAIN=rw.rookari.com
RW FRONT_END_DOMAIN=*
RW SUB_PUBLIC_DOMAIN=config.rookari.com/sub
```

- [ ] **Step 2: Patch gitignored `.env.rehearsal` public rows only**

Change these keys to the live shapes from Step 1:

- `BOT_RUN_MODE=polling`
- `WEBHOOK_URL=panel.rookari.com`
- `CABINET_URL=https://panel.rookari.com`
- `CABINET_ALLOWED_ORIGINS=*`
- `WEB_API_ALLOWED_ORIGINS=*`
- `MINIAPP_CUSTOM_URL=panel.rookari.com`
- `C2C_ENABLED=true`
- leave `C2C_ADMIN_CHAT_ID` unset or empty
- keep `WEBHOOK_PATH=/webhook`
- keep `REMNAWAVE_API_URL=http://rehearsal_rw:3000` (rehearsal compose network — **not** a copy of live `http://remnawave:3000`)
- keep `PRODUCTION_BOT_TOKEN_FINGERPRINT` and the existing test `BOT_TOKEN` (do not copy production token)
- keep `ALLOW_PRODUCTION_BOT_TOKEN=false`

Do **not** write `C2C_CARDS` values into git or chat. If you copy that key into the gitignored file, never print it.

Do **not** edit `/opt/remnabot1/.env`.

- [ ] **Step 3: Patch gitignored `.env.rehearsal-rw` hostnames**

Set (leave JWT values as already generated; do not regenerate unless missing; do not print them):

```
FRONT_END_DOMAIN=*
PANEL_DOMAIN=rw.rookari.com
SUB_PUBLIC_DOMAIN=config.rookari.com/sub
IS_TELEGRAM_NOTIFICATIONS_ENABLED=false
```

- [ ] **Step 4: Patch tracked `docker-compose.rehearsal.yml`**

Replace:

```yaml
      WEB_API_ALLOWED_ORIGINS: 'https://staging-host-cabinet.rookari.com'
```

with:

```yaml
      WEB_API_ALLOWED_ORIGINS: '*'
```

Replace:

```yaml
        VITE_TELEGRAM_BOT_USERNAME: rehearsal_placeholder_bot
```

with:

```yaml
        VITE_TELEGRAM_BOT_USERNAME: mrj7_bot
```

(`mrj7_bot` is the live test bot username already recorded in the M1-T3 matrix. Do not invent another.)

- [ ] **Step 5: Amend `docs/superpowers/evidence/2026-08-31-env-matrix.md`**

Update the classification table RC column for:

| Key | New RC (write this) |
|---|---|
| `WEBHOOK_URL` | `panel.rookari.com` |
| `CABINET_URL` | `https://panel.rookari.com` |
| `CABINET_ALLOWED_ORIGINS` | `*` |
| `WEB_API_ALLOWED_ORIGINS` | `*` |
| `MINIAPP_CUSTOM_URL` | `panel.rookari.com` |
| `C2C_ENABLED` | `true` (live `.env`; admin chat empty) |
| `FRONT_END_DOMAIN` | `*` (live RW) |
| `PANEL_DOMAIN` | `rw.rookari.com` |
| `SUB_PUBLIC_DOMAIN` | `config.rookari.com/sub` |

Rewrite the Verification outcomes list: drop “CORS not `*`” and “WEBHOOK_URL=staging-host-hooks…”. State operator binding: live `.env` is the RC public source; `staging-host-*` is not operational.

Keep fingerprint tables. Do not add secret values. Add a short “Revision 2026-08-31” note at the top pointing at this plan file.

- [ ] **Step 6: Verify (no compose up)**

```bash
cd /opt/remnabot1
python3 - <<'PY'
from pathlib import Path

def load(path):
    vals = {}
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, _, v = s.partition('=')
        vals[k.strip()] = v.strip().split('#')[0].strip().strip('"').strip("'")
    return vals

r = load('.env.rehearsal')
assert r['WEBHOOK_URL'] == 'panel.rookari.com', r.get('WEBHOOK_URL')
assert r['CABINET_URL'] == 'https://panel.rookari.com'
assert r['WEB_API_ALLOWED_ORIGINS'] == '*'
assert r['C2C_ENABLED'] == 'true'
assert r['REMNAWAVE_API_URL'] == 'http://rehearsal_rw:3000'
assert 'staging-host' not in r['WEBHOOK_URL']
assert 'staging-host' not in r['CABINET_URL']
assert r.get('ALLOW_PRODUCTION_BOT_TOKEN', 'false').lower() in ('false', '0', '')
rw = load('.env.rehearsal-rw')
assert rw['PANEL_DOMAIN'] == 'rw.rookari.com'
assert rw['FRONT_END_DOMAIN'] == '*'
assert rw['SUB_PUBLIC_DOMAIN'] == 'config.rookari.com/sub'
print('env assertions OK')
PY

docker compose -p rehearsal -f docker-compose.rehearsal.yml config >/dev/null
echo "bot config exit=$?"
docker compose -p rehearsal -f docker-compose.rehearsal.yml --profile bot-app config | grep -E 'WEB_API_ALLOWED_ORIGINS|CABINET_URL|WEBHOOK_URL|C2C_ENABLED|REMNAWAVE_API_URL|VITE_TELEGRAM_BOT_USERNAME'
docker compose -p rehearsal -f deploy/remnawave/docker-compose.rehearsal.yml --env-file .env.rehearsal-rw config >/dev/null
echo "rw config exit=$?"
```

Expected: assertions OK; both compose config exit 0; rendered bot-app shows `WEB_API_ALLOWED_ORIGINS: *` (or `"*"`), `C2C_ENABLED: "true"` or `true`, webhook/cabinet `panel.rookari.com`, `REMNAWAVE_API_URL` still `http://rehearsal_rw:3000`, Vite `mrj7_bot`. No `staging-host` in those grep lines.

Forbidden-volume grep must still be empty:

```bash
docker compose -p rehearsal -f docker-compose.rehearsal.yml config | grep -E 'remnawave-db-data|remnabot1_postgres|bot-remnawave' || echo "(none)"
```

- [ ] **Step 7: Confirm live `.env` and live Caddy were not modified**

```bash
cd /opt/remnabot1
git diff -- /opt/caddy/Caddyfile || true
# live .env is gitignored; confirm you did not open it for write this task
grep -n 'https://panel.rookari.com' /opt/caddy/Caddyfile | head
```

Expected: Caddy still has `https://panel.rookari.com`. No Caddy diff from this task.

- [ ] **Step 8: Commit tracked files only**

```bash
cd /opt/remnabot1
git add docs/superpowers/evidence/2026-08-31-env-matrix.md docker-compose.rehearsal.yml
git status
git commit -m "$(cat <<'EOF'
fix(M1-T3): align rehearsal public URLs with live .env

EOF
)"
```

Confirm `git status` does **not** stage `.env.rehearsal`, `.env.rehearsal-rw`, or `/opt/remnabot1/.env`. Do not push.

---

## Out of scope (do not do in this batch)

- M1-T4 Caddy authoring / `deploy/caddy/` / `caddy reload` / HTTP-01
- Changing live remnabot1 compose or `.env`
- Deleting Cloudflare `staging-host-*` A records
- Enabling webhook mode
- Inventing a P1 C2C admin chat
- Graft / restore / alembic
- Pinning Remnawave `backend:3` / `:latest` / `v3.4.2` as production identity

---

## Checkpoint

Both REV-T1 and REV-T2 committed on `prod-cutover`, not pushed. Live sandbox still serves `panel.rookari.com`. Next M1 work (Caddy single-source, M2 restore) waits for explicit user start and must not reintroduce `staging-host-*` as RC env URLs.
