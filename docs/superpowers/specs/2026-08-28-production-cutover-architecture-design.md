---
Recovered: 2026-08-29 from k4lantar4/remnabot origin/chore/mcp-dev-tools @ 70476c0e0a23657ce8959ffb76d0dfbebbd7e697
Topology/Alembic/cabinet paths superseded by:
  - docs/superpowers/specs/2026-08-28-production-cutover-architecture-errata.md
  - docs/superpowers/plans/2026-08-28-production-cutover-mvp.md
Do NOT follow §2.2, §7.2–7.3, or cabinet1 paths without errata.
---


# Design: Production Cutover Architecture A

Date: 2026-08-28  
Status: Locked (awaiting user review of this spec before `/writing-plans`)  
Scope: Evidence-based path from live production (`Bot` / `91.107.249.43`) to maintained trees on `bot-v4` / `91.107.144.95`

Supersedes `docs/superpowers/specs/2026-08-25-merge-runtime-bot-cabinet-mirror-design.md` for production migration, database, Telegram, Caddy, and cutover. That document remains historical evidence of an earlier merge-runtime attempt. It is **not** the production data or cutover plan.

This spec is implementation-ready. It does **not** authorize implementation, migrations, restores, DNS changes, or Caddy edits.

Evidence classes used throughout: **VERIFIED** (directly observed), **INFERRED** (logically derived), **UNKNOWN** (insufficient evidence).

---

## Goals

1. `/opt/remnabot1` becomes the maintained remnabot application tree.
2. `/opt/cabinet1` becomes the maintained cabinet tree.
3. Required donor 4.2 functionality is integrated as additive schema + code, without overwriting custom history.
4. Existing production functionality remains intact through rehearsal, then cutover.
5. Custom behavior (FA i18n, Toman, C2C, wholesale, cabinet1 panel) stays isolated from upstream via seams.
6. Alembic identity and Remnawave schema history remain coherent (no fake stamps, no donor-ID reuse).
7. Final live cutover is DNS-based, reversible, and evidence-gated.

## Non-goals

- Moving or swapping the production Primary IP.
- Creating or using a Floating IP.
- In-place upgrade of live `Bot`.
- Copying donor Alembic files `0088`–`0110` into remnabot1.
- Using current staging/donor databases as production migration sources.
- Putting production `BOT_TOKEN` into the RC before cutover.
- Introducing AAAA records.
- Migrating, relocating, or changing x-ui/xray on the old host.
- Blindly copying production `.env` or production Caddyfile.
- Treating Remnawave 3.3.2 as an irrevocable production pin before rehearsal gates pass.
- Live cutover execution (that is a later phase after the implementation plan and verification).

---

## 1. Current architecture

Two Hetzner Cloud servers in the same location (`nbg1-dc3`, `eu-central`). **VERIFIED** via instance metadata.

### 1.1 Production application host — `Bot` / `91.107.249.43`

| Component | Observed state | Class |
|---|---|---|
| Hostname | `Bot` | VERIFIED |
| IPv4 | `91.107.249.43` (Primary IP; DNS target) | VERIFIED |
| IPv6 | `2a01:4f8:1c1b:1aa6::1` present; **no AAAA** on app hostnames | VERIFIED |
| Bot | image `bot-remnawave-bot`, version **3.60.0**, webhook mode | VERIFIED |
| Bot DB | `postgres:15.18`, Alembic **0103**, **7828** users, `c2c_receipts` present | VERIFIED |
| Remnawave | `remnawave/backend:2.8.1`, PG **17.6**, **3180** users, `users.uuid` + `t_id` PK | VERIFIED |
| Cabinet | container `cabinet_frontend` on `:3020`, public `cabinet.rookari.com` | VERIFIED |
| Caddy | custom image with `dns.providers.cloudflare`; wildcard `*.rookari.com` | VERIFIED |
| Telegram | `BOT_RUN_MODE=webhook`, `WEBHOOK_URL=https://hooks.rookari.com`, `WEBHOOK_PATH=/webhook`, secret **set**, `WEBHOOK_IP` **absent** | VERIFIED |
| Payments | `payment_method_configs`: **only `c2c` enabled** | VERIFIED |
| Remnawave webhooks | `WEBHOOK_ENABLED=false` (placeholder URL) | VERIFIED |
| x-ui | host process `/usr/local/x-ui/x-ui`, listen `*:2096` and `*:2054` | VERIFIED |

Production public hostnames (Cloudflare A → `91.107.249.43`, TTL **300s**, DNS-only / grey cloud, no AAAA):

- `cabinet.rookari.com`
- `hooks.rookari.com`
- `master.rookari.com` (Remnawave `FRONT_END_DOMAIN` / `PANEL_DOMAIN`)
- `sub.rookari.com` (subscription page; `SUB_PUBLIC_DOMAIN=sub.rookari.com/sub`)
- `miniapp.rookari.com`
- `pgadmin.rookari.com` (operator; out of app cutover routing scope)

**VERIFIED** against `camilo.ns.cloudflare.com` and live HTTPS.

### 1.2 Release-candidate host today — `bot-v4` / `91.107.144.95`

This host is **not** a copy of production data.

| Component | Observed state | Class |
|---|---|---|
| Hostname | `bot-v4` | VERIFIED |
| IPv4 | `91.107.144.95` | VERIFIED |
| IPv6 | `2a01:4f8:1c1b:2a12::1`; no AAAA on app names | VERIFIED |
| Bot | `/opt/remnabot1`, container `remnawave_bot`, **different** Telegram token from production | VERIFIED (fingerprint inequality) |
| Bot DB | PG 15, Alembic **0106** stamped, **2 users**, donor lineage; remnabot1 tree **has no 0106 file** | VERIFIED |
| Remnawave | `remnawave/backend:3` reports **3.3.2**, PG **18.4**, **4 users**, `users.id` PK, no `uuid` | VERIFIED |
| Cabinet | `/opt/cabinet1` → `cabinet_frontend` | VERIFIED |
| Caddy | stock `caddy:2.9`, **no** Cloudflare DNS plugin | VERIFIED |
| Public names already here | `panel.rookari.com`, `rw.rookari.com`, `config.rookari.com`, `staging-host-*`, `admin.rookari.com` | VERIFIED |

`panel.rookari.com` is **not** a production hostname. Production cabinet is `cabinet.rookari.com`. `panel.rookari.com` is a historical merge URL on this host.

### 1.3 Authoritative vs non-authoritative data

| Source | Role |
|---|---|
| Live DBs on `Bot` | **Authoritative production data** |
| Fresh dumps taken from `Bot` under maintenance | **Cutover artifacts** (checksummed) |
| On-disk dumps (`old(3.60)_remnawave_bot.sql`, `old(2.8.1)_remnawave.sql`, `/opt/backups/*` dated Aug 10–11) | **Rehearsal inputs / evidence only**, not cutover artifacts |
| Current `bot-v4` PG volumes (`bot_postgres_data`, `remnabot1_postgres_data`, `remnawave-db-data`) | **Donor / wrong lineage — never restore onto these** |

### 1.4 Last shared bot revision

Alembic **0087** (`add_autopay_period_days_to_subscriptions`) is the last identical revision in remnabot1 and donor `/opt/bot`. **VERIFIED.**

From **0088** onward the numeric IDs are a parallel universe. Production live is remnabot1-lineage **0103**. Donor 4.2 HEAD is **0110**. Staging’s stamped **0106** is donor-lineage and is irrelevant to production.

---

## 2. Target architecture

### 2.1 Five identities (must not be conflated)

| Identity | During RC | After successful cutover |
|---|---|---|
| Release-candidate host | `bot-v4` / `91.107.144.95` | same machine |
| Production **application** host | still `Bot` | **`bot-v4`** |
| Production **network identity** (IPv4 users resolve) | `91.107.249.43` | `91.107.144.95` via Cloudflare A records |
| Production **data** | live DBs on `Bot` | restored+migrated copies on `bot-v4` (fresh cutover dumps) |
| Production **public hostnames** | still on `Bot` | same names, new A target |

The production Primary IP **does not move**. Rollback is DNS back to `91.107.249.43` plus starting the frozen 3.60 / 2.8.1 stacks.

### 2.2 Maintained trees

- `/opt/remnabot1` — application + Alembic (`0001`–`0104` preserved; new additive revisions `0111+`).
- `/opt/cabinet1` — cabinet frontend, split compose, `/api` via Caddy to bot.
- `/opt/remnawave` on `bot-v4` — Remnawave **rehearsal target 3.3.2**, promoted to production pin only after gates pass.
- Donors `/opt/bot` and `/opt/cabinet` — compare-only; never `docker compose up`.
- Live `/opt/remnabot` and `/opt/bot-remnawave` on `Bot` — frozen rollback images/config; not modified during RC work.

### 2.3 Locked cutover mechanism

Cloudflare DNS A-record cutover for production hostnames. TTL 300s. DNS-only (not proxied). IPv4 only. No Floating IP. No Primary IP reassignment.

---

## 3. Component topology

### 3.1 RC topology (non-production names only)

```text
                    Cloudflare (DNS-only)
                            |
            staging-host-cabinet.rookari.com
            staging-host-hooks.rookari.com
            staging-host-miniapp.rookari.com
            staging-host-master.rookari.com   (ADD)
            staging-host-sub.rookari.com
                            |
                     Caddy on bot-v4
                     (stock HTTP-01)
            /api/*  → rehearsal_bot:8080
            /webhook + payment paths → rehearsal_bot:8080
            cabinet UI → cabinet_frontend:80
            master → rehearsal_remnawave:3000
            sub → rehearsal_subscription_page:3010

        rehearsal_bot     (/opt/remnabot1, TEST Telegram token)
        rehearsal_bot_db  (NEW volume, PG 15, restored prod dump)
        rehearsal_rw      (3.3.2 after 2.8.1 restore+upgrade)
        rehearsal_rw_db   (NEW volume, PG 17.6 for restore)
        cabinet_frontend  (/opt/cabinet1)
```

Rehearsal **must not** use the currently running donor containers’ volumes (`remnawave-db-data`, current `remnawave_bot_db` data). Use a dedicated compose project (suggested name `rehearsal`) and dedicated container/volume names.

Existing donor Remnawave 3.3.2 (4 users) and donor bot DB (2 users / 0106) stay untouched as fossils until deliberately removed after RC isolation is standing. They are not inputs.

### 3.2 Production topology after cutover

Same processes on `bot-v4`, Caddy gains production server names, Cloudflare A records point at `91.107.144.95`.

```text
cabinet.rookari.com  → cabinet_frontend + /api → bot
hooks.rookari.com    → bot (Telegram /webhook + payment paths)
master.rookari.com   → remnawave:3000
sub.rookari.com      → remnawave-subscription-page
miniapp.rookari.com  → miniapp static + bot /miniapp
```

Old `Bot`: bot + Remnawave + cabinet **stopped**. Databases **preserved, not migrated in place**. x-ui **remains running**.

### 3.3 What stays on `Bot` forever in this design

- x-ui / xray (`:2096`, `:2054`)
- Frozen 3.60 / 2.8.1 application + DB as rollback
- Production Primary IP `91.107.249.43`

---

## 4. Production / staging / RC boundaries

| Boundary | Rule |
|---|---|
| Production Telegram token | Exists only on `Bot` until cutover step that starts the new bot. Never in RC compose `env_file`. |
| RC Telegram token | Existing separate test bot. Polling **or** webhook to `staging-host-hooks` only. |
| Production hostnames in Caddy on `bot-v4` | Absent until cutover. |
| RC hostnames | `staging-host-*` only (plus optional leftover `panel.rookari.com` as a non-production URL). |
| Production C2C admin chat | Never used by RC. |
| Payment provider production credentials | Never loaded by RC. Unused methods stay disabled. |
| Donor volumes | Never restore targets. |
| `/opt/remnabot` on `Bot` | Do not modify. |
| Implementation on donors `/opt/bot`, `/opt/cabinet` | Forbidden. |

`panel.rookari.com` may remain as a secondary RC URL because it is already on `bot-v4` and is not a production name. Designed RC cabinet URL is `staging-host-cabinet.rookari.com`. Do not add `cabinet.rookari.com` to this Caddy until cutover.

---

## 5. Database migration architecture

### 5.1 Isolation requirements

- New Docker volume names for every rehearsal restore.
- Suggested: `rehearsal_bot_pg15`, `rehearsal_rw_pg17`.
- Cutover uses **fresh** dumps. Either new volumes (`cutover_bot_pg15`, `cutover_rw_pg17`) or the rehearsal volumes **after** a snapshot, with contents replaced. Rehearsal dump contents must not become the live dataset.
- Postgres major versions:
  - Bot: restore **PG 15.18 dump → PG 15**. Do not jump bot PG major. **VERIFIED** dump is 15.18.
  - Remnawave: restore **PG 17.6 dump → PG 17.6**, verify under 2.8.1, then upgrade. Do **not** land the 2.8.1 dump straight onto PG 18.4. Whether 3.3.2 requires PG 18 is **UNKNOWN**; compose on this host uses `postgres:18.4`. Split app upgrade from PG major upgrade.

### 5.2 Dumps, not volume copies

Volume copy cannot cross PG 17 → 18. Dumps are reproducible and checksummable. Prefer `pg_dump` custom format (`-Fc`) plus a plain-SQL fallback if already used operationally. Record checksums (SHA-256) of dump files.

### 5.3 Two separate rehearsal tracks

| Track | Source | Restore into | First verify | Then |
|---|---|---|---|---|
| Bot | production `remnawave_bot` @ 0103 | PG 15 new volume | counts, C2C table, alembic 0103 | Alembic `0104` then `0111+` |
| Remnawave | production `remnawave` @ 2.8.1 | PG 17.6 new volume | counts, `users.uuid`, Prisma history | Image 3.3.2 + Prisma |

Tracks are parallel until bot `remnawave_id` backfill, which needs the rehearsed 3.x API.

### 5.4 Integrity checks after restore (before app migrate)

**Bot**

- `alembic_version = 0103`
- `count(users)` matches dump (production observed 7828)
- `to_regclass('public.c2c_receipts')` is not null
- `payment_method_configs` has `c2c` enabled
- No unexpected `0106` stamp

**Remnawave**

- `count(users)` matches dump (production observed 3180)
- `users.uuid` still present
- Prisma latest names match 2.8.1 lineage (production tail included `20260625200530_add_external_squad_index`)
- Panel login works on **non-production** hostname

### 5.5 Cutover dumps

Under maintenance: dump both DBs, checksum, restore onto the proven path, migrate, verify, then DNS. Dated Aug 10–11 backups and the `old(*)` SQL files are **not** cutover artifacts.

---

## 6. Remnawave migration architecture

### 6.1 Version pin

- **Rehearsal target:** `remnawave/backend:3.3.2` (what `bot-v4` already runs as `remnawave/backend:3`). **VERIFIED** installed version string `3.3.2`.
- **Production pin:** not irrevocable. Promote 3.3.2 to production target only if rehearsal gates pass against a copy of the real production DB.
- If gates fail: **PLAN REVISION REQUIRED** — choose another 3.x tag and re-rehearse. Do not invent a workaround on live data.

### 6.2 Schema transition (observed)

| 2.8.1 production | 3.3.2 on this host (donor DB, not prod data) |
|---|---|
| `users.uuid` unique | no `uuid` in `\d users` head |
| PK `users.t_id` | PK `users.id` |
| Bot talks UUID via API | Bot must talk numeric `id` |

**INFERRED:** Prisma migrations in 3.3.2 perform this transition on a 2.8.1 database. That inference is exactly what rehearsal must prove on production data.

### 6.3 Coupling to the bot

Donor revision `0104_remnawave_numeric_id` (semantic, not the file ID) adds nullable `remnawave_id` on `users`, `subscriptions`, and `grace_access_sessions` (if present), keeps `remnawave_uuid` as audit, relaxes grace `remnawave_uuid` to nullable. remnabot1 models today have `remnawave_uuid` only — **no `remnawave_id`**. **VERIFIED.**

Order:

1. Restore RW 2.8.1 copy and verify.
2. Upgrade that copy to 3.3.2; snapshot before/after.
3. Apply bot schema adding nullable `remnawave_id` (may occur before or after step 2; columns are nullable).
4. **Backfill `remnawave_id` only after** the rehearsed panel is 3.x and the API returns numeric ids.
5. Production bot 3.60 and production panel 2.8.1 cut over **in one window**. Do not leave 3.60 talking to 3.x, or v4 bot talking to 2.8.1, in production.

### 6.4 Rollback of Remnawave

Do **not** downgrade a migrated 3.x database in place. Rollback = DNS to old host + start frozen 2.8.1. Keep the 2.8.1 dump and the untouched old PG 17 volume on `Bot`.

### 6.5 Rehearsal gates for 3.3.2 (promotion condition)

All must be **VERIFIED** on the restored production copy:

- Schema: `users` identity is numeric; historical mapping from old `uuid` is reconstructible (uuid retained somewhere, or a documented mapping table/column).
- User count and a sample of usernames/telegram_ids survive.
- Subscription / squad / HWID relationships still join.
- Panel login on RC hostname.
- Subscription links on RC sub hostname fetch a config for a known user.
- Bot (test token, rehearsed DB) can read/update a panel user via numeric id after backfill.
- No silent mass expiry / revoke.

If uuid is dropped without a mapping, that is a **release blocker** until mapping is proven.

---

## 7. Bot Alembic architecture

### 7.1 Invalidated strategy

`0088–0106 → 0107–0125` is **discarded**. It assumed remnabot1 IDs could be renamed onto donor history. Production **0103** is `subscription_user_disabled`; donor **0103** is `add_legal_consents`. Staging **0106** is a donor stamp without a remnabot1 file. Never `alembic stamp` to hide that.

### 7.2 Preserved graph

```text
0001 … 0087     shared with donor (0087 last identical)
0088            c2c_receipts                          CUSTOM
0089            dedupe_tariff_subscriptions           (= donor 0088 semantically)
0090            wheel_spins.telegram_charge_id        (= donor 0089)
0091            multi_account / account_sequence      CUSTOM
0092            subscription.panel_username           CUSTOM
0093            wholesale_discount_bps, business_role CUSTOM
0094            c2c_receipt enhancements              CUSTOM
0095            partner panel fields                  CUSTOM
0096            merge heads 0094+0095                 CUSTOM
0097            payment_method_configs.quick_amounts  (= donor 0090)
0098            info_pages.display_mode               (= donor 0091)
0099            vk/yandex email_verified backfill     (= donor 0092)
0100            yclid                                 (= donor 0093)
0101            subscription_public_serial_seq        CUSTOM
0102            broadcast/pinned entities_json        CUSTOM
0103            subscriptions.user_disabled           CUSTOM  ← PRODUCTION HEAD
0104            traffic_purchases expiry clamp        CUSTOM  ← remnabot1 HEAD, not on prod yet
```

Keep these files. Do not renumber them. Do not import donor files that reuse these IDs.

### 7.3 Donor IDs 0088–0110

Do **not** copy those files. Do **not** reuse those revision IDs. IDs `0105`–`0110` stay unused in remnabot1 so a later accidental copy cannot collide silently.

### 7.4 Planned new revision space (`0111+`)

IDs below are **planned labels for the implementation plan**, not authorization to write migration files. The plan may bundle or split after column-level verification against a restored 0104 schema. All new revisions: `down_revision` chain from `0104`; inspector-guarded; additive; no drops of custom columns.

### 7.5 Complete migration mapping

**Already present in remnabot1 (do not re-apply as new history)**

| Donor rev | Semantic | Local equivalent | Action |
|---|---|---|---|
| 0088 | dedupe tariff subscriptions (no-op) | 0089 | none |
| 0089 | wheel_spins.telegram_charge_id | 0090 | none |
| 0090 | payment_method_configs.quick_amounts | 0097 | none |
| 0091 | info_pages.display_mode | 0098 | none |
| 0092 | vk/yandex email_verified backfill | 0099 | none |
| 0093 | yclid | 0100 | none |

**Custom local-only (protect; never drop)**

| Local rev | Schema / feature | Protect |
|---|---|---|
| 0088, 0094 | `c2c_receipts` and enhancements | C2C |
| 0091 | `subscriptions.account_sequence` | multi-account |
| 0092 | `subscriptions.panel_username` | partner/panel |
| 0093 | `users.wholesale_discount_bps`, `users.business_role` | wholesale |
| 0095 | `purchase_note`, `panel_brand_prefix` | partner |
| 0101 | `subscription_public_serial_seq` | serials |
| 0102 | `entities_json` on broadcasts/pins | broadcasts |
| 0103 | `subscriptions.user_disabled` | admin disable |
| 0104 | traffic_purchases expiry clamp (data fix) | partner traffic bugfix |

**Required new additive revisions (schema/semantic delta vs donor 4.2 HEAD)**

| Planned ID | Source donor rev | Semantic | Depends on | Resulting schema | Notes |
|---|---|---|---|---|---|
| 0111 | 0104 | nullable `remnawave_id` on `users`, `subscriptions`; unique indexes; if `grace_access_sessions` exists, add `remnawave_id` and relax `remnawave_uuid` nullability | 0104; RW 3.x for **backfill**, not for DDL | numeric identity columns beside retained `remnawave_uuid` | Highest coupling. remnabot1 has no `remnawave_id` today. Inspector-guard grace table. |
| 0112 | 0094 | `payment_method_configs.description` | 0104 | nullable Text | Local model has no this column. |
| 0113 | 0095 | tables `coupon_batches`, `coupons` | 0104 | coupon schema | Unused in production payments; schema only until product enables it. |
| 0114 | 0096 | table `recurrent_payments` | 0104 | recurrent schema | |
| 0115 | 0097 | table `grace_access_sessions` + subscription grace columns | 0104 | grace overlay | Create with nullable `remnawave_uuid` and `remnawave_id` so 0111 does not have to retrofit. |
| 0116 | 0098 | table `cispay_payments` | 0104 | cispay schema | Do not enable with production secrets. |
| 0117 | 0099+0100 | `platega_subscriptions` + alive unique index | 0104 | platega recurrent | Production `platega` method is disabled. |
| 0118 | 0101 | `lava_subscriptions` + `tariffs.lava_product_id` | 0104 | lava recurrent | |
| 0119 | 0102 | `coupon_batches.max_per_user` | 0113 | column | |
| 0120 | 0103 | table `legal_consents` | 0104 | cabinet legal log | |
| 0121 | 0105 | `promocodes.traffic_gb` | 0104 | int not null default 0 | |
| 0122 | 0106 | `guest_purchases.campaign_slug` | 0104 | nullable string | |
| 0123 | 0107 | `guest_purchases.idempotency_key` + unique index | 0122 or 0104 | financial idempotency | |
| 0124 | 0108 | `referral_reward_levels` + extra `referral_earnings` columns | 0104 | referral v2 | |
| 0125 | 0109 | `required_referrals*` on levels | 0124 | thresholds | |
| 0126 | 0110 | `users.referral_days_subscription_id`, `referral_reward_preference` | 0124 | user choice | |

**Application work that is not an Alembic revision**

- Backfill `remnawave_id` from Remnawave 3.x API after 0111 DDL and panel upgrade.
- Port donor 4.2 **code** for coupons/grace/cispay/etc. behind seams; enabling a payment method is a separate product decision.
- Do not enable YooKassa / Platega / CryptoBot / CisPay / Lava against production credentials on RC.

Column-level verification (restored 0104 schema vs donor 0110 models) is an **implementation-plan evidence task**. If that diff finds extra/missing columns, update this mapping before writing files.

### 7.6 Apply order on a restored production bot DB

```text
restore dump → alembic_version=0103
→ upgrade 0104 (traffic clamp)
→ upgrade 0111+ (planned chain)
→ remnawave_id backfill (after RW 3.x)
```

Never stamp. If upgrade fails, fix the revision; do not skip.

---

## 8. Environment reconciliation model

Production `.env` is the **behavioral reference**, not a file to copy blindly. Never print secret values in this spec, plans, commits, or logs.

### 8.1 Classes

**A — Must preserve (behavior)**

Language/currency/Toman, tariff prices and periods, feature flags that define the product, `WEBHOOK_PATH=/webhook`, `REMNAWAVE_AUTH_TYPE=api_key`, C2C copy/limits (not the admin chat id), wholesale/partner flags, `CABINET_ENABLED`, `DEFAULT_LANGUAGE=fa`, `MULTI_TARIFF_ENABLED`, traffic packages.

**B — RC-specific override**

| Variable | RC value shape |
|---|---|
| `BOT_TOKEN` | existing **test** token only |
| `BOT_RUN_MODE` | `polling` or `webhook` |
| `WEBHOOK_URL` | `https://staging-host-hooks.rookari.com` if webhook; never production hooks URL |
| `WEBHOOK_SECRET_TOKEN` | RC-only secret, or empty if polling |
| `CABINET_URL` | `https://staging-host-cabinet.rookari.com` |
| `WEB_API_ALLOWED_ORIGINS` | RC origins only |
| `C2C_ENABLED` | `true` only with isolated test admin chat; else `false` |
| `C2C_ADMIN_CHAT_ID` | test chat or unset |
| Remnawave `FRONT_END_DOMAIN` / `PANEL_DOMAIN` | RC master hostname |
| Remnawave `SUB_PUBLIC_DOMAIN` | RC sub hostname + path |
| `IS_TELEGRAM_NOTIFICATIONS_ENABLED` | false, or true only with **non-production** RW Telegram token (staging RW token already ≠ prod) |
| `REMNAWAVE_API_URL` | docker-internal to **rehearsal** panel, not production |

**C — Generated for RC**

Passwords for new PG volumes; RC `CABINET_JWT_SECRET` (do not reuse production JWT on an internet-exposed RC); RC webhook secret if webhook mode.

**D — Production-only secrets (cutover, not RC compose)**

Production `BOT_TOKEN`, production `WEBHOOK_SECRET_TOKEN`, production `CABINET_JWT_SECRET`, `REMNAWAVE_API_KEY`, Remnawave `JWT_*`, DB passwords of **live** `Bot` (needed to dump, not to start RC), Caddy/pgAdmin prod passwords, Cloudflare token if used for DNS-01 later.

Store D in a cutover secret file that is **not** referenced by RC `env_file`. Load only at the cutover start-new-bot step.

**E — Must never enter RC**

Production `BOT_TOKEN` before cutover; production webhook URL while RC is running; production `C2C_ADMIN_CHAT_ID`; production payment provider API tokens/secrets; production Remnawave Telegram token.

### 8.2 Cabinet frontend

`VITE_API_URL=/api` (relative) remains. Caddy chooses the host. `VITE_TELEGRAM_BOT_USERNAME` on RC is the **test** bot username. Production username is a cutover rebuild or runtime config of cabinet1.

### 8.3 Enforcement

RC compose must fail closed: if `BOT_TOKEN` fingerprint equals the known production fingerprint, refuse to start. Implementation plan will specify the check; this spec requires it.

---

## 9. Caddy / HTTP / DNS architecture

### 9.1 DNS (locked)

- Authoritative: Cloudflare (`camilo` / `lola`). **VERIFIED.**
- Production app records: A only, TTL 300, DNS-only, target `91.107.249.43` today.
- Cutover: change those A records to `91.107.144.95`.
- No AAAA.
- No proxy (orange cloud) as part of this migration.
- No Primary IP / Floating IP change.

Hostnames that **move**: `cabinet`, `hooks`, `master`, `sub`, `miniapp` (optional `pgadmin` — out of app routing scope unless later decided).

Hostnames that **must not** be treated as production cutover: `panel`, `rw`, `config`, `staging-host-*`, `admin*`, apex `rookari.com`.

### 9.2 RC Caddy (now)

Derive **minimal** routes; do not copy production Caddyfile (it contains pgadmin basic-auth, remnawave-admin, leftover staging-host blocks pointing at containers that do not exist on `Bot`, youtube redirect, wildcard DNS-01).

| RC hostname | Route |
|---|---|
| `staging-host-cabinet.rookari.com` | `/api/*` strip → bot; else cabinet |
| `staging-host-hooks.rookari.com` | all → bot (webhook + future payment paths) |
| `staging-host-miniapp.rookari.com` | `/miniapp/*` + `app-config.json` → bot; else miniapp static |
| `staging-host-master.rookari.com` | → rehearsal Remnawave `:3000` |
| `staging-host-sub.rookari.com` | → rehearsal subscription page |

TLS: HTTP-01 on stock Caddy. Sufficient because Cloudflare is grey-cloud. **INFERRED** from existing `panel.rookari.com` cert on this host.

Do not add production names until cutover.

### 9.3 Cutover Caddy

Add five production server blocks equivalent to:

| Name | Route |
|---|---|
| `cabinet.rookari.com` | `/api/*` → bot; else cabinet |
| `hooks.rookari.com` | → bot (include `/webhook` and existing payment path handles) |
| `master.rookari.com` | → remnawave `:3000` |
| `sub.rookari.com` | subscription page; preserve production root redirect behavior if still required |
| `miniapp.rookari.com` | miniapp static + bot `/miniapp` |

Then flip DNS. HTTP-01 issues after the A record points here (or shortly before if the name already answers here — it will not, until the flip).

Wildcard DNS-01 is **not** required if each name has a site block. Staging Caddy lacks the Cloudflare plugin. **VERIFIED.**

SNI: new host must serve the exact production names. **VERIFIED** need.

### 9.4 Telegram vs DNS

Webhook URL is hostname-based. Telegram does not need re-registration **because of DNS**. Re-`setWebhook` is optional after cutover to reset Telegram’s TLS session, and **only** with the production token on the new bot after the old bot is stopped.

`WEBHOOK_IP` stays unset so Telegram keeps following DNS. Do not set `WEBHOOK_IP` to either server.

---

## 10. Telegram isolation

### 10.1 RC

- Existing separate test token only. **VERIFIED** distinct from production.
- Never call `setWebhook`, `deleteWebhook`, or other webhook-mutating Bot API methods with the production token.
- Do not run `getUpdates` (polling) on the production token from RC.
- RC webhook, if used, only `https://staging-host-hooks.rookari.com` + `/webhook`.
- BotFather domain allowlist for the **test** bot includes RC cabinet host.

### 10.2 Cutover sequence (Telegram)

1. Stop production bot (releases the webhook consumer on `Bot`).
2. Switch application/runtime on `bot-v4` to production secrets + production webhook URL (Caddy already serving `hooks.rookari.com` or about to, DNS flipped or flipping).
3. Start **one** new bot process with production token.
4. Verify `getWebhookInfo` shows `https://hooks.rookari.com/webhook`.
5. Optionally `setWebhook` to the same URL if info is stale or Telegram still posts to a dead connection.

Never two production-token processes at once.

Startup code in remnabot1 **always** `setWebhook` when `BOT_RUN_MODE=webhook`. **VERIFIED.** Therefore the new process must not be started with the production token until step 3.

### 10.3 Remnawave Telegram notifications

Production RW `TELEGRAM_BOT_TOKEN` ≠ staging RW token. **VERIFIED.** RC rehearsal panel must not use the production RW token. Production RW `IS_TELEGRAM_NOTIFICATIONS_ENABLED=true` — a second panel with that token would dual-notify.

---

## 11. C2C isolation

C2C is Telegram-admin, not an HTTP callback. Production enabled method is **only C2C**. **VERIFIED.**

RC may enable C2C **only if all** of:

- test Telegram bot (not production token)
- `C2C_ADMIN_CHAT_ID` is a **test** chat, never the production admin chat
- restored production `c2c_receipts` data is allowed (historical rows)

If a truly isolated test admin chat cannot be established: `C2C_ENABLED=false` and mark verification **C2C INCOMPLETE**. Do not fake PASS. Do not post RC receipts into the production admin chat.

Protected columns/tables: `c2c_receipts` and related 0088/0094 fields. Donor migrations must not drop them.

---

## 12. Rollback architecture

Old host is a **rollback target**, not a second live application after cutover.

After cutover:

- Old bot **stopped**
- Old Remnawave **stopped**
- Old production DBs **preserved and untouched**
- x-ui/xray **remain active** (independent)

Rollback procedure:

1. Stop the new application on `bot-v4` (releases production Telegram token).
2. Restore Cloudflare A records to `91.107.249.43`.
3. Start frozen 3.60 / 2.8.1 stacks on `Bot`.
4. Verify/restore Telegram webhook to `https://hooks.rookari.com/webhook` if needed.
5. Verify cabinet, sub, panel, C2C.

Do **not** in-place downgrade Remnawave 3.x or Alembic `0111+`. DNS + frozen old stacks are the rollback.

TTL 300s is the DNS convergence window. Telegram resolver cache beyond that is **UNKNOWN**; optional `setWebhook` on the restored old bot mitigates stuck connections.

---

## 13. Cutover sequence

High-level only (implementation plan will expand). Order is a safety constraint.

1. RC isolation standing (test token, non-prod Caddy, new volumes).
2. Bot restore rehearsal + `0104` + planned `0111+` on copy.
3. Remnawave 2.8.1 restore rehearsal + 3.3.2 upgrade on copy.
4. `remnawave_id` backfill against rehearsed 3.x.
5. Cabinet1 + protected-behavior smoke on RC names (FA, Toman, wholesale, C2C-if-isolated, panel).
6. If 3.3.2 gates fail: stop, revise RW target, do not cut over.
7. Maintenance: stop accepting new production writes as needed; dump bot + RW; checksum.
8. Restore fresh dumps onto proven path; migrate; verify on `bot-v4` **before** DNS (using hosts-file / extra-name test, or verify internally). Production Caddy names added on `bot-v4`.
9. Stop production bot (and production RW once data is copied and old writes must cease).
10. Flip Cloudflare A records.
11. Start **one** new bot with production token + `https://hooks.rookari.com/webhook`.
12. Verify webhook, cabinet, sub, master, C2C, FA.
13. Leave `Bot` apps stopped, DBs intact, x-ui running.

Step 8–11 is the production window. Target: minutes dominated by TTL 300s + migrate time on 7828/3180-row databases (**UNKNOWN** wall-clock until rehearsal measures it).

---

## 14. Verification gates

A gate is PASS only with evidence (command output, counts, screenshot/HTTP status as appropriate). “Build succeeded” is not PASS.

| Gate | When | Must show |
|---|---|---|
| G1 Restore bot | After rehearsal restore | 0103, user count, C2C table |
| G2 Restore RW | After rehearsal restore | 2.8.1 schema, user count, uuid |
| G3 RW 3.3.2 | After upgrade copy | numeric identity, mapping, login, sub link, no mass revoke |
| G4 Bot 0104 | After clamp migration | alembic 0104, traffic_purchases invariant |
| G5 Bot 0111+ | After new revisions | expected tables/columns; C2C/wholesale columns still present |
| G6 Backfill | After 3.x + 0111 | sample `remnawave_id` matches panel `users.id` |
| G7 Telegram RC | Continuous | production `getWebhookInfo` still production URL; RC uses test token |
| G8 C2C | RC | isolated chat works **or** explicit INCOMPLETE |
| G9 Cabinet | RC | `staging-host-cabinet` login/API; FA strings; Toman display |
| G10 Wholesale | RC | protected pricing path |
| G11 Cutover Telegram | After start new bot | webhook URL + secret path live; single consumer |
| G12 Cutover HTTP | After DNS | cabinet/hooks/master/sub/miniapp 200/expected on new IP |
| G13 Rollback drill | Before cutover window | documented dry-run of DNS revert + old stack start **without** executing live revert |

G13 may be a tabletop + command rehearsal (`docker compose start` on `Bot` while still live is **not** done). Prefer verifying compose files and dump restore locally on RC.

---

## 15. Failure modes

| Failure | Detection | Response |
|---|---|---|
| RC process uses production token | fingerprint check / webhook theft | stop RC immediately; restore webhook on `Bot` |
| Two production bots | duplicate `setWebhook` / polling conflict | stop newer; verify webhook |
| Restore onto donor volume | user count 2 or alembic 0106 | abort; use new volumes |
| Alembic ID collision | startup `Can't locate revision` | never stamp; fix graph |
| RW 3.3.2 loses uuid mapping | gate G3 | do not promote 3.3.2; revise version |
| C2C posts to prod admin chat | wrong `C2C_ADMIN_CHAT_ID` | disable C2C; treat as incident |
| Payment provider hits RC | production secrets on RC + DNS still prod | should not happen if secrets omitted; if enabled, disable method |
| TLS fail after DNS | HTTP-01 / SNI | wait TTL; check Caddy; rollback DNS if prolonged |
| Split-brain TTL | both IPs serve same name | old app **stopped** so old IP should fail closed for bot; RW old stopped |
| Remnawave 3.x data corruption | G3 | rollback DNS; never downgrade 3.x DB |
| x-ui mistaken as in-scope | process killed | out of scope; do not touch |

---

## 16. Security constraints

- No secret values in git, chat, STATE.md, specs, plans, or logs. Fingerprints (short SHA-256) allowed.
- RC env_file must not contain class D/E secrets.
- Production JWT must not validate on a public RC hostname (generate RC JWT).
- YooKassa IP allowlist and other provider auth are **not** a substitute for keeping production payment secrets off RC.
- Cloudflare remains DNS-only; do not flip to proxied as a silent part of cutover (would change client IPs seen by YooKassa allowlist if that method is later enabled).
- pgadmin / remnawave-admin / unrelated vhosts stay out of this Caddy derivation unless a later decision includes them.
- Do not expose production DB ports on `0.0.0.0` on `bot-v4`.

---

## 17. Explicit assumptions

1. Cloudflare A-record edits are operationally available at cutover (human or API). Not verified as an API token on these hosts for DNS writes. **DNS write access is UNKNOWN; DNS read is VERIFIED.**
2. Telegram re-resolves `hooks.rookari.com` within a small multiple of 300s. Extra cache is UNKNOWN; optional `setWebhook` is the mitigation.
3. Subscription node IPs are **not** this app host; moving `sub.rookari.com` does not move x-ui. **INFERRED** from x-ui staying in scope-out and Remnawave managing nodes.
4. Production C2C is the only live payment method that can affect real money/admin attention during RC.
5. Donor 4.2 schema delta listed in §7.5 is complete at **revision-file** granularity. Column-level leftover drift is an implementation evidence task.
6. `bot-v4` remains the intended long-term app host (capacity/disk **UNKNOWN** as a formal sizing study; both hosts already run similar stacks).
7. Cabinet1 `/api` reverse-proxy pattern stays; no cabinet-on-bot embed.
8. Historical spec 2026-08-25 “fresh DB / copy donor env” is false for production and is superseded.

---

## 18. Remaining UNKNOWN items

1. Telegram DNS/connection cache beyond Cloudflare TTL 300s.
2. Whether Remnawave 3.3.2 **requires** Postgres 18 vs merely shipping `postgres:18.4` in compose.
3. Prisma 2.8.1 → 3.3.2 behavior on **this** 3180-user database (must be rehearsed).
4. Whether 3.3.2 retains a reconstructible uuid mapping.
5. Wall-clock for dump/restore/migrate of production-sized DBs.
6. Cloudflare DNS **write** credential location (read is public).
7. Where production Caddy’s Cloudflare DNS-01 token lives (`CF_API_TOKEN` not in Caddy `.env` keys); irrelevant if HTTP-01 is used.
8. Whether anything public depends on x-ui `:2096`/`:2054`.
9. Exact `WEB_API_ALLOWED_ORIGINS` production value (length 1; not printed).
10. Column-level schema residual after applying §7.5 (models vs restored 0104).
11. Test C2C admin chat availability (human decision at execution).
12. Hetzner Primary IP reassignability — unused under architecture A.

---

## 19. Decisions that still require evidence during implementation

These are **not** re-opened architecture questions. They are evidence gates that may force a **plan revision**, not a silent workaround.

| ID | Question | If evidence fails |
|---|---|---|
| E1 | Does 3.3.2 upgrade of the real RW dump preserve identity and subs? | Choose another 3.x; re-rehearse; do not cut over |
| E2 | PG 17 vs 18 for 3.3.2 | Stay on 17 if app works; only then consider PG 18 as a **separate** track |
| E3 | Column-level Alembic delta vs §7.5 | Update mapping; do not copy donor files |
| E4 | Isolated C2C test chat | Disable C2C on RC; mark G8 INCOMPLETE |
| E5 | Dump/restore duration | Size the maintenance window; do not skip checksums |
| E6 | HTTP-01 after DNS flip for five names | Fix Caddy; rollback DNS if certs fail beyond TTL |
| E7 | `remnawave_id` backfill coverage | Block cutover until sample+count gates pass |
| E8 | Cabinet Telegram widget with test bot | Fix BotFather domain / username; not a reason to use production token |

---

## Consistency review (pre-final)

Checked for contradictions before locking this text:

| Topic | Resolution |
|---|---|
| Database vs cutover | Rehearsal dumps ≠ cutover dumps. New volumes. Old `Bot` DB never mutated. |
| Telegram vs Caddy vs DNS | RC never serves `hooks.rookari.com`. Production webhook hostname moves only at DNS flip **after** old bot stop **and** new Caddy names. Production token only in the new process. |
| Rollback vs Remnawave 3.x | Rollback is DNS + frozen 2.8.1, not Prisma downgrade. |
| Rollback vs Alembic | Rollback does not downgrade `0111+` on the new DB; old 0103 DB is the rollback dataset. |
| 3.3.2 pin | Rehearsal target, not irrevocable production pin. Matches E1. |
| Alembic | Preserve `0001–0104`; no donor ID reuse; `0111+` planned labels only. |
| C2C | Isolated or explicitly incomplete; never production admin chat. |
| IPv6 | No AAAA; both hosts have unused v6. |
| x-ui | Stays on `Bot`; not in Caddy derivation. |
| Floating IP / Primary IP | Not used; DNS only. |
| Old 2026-08-25 spec | Fresh DB / copy donor env / panel.rookari.com as the production surface — **superseded**. |

No remaining internal contradiction identified among the locked strategies.

---

## Next step

User reviews this spec. After approval, invoke `/writing-plans` to produce the implementation plan. Do not implement from this document alone.
