# Production Cutover MVP Implementation Plan (Topology Revision)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. Code tasks use TDD; operational tasks use evidence gates. "Container started" / "build passed" is **never** a PASS.
>
> **Do not execute M0 or any later task from this document until the user explicitly starts execution.**
>
> **Revision 2026-08-29 (topology):** The previous plan assumed `/opt/remnabot1` was the custom 3.60 tree and `/opt/cabinet1` was the cabinet working tree. That topology is **obsolete**. Verified live trees invert the code strategy: `/opt/remnabot1` is now a **fresh 4.2 upstream fork**; custom production behavior lives in `/opt/remnabot`; cabinet is the **separate** repo `/opt/cabinet` (`k4lantar4/cabinet`). Several names in the incoming English brief (`k4lantar4/cabinet1`, `/opt/cabinet1`, remnabot1 origin = `k4lantar4/remnabot`) are **disproven** and must not be used.
>
> **Revision 2026-08-29 (plan review):** External review of this document (not of application code). Critical findings verified on disk and absorbed here: (1) M1 is inlined — there is no prior MVP plan on disk; (2) Architecture A is recovered only with a **binding errata** (plan is Alembic/topology authority after inversion); (3) Alembic graft is lineage-correct but not a drop-in — auto-upgrade / leftover `0105–0110` / `0001` create_all / 4.2 tests are explicit hazards; (4) DAG forbids starting remnabot1 against a restored volume before M4-T0. M5–M9 restored to executable tasks with `/opt/cabinet` substitutions. **Still do not execute.**

**Goal:** Produce a production-usable New-Version MVP: maintained bot at `/opt/remnabot1` (4.2 code + ported custom behavior) + separate cabinet at `/opt/cabinet` + a **verified immutable** Remnawave 3.x revision, rehearsed on production-lineage data, cut over by DNS, with rollback to frozen 3.60/2.8.1.

**Architecture:** Start from the clean 4.2 fork (`/opt/remnabot1`). Port only MVP-required custom behavior from `/opt/remnabot` (C2C, FA, Toman, wholesale/partner, production identity columns). Keep Cabinet as an independent application behind the API. Rehearse Remnawave 2.8.1 → a concrete 3.x **candidate** (currently 3.3.2 is the latest GitHub release and the local staging image — **not** a permanent pin). Production DB stays on the **remnabot Alembic lineage** (`0103`/`0104`); do not apply remnabot1's upstream `0088–0110` files onto that database. Cutover freezes writers, dumps, restores, verifies pre-DNS, then flips A records.

**Tech Stack:** Python 3.12 / aiogram, SQLAlchemy + Alembic, PostgreSQL 15 (bot) and 17.6 (Remnawave restore), Remnawave panel (rehearsal candidate, then immutable digest), Vite/React cabinet, Caddy 2.9 at `/opt/caddy`, Docker Compose, Cloudflare DNS-only.

**Spec:** Architecture A remains authoritative for cutover/DNS/Telegram/C2C isolation/rollback **except where the locked errata below overrides it**. Recover the spec from `k4lantar4/remnabot` `origin/chore/mcp-dev-tools` (`70476c0e`, path `docs/superpowers/specs/2026-08-28-production-cutover-architecture-design.md`). **Do not treat the recovered spec as Alembic or cabinet-path authority.** Executors read: **this plan + errata**, then the spec for DNS/Telegram/C2C/rollback/gates.

---

## Six identities (do not conflate)

| # | Identity | Verified tree / remote | Role |
|---|---|---|---|
| 1 | **Production reference** | `/opt/remnabot` (`origin` = `k4lantar4/remnabot`, HEAD `f36ec4ca`, CHANGELOG **3.60.0**); embedded `/opt/remnabot/cabinet` (cabinet-frontend **1.57.0**, not a separate git repo); production `/opt/bot-remnawave` **absent on this host** | READ-ONLY. Inspect production code/config/history/topology. Rollback reference. **Never** the working source; **never** modify during RC |
| 2 | **Maintained repository (bot)** | `/opt/remnabot1` · `origin` = `https://github.com/k4lantar4/remnabot1.git` · HEAD `89fa7dc5` = **4.2.0** · branch `main` | Final custom bot **code** authority after ports. Own Git history and release lifecycle |
| 3 | **Upstream repository (bot)** | `BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot` | Official bot upstream. Moving target. Fetch/compare only |
| 4 | **Upstream working tree (bot)** | `/opt/bot` · `origin` = official upstream · HEAD **identical** to remnabot1 `89fa7dc5` · dirty: `docker-compose.yml` only | Local read-only clone of upstream. **Not** canonical. Never `compose up`, never restore, never implement here |
| 5 | **RC runtime** | `bot-v4` / `91.107.144.95` · rehearsal compose + new volumes · test Telegram token · `staging-host-*` | Isolated rehearsal |
| 6 | **Production runtime (today)** | `Bot` / `91.107.249.43` · frozen 3.60 / 2.8.1 after cutover | Live until cutover; then rollback target |

**Cabinet (separate maintained application):**

| Identity | Verified | Role |
|---|---|---|
| Maintained cabinet repo + tree | `/opt/cabinet` · `origin` = `https://github.com/k4lantar4/cabinet.git` · `upstream` = `https://github.com/BEDOLAGA-DEV/bedolaga-cabinet.git` · HEAD `35e5aa9e` = **1.67.0** · `main` 0/0 vs origin **and** upstream | Independent app. Talks to bot via `/api`. **Do not** merge into remnabot1 |
| Official cabinet upstream | `BEDOLAGA-DEV/bedolaga-cabinet` | Moving target |
| Legacy production cabinet | `/opt/remnabot/cabinet` (1.57.0, embedded in remnabot git) | READ-ONLY production topology |

**Remnawave runtime (not a git repo):** `/opt/remnawave` (panel compose `remnawave/backend:3`) + `/opt/remnawave/subscription` (`remnawave/subscription-page:latest`). Authorized infrastructure only.

**Caddy:** `/opt/caddy` (stock `caddy:2.9`). Authorized infrastructure. Single source of truth will live under remnabot1 `deploy/caddy/`.

---

## Claim verification (English brief vs user notes vs disk)

| Claim | Verdict | Evidence |
|---|---|---|
| `/opt/bot` is upstream clone | **CONFIRMED** (user notes) | `origin` = `BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot`; HEAD = remnabot1 |
| `/opt/remnabot` is remnabot origin clone | **CONFIRMED** | `origin` = `k4lantar4/remnabot`; 3.60.0; has embedded `cabinet/` |
| `/opt/cabinet` is fresh upstream fork | **CONFIRMED** | origin `k4lantar4/cabinet` + upstream `bedolaga-cabinet`; HEAD = upstream `main` |
| `/opt/remnabot1` is fresh upstream fork | **CONFIRMED** | origin `k4lantar4/remnabot1`; upstream official bot; HEAD = 4.2.0 = `/opt/bot` |
| `/opt/remnawave` is panel + subscription | **CONFIRMED** | compose + `subscription/` |
| Maintained cabinet = `k4lantar4/cabinet1` + `/opt/cabinet1` | **FALSE** | `/opt/cabinet1` **MISSING**; `git ls-remote https://github.com/k4lantar4/cabinet1.git` → **Repository not found** |
| remnabot1 `origin` should be `k4lantar4/remnabot` | **FALSE** | remnabot1 `origin` = `k4lantar4/remnabot1.git`. Extra remote `remnabot` → `k4lantar4/remnabot` (custom reference). Do not retarget origin |
| `/opt/bot` is canonical source | **FALSE** | Upstream working tree only |
| `k4lantar4/cabinet1` already exists as clean fork | **FALSE** | 404. The clean fork is `k4lantar4/cabinet` |
| Blind `git init -b prod-cutover` in cabinet1 | **FORBIDDEN** | cabinet already has full history on the correct remotes |
| Remnawave permanently pin 3.3.2 | **REJECTED** | Latest GitHub release of `remnawave/panel` is **v3.3.2** (2026-08-20) and local compose uses `backend:3` — **rehearsal candidate / tracking snapshot**, not a production pin. Promote only a verified digest |
| Donor/4.2 code = specification | **REJECTED** | Official panel + actual API + rehearsal + tests are authoritative. remnabot1 4.2 client is a **starting implementation** to verify, not to copy blindly |
| remnabot1 working tree is clean | **FALSE as of plan-review** | Untracked `docs/superpowers/` (this plan). remnabot and cabinet working trees are clean. Do not encode “clean tree” as a current fact |

---

## Workspace governance (authoritative)

| Class | Trees | Allowed |
|---|---|---|
| **APPLICATION (maintained)** | `/opt/remnabot1`, `/opt/cabinet` | Implement, test, commit, push on migration branches |
| **AUTHORIZED INFRASTRUCTURE** | `/opt/caddy`, `/opt/remnawave` | Rehearsal/runtime orchestration only. No business logic. Caddyfile deployed from repo single-source |
| **PRODUCTION REFERENCE (protected)** | `/opt/remnabot` (incl. `/opt/remnabot/cabinet`); `/opt/bot-remnawave` if present on `Bot` | Read-only inspect. Never modify during RC |
| **UPSTREAM WORKING TREES (reference)** | `/opt/bot` only | Never compose-up, never restore, never implement. `/opt/cabinet` is **maintained**, not an upstream-only compare tree |

Caddy single-source: canonical files in `/opt/remnabot1/deploy/caddy/`; live `/opt/caddy/Caddyfile` is a deploy of that file; every Caddy task ends with a SHA-256 drift check.

---

## Locked errata vs Architecture A (binding)

Architecture A (`70476c0e`) was written when remnabot1 was assumed to be the custom 3.60 tree. Live trees invert that. After M0-T7 the recovered spec file **must** ship with this errata; a one-line “recovered” header is not enough.

| Spec location | Spec says (STALE) | Binding replacement |
|---|---|---|
| §2.2 Maintained trees | `/opt/cabinet1`; remnabot1 keeps custom `0001–0104` | Cabinet = **`/opt/cabinet`**. remnabot1 is **4.2** (`0001` plus upstream `0088–0110` on disk today). Custom Alembic `0088–0104` is **grafted from `/opt/remnabot`**. |
| Non-goal / §7.3 | Do **not** copy donor Alembic `0088–0110` into remnabot1 | That non-goal assumed remnabot1 already held production lineage. After inversion: **archive remnabot1 `0088–0110`** (4.2 files) and **copy remnabot `0088–0104` onto the live graph**. “Donor” in the spec meant `/opt/bot`; do not copy `/opt/bot` files. |
| §7.2 | Production `0103` is remnabot1-lineage `subscription_user_disabled` | Production `0103` is remnabot-lineage `subscription_user_disabled`. remnabot1 `0103` is `add_legal_consents`. Same ID, different file. |
| §2.1 identities | Five identities; `/opt/cabinet` is a donor | Six identities in this plan. `/opt/cabinet` is the **maintained** cabinet. `/opt/bot` is the only bot upstream working tree. |
| §6.1 / G3 | Pin Remnawave **3.3.2** | **Candidate**, not pin. Promote only a verified image digest after G3. |
| §13 step 5 | “Cabinet1” | `/opt/cabinet` |
| Dump name | `old(3.60)_remnawave_bot.sql` | Live path: `/opt/remnabot/old_3.60_remnawave_bot.sql` |

**Alembic authority after inversion = this plan.** Spec remains authority for DNS (no Primary IP move, no Floating IP, no AAAA, DNS-only), Telegram isolation, C2C isolation, rollback (DNS + frozen 3.60/2.8.1), writer freeze, pre-DNS verify, and gates G1–G13.

---

## Repeatable upstream policy (tomorrow, not a one-shot)

**UPSTREAM TRACKING** (may move daily):

```
fetch official remotes
→ record new HEAD SHA / tag
→ diff against last recorded tracking SHA
→ classify: ignore / integrate-now / defer
```

**PRODUCTION PROMOTION** (immutable only):

```
choose a commit SHA (bot, cabinet) and/or image digest (Remnawave)
→ integrate on a branch
→ test (unit + RC rehearsal gates)
→ record: Git SHA, tag if any, image digest, Alembic head, verification evidence
→ only then deploy that revision
```

Never deploy implicit `latest`, `backend:3`, or an unreviewed moving branch. The 4.2.0 / cabinet 1.67.0 / panel 3.3.2 observed today are **candidate snapshots**.

**Remnawave specifically:**

1. Inspect `remnawave/panel` releases/tags (currently latest **v3.3.2** — VERIFIED 2026-08-29 via GitHub releases).
2. Identify the currently relevant stable/recommended 3.x **candidate**.
3. Inspect official migration/API notes 2.8.1 → candidate (not only 4.2 bot comments).
4. Rehearse that **immutable** image digest against a copy of production RW data.
5. Promote only the candidate that passes G3 + M3-ID.

Do **not** duplicate Prisma/panel migrations in the bot. Bot Alembic only owns the **bot** database.

---

## Alembic strategy (inverted — critical)

**VERIFIED collision:** remnabot1 `0088` = `dedupe_tariff_subscriptions` (no-op); remnabot `0088` = `create_c2c_receipts`. Same IDs, different semantics from `0088` onward. Last shared identical revision remains **`0087`**. remnabot `0096` is a **merge** `down_revision = ('0094','0095')`.

**Production bot DB** is remnabot-lineage **`0103`** (custom). remnabot1 HEAD files are upstream **`0110`**. No `0111*` files exist on either tree.

**Therefore:** never `alembic upgrade` remnabot1's current `0088–0110` onto a restored production DB. Never `stamp` to hide the mismatch.

**Required graph for remnabot1 (the maintained code tree):**

1. **Graft** remnabot custom files `0088–0104` into remnabot1 `migrations/alembic/versions/` (those IDs already exist as different files — **replace** the upstream files in `versions/`).
2. Archive **all** remnabot1 `0088–0110` as **reference only** under `docs/superpowers/reference/upstream-alembic-0088-0110/` in the **same commit** as the graft. Leaving `0105–0110` in `versions/` is fatal: remnabot1 `0105.down_revision = '0104'`, so after replacing `0104` with remnabot traffic-clamp, leftover `0105–0110` would still run (guest/referral/promocode onto production-lineage data) and `alembic heads` would be `0110`.
3. New additive revisions **`0111+`** chain from remnabot **`0104`**, inspector-guarded, for 4.2 schema the **running 4.2 code** actually needs after unused features stay disabled. `0111` is a **new file / new ID**. Never reuse remnabot1’s `0104` or `0105–0110` IDs on the live graph.
4. `remnawave_id` is already in remnabot1 **models** and in the **archived** upstream `0104_remnawave_numeric_id.py`. It is **absent** from remnabot models/production schema (dump has no `remnawave_id`). The live `0111` **candidate** DDL (filled only after M3-ID) is: `users.remnawave_id` nullable BIGINT + **full** unique `ix_users_remnawave_id`; `subscriptions.remnawave_id` nullable BIGINT + **partial** unique `WHERE remnawave_id IS NOT NULL`. Those index shapes exist in 4.2 code; they are **not** rehearsal proof. Models must match (no inline `unique=True` on Subscription).

**Graft is lineage-correct and not a drop-in.** File-swap alone is unsafe until these hazards are gated:

| Hazard | Evidence | Gate |
|---|---|---|
| Startup auto-upgrade | remnabot1 `main.py` calls `run_alembic_upgrade()` before `setup_bot()`. On existing DBs: `command.upgrade(..., 'head')`. On “fresh”: `create_all` + **`stamp head`**. `SKIP_MIGRATION` exists but is not a rehearsal default. | **Forbidden:** start any remnabot1 **app** container (or run `alembic upgrade` / `stamp`) against a volume that contains the restored dump until M4-T0 verification (`alembic heads` = remnabot `0104`). |
| Leftover `0105–0110` | `0105.down_revision = '0104'` | Archive **0088–0110** in the same commit as the remnabot copy. M4-T0 fails if `0104_remnawave_numeric_id.py` or `0110_*.py` remain in `versions/`. |
| `0001` = `Base.metadata.create_all` | `0001_initial_schema.py` creates **current** 4.2 models (remnawave_id, grace, coupons, legal consents, **no C2C**) then later revisions apply. Production restore skips `0001`; empty/CI volumes do not. | M4-T1 records this. Tests/CI against empty DBs are expected inconsistent until M4-T4/T7. Do not use empty-volume `create_all` as a production path. |
| 4.2 tests/models vs grafted graph | Models already declare `users.remnawave_id` unique; tests import grace/legal/coupons; `tests/database/test_migration_chain.py` assumes the 4.2 chain. | Graft commit will desync models vs live graph until M4-T1/T3/T4/T7. Do not claim green 4.2 tests at M4-T0. List known breakages in M4-T0 evidence. |

**Code vs schema:** remnabot1 already contains the 4.2 Remnawave client (`get_user_by_id`, `get_all_users_stream`, `resolve_user`, no `get_user_by_uuid`) and `scripts/backfill_remnawave_ids.py` / `app/services/remnawave_identity_backfill.py`. Treat these as **reference implementations**. Verify against official panel + rehearsal (M3-ID) before trusting them. Do not assume “4.2 code works ⇒ architecture is correct.”

---

## Technical-debt / refactoring policy

Target: **clean production-compatible MVP** + **minimal risk-reducing refactoring** + **clean upstream boundaries** + **future mergeability**.

Refactor **now** only if it directly reduces: migration risk, duplicated compatibility logic, custom/upstream coupling, configuration fragmentation, testability, or future merge conflicts.

| Area | Decision | Why |
|---|---|---|
| remnabot1 4.2 Remnawave client | **KEEP + verify** (do not rewrite) | Already 3.x-shaped; verify on rehearsal; adapt only where official API differs |
| remnabot1 Alembic `0088–0110` as live graph | **REFACTOR NOW** (graft remnabot lineage) | Applying them to production data is unsafe |
| C2C / FA / Toman / wholesale from remnabot | **PORT NOW** (MVP) | Protected production behavior; remnabot1 has no C2C plugin and no `PaymentMethod.C2C` |
| Russian payment business logic | **DEFER** | Not an MVP product requirement |
| Unused 4.2 schema (coupons, grace, cispay, …) | **DEFER** unless boot/import requires it | M4-T1 must prove requirement. Do not re-import Architecture A §7.5 `0112–0126` because 4.2 files exist |
| FA/Toman extraction into `app.custom.*` | **DEFER** unless it unblocks mergeability | Prefer tests + keep working remnabot code paths |
| T2.1 wholesale seam (old uncommitted WIP) | **LOST with remnabot1 tree replace** | Recover from remnabot inline `price_display` / remnabot git; do not invent a housekeeping commit |

---

## Payment scope (MVP)

- **C2C: mandatory.** Port from `/opt/remnabot/app/plugins/c2c` + `PaymentMethod.C2C` + `c2c_receipts`. Isolated test admin chat (P1) required. G8 INCOMPLETE ⇒ **MVP-VERIFIED = NO-GO**.
- **Telegram Stars / CryptoBot:** already in remnabot1 `PaymentMethod`. May stay as **disabled-but-importable** paths if they start cleanly. Do not implement new business logic unless explicitly promoted.
- **Russian-specific providers** (YooKassa, Platega, Lava, CisPay, and the rest of the remnabot1 enum): **compatibility-only**. Imports must not break startup; paths stay disabled; production credentials never enter RC; no full integration “because upstream has them.”

---

## Global constraints (unchanged safety + topology corrections)

- Production Primary IP never moves. No Floating IP. No AAAA. Cloudflare DNS-only. TTL 300.
- Never restore onto donor/wrong-lineage volumes. **Existing on this host (forbidden restore/compose targets):** `bot_postgres_data`, `remnabot1_postgres_data`, `remnawave-db-data`, `remnawave-admin_postgres_data`, `remnawave-staging_staging_postgres_data`. New volumes only: `rehearsal_*`, `cutover_*`.
- Bot PG 15.18 → PG 15. Pin `postgres:15.18` (or a digest), not moving `15-alpine`. RW 2.8.1 dump → PG 17.6, verify under 2.8.1, then upgrade **app**. PG 17→18 is a separate track.
- PostgreSQL-safe snapshots only (`pg_dump -Fc` or stopped-container filesystem). Never tar a running PGDATA.
- Production Telegram token / webhook / C2C admin chat / payment secrets never on RC. Never two production-token processes. `WEBHOOK_IP` stays unset. Never `setWebhook`/`deleteWebhook`/`getUpdates` with the production token from RC. Never serve `hooks.rookari.com` from RC until cutover Caddy.
- Writers (production bot+scheduler, RW backend) freeze **before** their DB is dumped.
- Rollback: DNS back + frozen 3.60/2.8.1. Never in-place downgrade 3.x or `0111+`.
- Secrets: fingerprints only in git/chat/plans.
- **Do not merge cabinet source into remnabot1.**

### Forbidden actions (DAG edges, not comments)

1. **No remnabot1 app process** and **no `alembic upgrade` / `stamp`** on any volume containing the restored production dump until M4-T0 verification (`alembic heads` = remnabot `0104` traffic clamp; no `0104_remnawave_numeric_id.py` in `versions/`).
2. **Never** `docker compose up` / restore against `bot_postgres_data`, `remnabot1_postgres_data`, `remnawave-db-data`, or other existing non-`rehearsal_*`/`cutover_*` volumes.
3. **Never** start the production-token bot until the old production bot is stopped (M8).
4. **Never** apply remnabot1 live-graph `0088–0110` to a remnabot-lineage `0103` database.

---

## Pre-execution prerequisites

| # | Prerequisite | Blocks | If missing |
|---|---|---|---|
| P1 | Isolated C2C test admin chat (≠ production) | M6-T4, MVP-VERIFIED | **NO-GO** |
| P2 | Cloudflare DNS write access | M7-T5, M8 | stop |
| P3 | Cloudflare token for DNS-01 (optional) | M7-T6 preferred path | HTTP-01 window documented |
| P4 | `remnawave/backend:2.8.1` pullable | M2-T0 | stop |
| P5 | Read-only production RW env/compose on `Bot` | M2-T0 | residual env UNKNOWN |
| **P6** | **Production bot dump** | M2-T1 | **SATISFIED 2026-08-29.** Rehearsal input at `/opt/remnabot/old_3.60_remnawave_bot.sql` (11M). SHA-256 `b5fc023a23e99471ab9a4a61f834989ff7ff21c7f6061af4f926e404c093cb85`. `alembic_version=0103`; `c2c_receipts` present; custom user cols (`business_role`, `wholesale_discount_bps`, `panel_brand_prefix`, `remnawave_uuid`) present. **Not** a cutover artifact. Not inside remnabot1 git. RW dump remains `/opt/remnawave/old(2.8.1)_remnawave.sql`. |

---

## Parallel DAG (revised)

```
M0 (gov + topology + recover spec WITH errata + alembic strategy + upstream baseline)
  ├─ M1 RC infra (compose definable; postgres/redis may start; remnabot1 APP must not mount restored volume)
  ├─ M2-T0 pin RW 2.8.1 runtime
  ├─ M2-T1 bot restore postgres-only (needs P6, M1.1)     ──┐
  ├─ M2-T2 RW restore                                         │
  │      └─ M3-T1 3.x candidate rehearsal GO/NO-GO            │
  │            └─ M3-ID official+runtime identity/API proof     │
  └─ M4-T0 graft Alembic (needs M0-T6; independent of M3) ──┘
        HARD JOIN: M4-T0 verified BEFORE any remnabot1 app mounts rehearsal_bot_pg15
        └─ M4-T1 schema/boot dependency diff (needs M2-T1 + M4-T0)
        └─ M4-T2 verify/adapt 4.2 client (needs M3-ID)
        └─ M4-T3 0111 remnawave_id (candidate DDL after M3-ID)
        └─ M4-T4 models match
        └─ M4-T5 persist_identity seam
        └─ M4-T6 backfill (stable-key, after M3-ID)
        └─ M4-T7 port C2C/FA/Toman/wholesale from remnabot
M5 cabinet (/opt/cabinet, API only)
M6 gates (C2C hard) → MVP-VERIFIED
M7 prep → M8 cutover (21) → M9
```

**Hard rule:** identity proof (M3-ID) before trusting backfill/client. Graft verified before remnabot1 app starts on restored data. Writer freeze before final dumps. Official panel + rehearsal override 4.2 comments.

Weights: 1,2,3,5,8,13,21. Batches: NORMAL 8–13, HIGH-RISK 3–8, 21 standalone.

---

# M0 — Governance, topology, upstream baseline (do not execute yet)

### Task M0-T0: Codify workspace governance

- **ID:** M0-T0 · **WEIGHT:** 2 · **RISK:** Low · **DEPENDENCIES:** none
- **GOAL:** Make the six-identity model and tree classes the machine-readable rule.
- **FILES:** Create `.cursor/rules/10-remnabot-migration.mdc` on remnabot1 (file does not exist on the fresh fork).
- **EXACT IMPLEMENTATION:** Write the APPLICATION / INFRA / PRODUCTION REFERENCE / UPSTREAM WORKING TREE table using **verified** remotes (`k4lantar4/remnabot1`, `k4lantar4/cabinet`, `k4lantar4/remnabot` as reference). State Caddy single-source. State “cabinet never merged into remnabot1.” Include the four forbidden actions from this plan.
- **VERIFICATION:** rule names `/opt/cabinet` (not cabinet1); remnabot1 origin name `remnabot1`.
- **FAILURE CONDITION:** rule still says cabinet1 or remnabot1-origin=remnabot.
- **RECOVERY:** revert the rule file.
- **COMMIT:** `docs(M0-T0): workspace governance for split bot/cabinet` · **PUSH:** yes, on a new branch `prod-cutover` (see M0-T1) · **CHECKPOINT:** M0.

### Task M0-T1: Record Git topology (evidence only)

- **ID:** M0-T1 · **WEIGHT:** 2 · **RISK:** Low · **DEPENDENCIES:** none
- **GOAL:** Durable record of the **current** remotes/HEADs (this revision’s table is the seed; re-verify at execution).
- **FILES:** Create `docs/superpowers/evidence/2026-08-29-git-topology.md`.
- **EXACT IMPLEMENTATION:** For `/opt/remnabot1`, `/opt/cabinet`, `/opt/remnabot`, `/opt/bot`, `/opt/remnawave`, `/opt/caddy` record: exists?, git?, branch, HEAD (**full SHA**), remotes, `@{u}`, ahead/behind, dirty, cabinet embed. Record that remnabot1 `main` is **0/0 vs origin and vs upstream** at `89fa7dc5`. Record remnabot `chore/mcp-dev-tools` local `47a92619` vs `origin/chore/mcp-dev-tools` `70476c0e` (spec lives on the remote tip, not the local branch). Record remnabot1 dirty = untracked `docs/superpowers/` until this plan is committed.
- **VERIFICATION:** file contains the six-identity table with full SHAs.
- **COMMIT:** `docs(M0-T1): git topology evidence 2026-08-29` · **PUSH:** yes · **CHECKPOINT:** M0.

**Branch strategy (bot):** before any implementation commit, `git checkout -b prod-cutover` from `89fa7dc5` on remnabot1. Leave `main` free to track upstream. Never force-push. Never overwrite `origin/main`.

### Task M0-T2: WIP inventory after tree replace (no housekeeping bundle)

- **ID:** M0-T2 · **WEIGHT:** 2 · **RISK:** Low · **DEPENDENCIES:** M0-T1
- **GOAL:** State what WIP survived the remnabot1 replacement. **Do not** commit `.cursor` churn or invent T2.1.
- **FILES:** Evidence only.
- **EXACT IMPLEMENTATION:** Re-verify working trees at execution. remnabot1 is **not** clean while this plan is untracked (`?? docs/superpowers/`). remnabot and cabinet were clean at plan-review. Record that the previous T2.1 wholesale seam (`app/custom/pricing`, uncommitted on the old remnabot1 custom tree) is **not present** on the new fork (`app/custom` missing). Wholesale logic still exists **inline** in `/opt/remnabot/app/utils/price_display.py` — that is the port source (M4-T7), not a housekeeping commit.
- **VERIFICATION:** no `app/` commit in M0.
- **COMMIT:** `docs(M0-T2): WIP inventory after remnabot1 re-fork` · **PUSH:** yes · **CHECKPOINT:** M0.

### Task M0-T3: Cabinet Git reconciliation (non-destructive — no `git init`)

- **ID:** M0-T3 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** M0-T1
- **GOAL:** Confirm `/opt/cabinet` already is the maintained fork; configure nothing that destroys history; create a branch **only if** `main` is unsuitable.
- **FILES:** Evidence `docs/superpowers/evidence/2026-08-29-cabinet-git.md`.
- **EXACT IMPLEMENTATION:**
  1. Inspect remote `k4lantar4/cabinet` (`git ls-remote`).
  2. Inspect `/opt/cabinet` remotes, `main`, ahead/behind.
  3. Confirm local history **is** the fork (HEAD = `origin/main` = `upstream/main` at `35e5aa9e` — already VERIFIED).
  4. Confirm `origin` → `k4lantar4/cabinet`, `upstream` → `BEDOLAGA-DEV/bedolaga-cabinet` (already set).
  5. Do **not** `git init`. Do **not** retarget to `cabinet1`. Do **not** force-push.
  6. Working branch: **`main` is suitable** for a tree that is still identical to upstream. If cabinet custom work starts, create `prod-cutover` from current `main` (new branch, non-destructive).
  7. If a future inspect shows divergent unexplained history → `PLAN REVISION REQUIRED: Git topology ambiguity`.
- **VERIFICATION:** remotes unchanged; no new unrelated history; evidence recorded.
- **COMMIT:** evidence on remnabot1 (cabinet repo unchanged unless a `prod-cutover` branch is created later for real cabinet edits) · **PUSH:** remnabot1 yes · **CHECKPOINT:** M0-CAB.

### Task M0-T4: Baseline tags + dump inventory

- **ID:** M0-T4 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** M0-T1
- **GOAL:** Freeze SHAs; checksum both rehearsal-input dumps. Bot dump is already restored (P6 satisfied).
- **FILES:** `docs/superpowers/evidence/2026-08-29-baseline-checksums.md`.
- **EXACT IMPLEMENTATION:** Tag remnabot1 `baseline/prefork-4.2.0-89fa7dc5`. Record SHA-256 of `/opt/remnabot/old_3.60_remnawave_bot.sql` (expected `b5fc023a23e99471ab9a4a61f834989ff7ff21c7f6061af4f926e404c093cb85`) and `/opt/remnawave/old(2.8.1)_remnawave.sql`. Label both **REHEARSAL INPUT — NOT cutover artifacts**. Do not copy the bot dump into remnabot1 git.
- **VERIFICATION:** both checksums recorded; bot dump still `alembic_version=0103`.
- **FAILURE CONDITION:** file moved/altered so checksum no longer matches.
- **COMMIT:** `docs(M0-T4): baseline SHAs + dump inventory` · **PUSH:** yes · **CHECKPOINT:** M0.

### Task M0-T5: Establish upstream tracking baseline [weight 3]

- **ID:** M0-T5 · **WEIGHT:** 3 · **RISK:** Low · **DEPENDENCIES:** M0-T1
- **GOAL:** Record tracking SHAs so tomorrow’s upstream move is a diff, not a guess. No application code changes. No force-push.
- **FILES:** `docs/superpowers/evidence/2026-08-29-upstream-tracking.md`.
- **EXACT IMPLEMENTATION:**
  - Inspect remnabot1: origin, upstream, branches, divergence (0/0 both — VERIFIED).
  - Inspect cabinet: origin, upstream, divergence (0/0 both — VERIFIED).
  - Fetch (read-only) remnabot1 `upstream` and cabinet `upstream` if execution-time refs may have moved; record new HEADs.
  - Record maintained HEADs vs upstream HEADs; local-only commits (none today); remote-only commits (none today).
  - Suitability: remnabot1 `main` = clean 4.2.0 starting point → **create `prod-cutover` for work**; keep `main` tracking. Cabinet `main` suitable until custom cabinet commits.
  - Inspect official `remnawave/panel` current release/tag (today: **v3.3.2** latest; compose still uses moving `:3` / subscription `:latest` — flag as policy violation for promotion).
  - If remotes disagree with this plan’s table → `PLAN REVISION REQUIRED: Git topology ambiguity`.
- **VERIFICATION:** artifact lists SHAs for bot origin, bot upstream, cabinet origin, cabinet upstream, remnabot reference, panel tag.
- **COMMIT:** `docs(M0-T5): upstream tracking baseline` · **PUSH:** yes · **CHECKPOINT:** M0.

### Task M0-T6: Alembic graph decision evidence (before any migration file edit)

- **ID:** M0-T6 · **WEIGHT:** 5 · **RISK:** High · **DEPENDENCIES:** M0-T1
- **GOAL:** Lock the graft strategy **including auto-upgrade / leftover-file / 0001 / test hazards**. Do not freeze an incomplete “file-swap only” story.
- **FILES:** `docs/superpowers/evidence/2026-08-29-alembic-graph.md`.
- **EXACT IMPLEMENTATION:** Table remnabot vs remnabot1 for `0088–0110`. State graft + archive **all** remnabot1 `0088–0110` in one commit + `0111+` from remnabot `0104`. List remnabot custom revisions that **must** remain on the live graph (C2C, wholesale, partner, serial, entities_json, user_disabled, traffic clamp; note `0096` merge). List upstream revisions that become **reference-only**. Quote `run_alembic_upgrade()` (upgrade head / stamp head) and `main.py` calling it before `setup_bot()`. State the four graft hazards from this plan. State: **no remnabot1 process / no alembic upgrade / no stamp** on restored volumes until M4-T0.
- **VERIFICATION:** document forbids applying remnabot1 `0104_remnawave_numeric_id.py` (rev id `0104`) onto remnabot `0104` (traffic clamp); document forbids leaving `0105–0110` in `versions/`; document forbids starting remnabot1 against `rehearsal_bot_pg15` before M4-T0.
- **COMMIT:** `docs(M0-T6): alembic graft strategy` · **PUSH:** yes · **CHECKPOINT:** M0.

### Task M0-T7: Recover Architecture A spec into remnabot1 docs (copy + errata)

- **ID:** M0-T7 · **WEIGHT:** 2 · **RISK:** Low · **DEPENDENCIES:** M0-T1
- **GOAL:** The spec is not on the fresh fork; it is on `k4lantar4/remnabot` `origin/chore/mcp-dev-tools` (`70476c0e`). Copy it **and** install the locked errata so executors cannot follow stale cabinet1 / old-Alembic instructions.
- **FILES:**
  - `docs/superpowers/specs/2026-08-28-production-cutover-architecture-design.md` (copy of that blob)
  - `docs/superpowers/specs/2026-08-28-production-cutover-architecture-errata.md` (this plan’s “Locked errata” table)
- **EXACT IMPLEMENTATION:** `git -C /opt/remnabot show origin/chore/mcp-dev-tools:docs/superpowers/specs/2026-08-28-production-cutover-architecture-design.md` — **not** local `chore/mcp-dev-tools` (`47a92619` lacks the blob). Write into remnabot1. Spec header: “Recovered 2026-08-29 from `70476c0e`. Topology/Alembic superseded by the errata sibling and the MVP plan. Do not follow §2.2 / §7.2–7.3 / cabinet1 paths.” Do **not** rewrite the spec body. Write the errata file from this plan’s table.
- **VERIFICATION:** spec file starts with `# Design: Production Cutover Architecture A`; errata file exists and names `/opt/cabinet` + graft-from-remnabot; plan remains Alembic authority.
- **FAILURE CONDITION:** spec copied without errata, or errata still says cabinet1 / “do not copy remnabot 0088–0104”.
- **COMMIT:** `docs(M0-T7): recover Architecture A spec + topology errata` · **PUSH:** yes · **CHECKPOINT:** M0.

**Batch M0** = {M0-T0, T1, T2, T4, T5, T7} (weight 14 — split if needed: M0.1 = T0+T1+T2+T7 (8), M0.2 = T4+T5 (6)). **Batch M0-GRAPH** = {M0-T6} (5, HIGH-RISK). **Batch M0-CAB** = {M0-T3} (3).

---

# M1 — RC isolation + infrastructure foundation

There is **no** prior MVP plan on disk. Tasks below are the full M1. Cabinet source is `/opt/cabinet`. Caddy is repo single-source. Remnawave image in this milestone is **not** pinned to 3.3.2 — M2-T0 pins 2.8.1 for restore; M3-T1 pulls the candidate digest.

### Task M1-T1: Dedicated `rehearsal` compose with NEW isolated volumes

- **ID:** M1-T1 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint M0
- **GOAL:** RC rehearsal stack that cannot touch existing volumes/containers. Definable without starting the remnabot1 **app** against a restored DB.
- **FILES:** Create `docker-compose.rehearsal.yml` (repo) + `deploy/remnawave/docker-compose.rehearsal.yml`. remnabot1 has **no** `deploy/` yet.
- **EXACT IMPLEMENTATION:** compose project `rehearsal`:
  - `rehearsal_bot_db`: image **`postgres:15.18`** (or digest; not `15-alpine`), volume **`rehearsal_bot_pg15`**, bind `127.0.0.1:6061:5432`.
  - `rehearsal_bot_redis`; `rehearsal_bot` (build `/opt/remnabot1`, `env_file: .env.rehearsal`, `127.0.0.1:8081:8080`) — **defined but not started** against `rehearsal_bot_pg15` until M4-T0 PASS.
  - `rehearsal_rw`: image from M2-T0 (`remnawave/backend:2.8.1` digest) until M3-T1 replaces it with the candidate digest. Do not use `:3` or `:latest`.
  - `rehearsal_rw_db` (`postgres:17.6`, volume **`rehearsal_rw_pg17`**, `127.0.0.1`); `rehearsal_rw_redis`; `rehearsal_sub`.
  - `cabinet_frontend` built from **`/opt/cabinet`** (not cabinet1, not `/opt/remnabot/cabinet`).
  - Explicit `name:` on every volume so Docker does not prefix-collide with `bot_*` / `remnabot1_*`.
- **VERIFICATION:** `docker compose -p rehearsal -f docker-compose.rehearsal.yml config` renders; `docker volume ls` after a volume create shows only new `rehearsal_*` names; no service references `bot_postgres_data` / `remnabot1_postgres_data` / `remnawave-db-data`. **Do not** `compose up` `rehearsal_bot` as the M1.1 pass condition.
- **EXPECTED RESULT:** isolated definable stack.
- **FAILURE CONDITION:** any volume resolves to an existing non-rehearsal volume.
- **RECOVERY/ROLLBACK:** `docker compose -p rehearsal down` (never `-v` on a wrong volume); delete only `rehearsal_*` volumes.
- **COMMIT:** `feat(M1-T1): isolated rehearsal compose` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M1.1.

### Task M1-T2: BOT_TOKEN production-fingerprint fail-closed guard (TDD)

- **ID:** M1-T2 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint M0
- **GOAL:** RC refuses to start if `BOT_TOKEN` matches the production fingerprint, unless an explicit cutover override is set.
- **FILES:** Create `app/custom/safety/token_guard.py`; Test `tests/custom/test_token_guard.py`; wire into `app/custom/__init__.py:register_custom` (new; remnabot1 has no `app/custom` today) and call in `main.py` **before** `run_alembic_upgrade()` / `setup_bot()`.
- **INTERFACES — Produces:** `token_fingerprint(token)->str` (first 16 hex of sha256); `assert_not_production_token(bot_token, prod_fingerprint, allow_override)` (raises on match).
- **STEPS:** (1) failing tests (match refuses; override allows; distinct passes; no-fingerprint passes) → (2) run FAIL → (3) implement (raise `RuntimeError` unless `allow_override`) + wire startup reading `PRODUCTION_BOT_TOKEN_FINGERPRINT` and `ALLOW_PRODUCTION_BOT_TOKEN` → (4) run PASS.
- **VERIFICATION:** tests pass; manual: set the fingerprint to the RC token's and confirm startup aborts.
- **EXPECTED RESULT:** fail-closed guard active.
- **FAILURE CONDITION:** false positive on a distinct RC token.
- **RECOVERY/ROLLBACK:** unset the fingerprint var.
- **COMMIT:** `feat(M1-T2): fail-closed production token guard` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M1.2.

### Task M1-T3: RC environment reconciliation matrix + `.env.rehearsal`

- **ID:** M1-T3 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** M1-T1
- **GOAL:** A/B/C/D/E classification; RC env with no class D/E secrets.
- **FILES:** `docs/superpowers/evidence/2026-08-28-env-matrix.md`; `.env.rehearsal` (gitignored).
- **EXACT IMPLEMENTATION:** classify important keys using Architecture A §8.1 (with errata: cabinet = `/opt/cabinet`). RC overrides: test token, `WEBHOOK_URL=https://staging-host-hooks.rookari.com` or polling, `CABINET_URL=https://staging-host-cabinet.rookari.com`, RC-scoped `WEB_API_ALLOWED_ORIGINS` (not `*`), C2C per spec §11, `REMNAWAVE_API_URL`=rehearsal panel. Generated RC secrets. Class D absent. Report key names + fingerprints only.
- **VERIFICATION:** no class D/E key present; `WEB_API_ALLOWED_ORIGINS` RC-scoped; matrix classifies each important key.
- **EXPECTED RESULT:** RC env safe by construction.
- **FAILURE CONDITION:** any class D/E key present.
- **RECOVERY/ROLLBACK:** remove/regenerate.
- **COMMIT:** matrix doc only (never the env file) · **PUSH:** yes · **CHECKPOINT:** Checkpoint M1.2.

### Task M1-T4: RC Caddy `staging-host-*` via repo single-source

- **ID:** M1-T4 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** M1-T1, M0-T0
- **GOAL:** Route the five RC hostnames to rehearsal containers with no production names, through the repo single-source-of-truth.
- **FILES:** Canonical `deploy/caddy/Caddyfile` (repo) → deploy to `/opt/caddy/Caddyfile`.
- **EXACT IMPLEMENTATION:** author `staging-host-{cabinet,hooks,miniapp,master,sub}` blocks (HTTP-01) in the canonical file (cabinet `/api`→`rehearsal_bot:8080` else `cabinet_frontend` built from `/opt/cabinet`; hooks→bot; miniapp `/miniapp*`+`app-config.json`→bot else static; master→`rehearsal_rw:3000`; sub→`rehearsal_sub:3010`). Do **not** add production names (`cabinet.rookari.com`, `hooks.rookari.com`, …). Deploy: `cp deploy/caddy/Caddyfile /opt/caddy/Caddyfile && docker exec caddy caddy validate --config /etc/caddy/Caddyfile && docker exec caddy caddy reload`. First confirm `staging-host-*` A records exist (spec claims present; live Caddyfile does not route them) — create DNS-only records if missing (P2) so HTTP-01 can issue. Drift check: `sha256sum /opt/caddy/Caddyfile deploy/caddy/Caddyfile` equal.
- **VERIFICATION:** `caddy validate` OK; `curl -I https://staging-host-cabinet.rookari.com` → cert + expected; production names still resolve to `Bot`; drift checksum equal.
- **EXPECTED RESULT:** RC reachable; production untouched.
- **FAILURE CONDITION:** HTTP-01 fails (missing A) or a production name added.
- **RECOVERY/ROLLBACK:** restore prior canonical file, redeploy, reload.
- **COMMIT:** `feat(M1-T4): RC staging-host Caddy (repo single-source)` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M1.3.

### Task M1-T5: RC network/port hardening

- **ID:** M1-T5 · **WEIGHT:** 3 · **RISK:** Low · **DEPENDENCIES:** M1-T1
- **GOAL:** RC DB/app ports not world-exposed; scoped CORS.
- **FILES:** `docker-compose.rehearsal.yml`, `.env.rehearsal`.
- **EXACT IMPLEMENTATION:** bind rehearsal DBs to `127.0.0.1`; no `0.0.0.0:6060`; `WEB_API_ALLOWED_ORIGINS=https://staging-host-cabinet.rookari.com`.
- **VERIFICATION:** `ss -ltnp | grep -E ':6061|:8081'` shows `127.0.0.1` only.
- **EXPECTED RESULT:** no RC DB port on a public interface.
- **FAILURE CONDITION:** any `0.0.0.0` DB bind on RC.
- **RECOVERY/ROLLBACK:** edit compose, `up -d` (postgres/redis only if bot not yet allowed).
- **COMMIT:** `chore(M1-T5): harden RC ports/CORS` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M1.1.

**Batches:** M1.1={M1-T1,M1-T5}(8, NORMAL); M1.2={M1-T2,M1-T3}(8, NORMAL); M1.3={M1-T4}(5, HIGH-RISK, shared Caddy). Checkpoints leave RC isolation improved; production untouched (G7 holds).

---

# M2 — DB restoration rehearsals

### M2-T0: Pin Remnawave **2.8.1** restore runtime (not a 3.x pin)

- **WEIGHT:** 5 · **DEPENDENCIES:** M1.1, P4, P5
- Pull `remnawave/backend:2.8.1`; record **digest**. Derive compose/env. Boot reports 2.8.1. This pins the **pre-upgrade verify** image only.

### M2-T1: Restore bot dump (G1) — postgres only

- **WEIGHT:** 8 · **DEPENDENCIES:** M1.1, P6 (satisfied)
- Restore `/opt/remnabot/old_3.60_remnawave_bot.sql` into `rehearsal_bot_pg15` with **only** `rehearsal_bot_db` (and redis if needed) running. G1: `alembic_version=0103`, user count, `c2c_receipts`, `c2c` enabled, not `0106`.
- **FORBIDDEN:** start `rehearsal_bot` / run remnabot1 `alembic upgrade` / `stamp` against this volume until M4-T0 PASS.

### M2-T2: Restore RW 2.8.1 dump (G2)

- **WEIGHT:** 8 · **DEPENDENCIES:** M2-T0
- Restore `/opt/remnawave/old(2.8.1)_remnawave.sql` into `rehearsal_rw_pg17`. G2: user count, `users.uuid`, Prisma tail `20260625200530_add_external_squad_index`, 2.8.1 login on RC hostname.

---

# M3 — Remnawave candidate rehearsal + identity proof

### M3-T0: Choose the 3.x **candidate** from official panel (tracking, not pin)

- **WEIGHT:** 3 · **DEPENDENCIES:** M0-T5
- Inspect `https://github.com/remnawave/panel/releases` (today latest **v3.3.2**). Record tag + recommended docker tag. If a newer 3.x exists at execution time, **that** is the candidate unless notes say otherwise. Output: `CANDIDATE_TAG`, to be pulled as digest in M3-T1.

### M3-T1: Upgrade copy 2.8.1 → **candidate** (G3) GO/NO-GO

- **WEIGHT:** 13 · **DEPENDENCIES:** M2-T2, M3-T0
- Snapshot via `pg_dump -Fc` (not live PGDATA tar). Pull `remnawave/backend:<tag>` and record **digest**. Prisma runs on the copy. G3: numeric identity, reconstructible correlation (`shortUuid` or proven mapping), counts, joins, login, sub link, no mass revoke. Failure → `PLAN REVISION REQUIRED` (pick another 3.x). Success promotes **that digest** to “rehearsal-passed candidate,” still not production until cutover records it.

### M3-ID: Prove identity/API on the **actual** candidate + official docs

- **WEIGHT:** 8 · **DEPENDENCIES:** M3-T1 GO
- Official panel migration/API + runtime: uuid dropped?, `shortUuid` retained?, mapping table?, which lookups work, correlation to bot `remnawave_short_uuid`, whether backfill is required, exact deterministic algorithm. **4.2 backfill is reference, not proof.** Adapt remnabot1 client only where evidence differs. Low shortUuid coverage → `PLAN REVISION REQUIRED`.

### M3-T2: PG 17 vs 18 (E2)

- **WEIGHT:** 5 · **DEPENDENCIES:** M3-T1 GO
- Stay on 17 if the candidate runs; PG 18 is a separate track.

---

# M4 — Bot compatibility (port custom → 4.2; verify client)

### M4-T0: Graft remnabot Alembic lineage into remnabot1

- **WEIGHT:** 8 · **DEPENDENCIES:** M0-T6
- Archive **all** remnabot1 `0088–0110` out of `versions/` into `docs/superpowers/reference/upstream-alembic-0088-0110/`. Copy remnabot `0088–0104` into `versions/` **in the same commit**. Confirm `alembic heads` = remnabot `0104` (traffic clamp). Record known test/model/`0001` breakages. Do not run against production. Do not start remnabot1 against `rehearsal_bot_pg15` until this verification PASSES.
- **VERIFICATION:** `alembic heads` is remnabot `0104`; no file `0104_remnawave_numeric_id.py` or `0110_*.py` on the live graph; archive directory contains the 4.2 files.
- **COMMIT:** `feat(M4-T0): graft remnabot alembic 0088-0104; archive upstream 0088-0110`

### M4-T1: Schema + boot + code-dependency diff (H10)

- **WEIGHT:** 8 · **DEPENDENCIES:** M4-T0, M2-T1
- Inputs: remnabot 0104 schema (restored), remnabot1 4.2 models/imports, remnabot custom models, official RW contract (M3-ID if available).
- Question: **does remnabot1 4.2 boot against remnabot 0104 schema with unused payments disabled?** Every missing table/column that crashes import/startup becomes MVP schema. Every omitted upstream table gets a reason: not-MVP / already-local / not-required-by-imported-code / deferred.
- **Do not** claim “MVP = remnawave_id only” until this runs.

### M4-T2: Verify/adapt Remnawave client (do not rewrite from scratch)

- **WEIGHT:** 8 · **DEPENDENCIES:** M3-ID, M4-T1
- Start from remnabot1’s existing 3.x client. Compare to official+rehearsal evidence. Change only mismatches. Tests: no live path calls removed 2.8 routes; `coerce_panel_user_id` rejects UUIDs.
- **COMMIT:** `feat(M4-T2): verify remnabot1 3.x client against rehearsal contract`

### M4-T3: Alembic `0111` remnawave_id (semantics from M3-ID, not 4.2 comments)

- **WEIGHT:** 8 · **DEPENDENCIES:** M4-T1, M3-ID
- `down_revision='0104'` (grafted remnabot). **Candidate** DDL (4.2 shapes, to confirm or replace from M3-ID): Users: nullable BIGINT + **full** unique `ix_users_remnawave_id`. Subscriptions: nullable BIGINT + **partial** unique `uq_subscriptions_remnawave_id WHERE remnawave_id IS NOT NULL`. Non-unique index on existing `remnawave_short_uuid`. Inspector-guard `grace_access_sessions` (absent on remnabot schema). Protect custom columns (`c2c_receipts.approved_amount_kopeks`, `wholesale_discount_bps`, `user_disabled`, …).
- If M3-ID shows uuid retained or a mapping table, keep bot uniqueness as needed but **do not** copy “uuid lookup is gone” into runtime until evidence agrees.
- TDD + G5 + downgrade round-trip.

### M4-T4: Models match `0111` (no drift)

- **WEIGHT:** 3 · **DEPENDENCIES:** M4-T3
- Port remnawave_id mapping from remnabot1’s current models onto the grafted graph: User `unique=True,index=True`; Subscription plain column + `__table_args__` partial Index. `alembic revision --autogenerate` = no diff.

### M4-T5: `persist_identity` seam (panel `.id`, not uuid lookup)

- **WEIGHT:** 5 · **DEPENDENCIES:** M4-T4
- Thin adapter; two write paths. No `resolve_remnawave_id(uuid=...)` unless M3-ID proves uuid lookup still exists and is required.

### M4-T6: Backfill (stable-key; verify remnabot1 script)

- **WEIGHT:** 13 · **DEPENDENCIES:** M4-T5, M3-ID
- Use remnabot1 `remnawave_identity_backfill` **only if** M3-ID match keys match the script. Otherwise rewrite the match order. Dry-run default, `--apply`, coverage report, idempotent, non-destructive. Low coverage blocks cutover (E7). The 4.2 module also imports `GraceAccessSessionModel` — do not treat that import as a reason to create grace tables unless M4-T1 proved a boot dependency.

### M4-T7: Port MVP custom behavior from `/opt/remnabot`

- **WEIGHT:** 13 · **DEPENDENCIES:** M4-T0 (schema lineage), M4-T1
- Port **only**: C2C plugin + `PaymentMethod.C2C`; FA fallback/default language behavior; Toman dual-scale; wholesale/partner pricing (`wholesale_discount_bps` / `partner_status`) from remnabot `app/utils/price_display.py` (not a lost T2.1 seam). Keep seams small. Tests from remnabot `tests/plugins/c2c` and pricing tests. Do not port unused payments. Do not merge cabinet.

**Batches:** M4.0={T0}(8); M4.1={T1}(8); M4.2={T2}(8); M4.3={T3}(8); M4.4={T4,T5}(8); M4.5={T6}(13); M4.6={T7}(13).

---

# M5 — Cabinet (separate repo `/opt/cabinet`)

### Task M5-T1: RC cabinet from `/opt/cabinet`

- **ID:** M5-T1 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint M1.3, Checkpoint M0-CAB
- **GOAL:** Serve cabinet on `staging-host-cabinet` with `/api`→rehearsal bot.
- **FILES:** `/opt/cabinet` compose (join `remnawave-network`), build args (`VITE_API_URL=/api`, `VITE_TELEGRAM_BOT_USERNAME`=**test** bot).
- **EXACT IMPLEMENTATION:** add `networks: [remnawave-network]` (external) to `cabinet_frontend`; keep relative `VITE_API_URL=/api`; test bot username. M1-T4 block routes `/api/*`→`rehearsal_bot:8080`.
- **VERIFICATION (G9):** `https://staging-host-cabinet.rookari.com` loads; login/API works; FA strings; Toman `تومان`.
- **EXPECTED RESULT:** cabinet RC functional.
- **FAILURE CONDITION:** `/api` 502 or CORS block.
- **RECOVERY/ROLLBACK:** revert network change.
- **COMMIT:** cabinet repo `feat(M5-T1): RC split compose + network` on `prod-cutover` if custom commits start · **PUSH:** yes · **CHECKPOINT:** Checkpoint M5.

### Task M5-T2: Single cabinet source of truth

- **ID:** M5-T2 · **WEIGHT:** 3 · **RISK:** Low · **DEPENDENCIES:** M5-T1
- **GOAL:** One canonical cabinet source.
- **EXACT IMPLEMENTATION:** Canonical: `/opt/cabinet`. `/opt/remnabot/cabinet` is legacy production embed — do not deploy it. remnabot1 must not grow an embedded `cabinet/`. remnabot1 4.2 fork has no `cabinet/` directory today — keep it that way.
- **VERIFICATION:** rehearsal compose does not mount `/opt/remnabot/cabinet` or an embedded remnabot1 cabinet.
- **COMMIT:** `chore(M5-T2): single cabinet source of truth` on remnabot1 if compose comments/docs need it · **PUSH:** yes · **CHECKPOINT:** Checkpoint M5.

### Task M5-T3: RC JWT (class C)

- **ID:** M5-T3 · **WEIGHT:** 2 · **RISK:** Medium · **DEPENDENCIES:** M1-T3
- **GOAL:** RC does not validate production JWT.
- **FILES:** `.env.rehearsal` (`CABINET_JWT_SECRET`=generated).
- **EXACT IMPLEMENTATION:** generate RC secret; confirm fingerprint ≠ production.
- **VERIFICATION:** RC login issues/validates tokens; production JWT does not validate on RC.
- **COMMIT:** none (secret); fingerprint note in matrix · **CHECKPOINT:** Checkpoint M5.

**Batch M5** = {M5-T1,M5-T2,M5-T3} (10, NORMAL).

---

# M6 — Protected behavior + end-to-end MVP

### Task M6-T1: FA fallback regression gate (G9-strings)

- **ID:** M6-T1 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** M4-T7
- **GOAL:** Lock the `fa→en→ru` fallback chain.
- **FILES:** Test `tests/localization/test_fa_fallback.py` (port from remnabot if present).
- **EXACT IMPLEMENTATION:** assert Persian for known keys; missing FA key → en → ru; English digits where required.
- **VERIFICATION (G9):** test passes; RC spot-check.
- **COMMIT:** `test(M6-T1): FA fallback gate` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M6.1.

### Task M6-T2: Toman dual-scale regression gate

- **ID:** M6-T2 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** M4-T7
- **GOAL:** Lock dual-scale (catalog kopeks÷100 vs balance Toman 1:1; `BALANCE_TOMAN_CUTOFF_UTC`).
- **FILES:** Test `tests/utils/test_price_display_toman.py`.
- **EXACT IMPLEMENTATION:** cover display helpers used after the remnabot port (`تومان`, fa-IR grouping).
- **VERIFICATION:** test passes; RC shows correct scale.
- **COMMIT:** `test(M6-T2): Toman gate` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M6.1.

### Task M6-T3: Wholesale pricing regression gate (G10)

- **ID:** M6-T3 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** M4-T7
- **GOAL:** Lock wholesale gating on `partner_status`+`wholesale_discount_bps` via the **ported remnabot `price_display` path**, not the lost T2.1 `app/custom/pricing` seam.
- **FILES:** Test `tests/services/test_wholesale_pricing.py` (adapt from remnabot).
- **EXACT IMPLEMENTATION:** integer BPS, floor; approved partner discounted, revoked not.
- **VERIFICATION (G10):** test passes; RC partner purchase discounted.
- **COMMIT:** `test(M6-T3): wholesale gate` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M6.1.

### Task M6-T4: C2C isolated RC test — HARD MVP gate (H9)

- **ID:** M6-T4 · **WEIGHT:** 5 · **RISK:** High · **DEPENDENCIES:** M4-T7, P1
- **GOAL:** Prove C2C on RC with the isolated test admin chat (P1). C2C is an MVP requirement — INCOMPLETE is a NO-GO.
- **FILES:** `.env.rehearsal` (`C2C_ENABLED=true`, `C2C_ADMIN_CHAT_ID`=test chat); evidence log.
- **EXACT IMPLEMENTATION:** with the isolated test chat (P1) and test bot: submit a receipt; approve in the test chat; confirm balance credit (Toman scale) + `c2c_receipts` row. Restored historical rows allowed. Never post to the production admin chat. Spec §11.
- **VERIFICATION (G8):** receipt→approve→balance flow verified in the isolated chat.
- **EXPECTED RESULT:** **G8 PASS**.
- **FAILURE CONDITION:** P1 unavailable, or any RC receipt reaches the production admin chat → **G8 INCOMPLETE ⇒ MVP-VERIFIED = NO-GO** (disable C2C, treat a prod-chat leak as an incident).
- **RECOVERY/ROLLBACK:** `C2C_ENABLED=false`.
- **COMMIT:** `docs(M6-T4): C2C RC PASS (isolated chat)` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M6.2.

### Task M6-T5: End-to-end RC MVP smoke — MVP-VERIFIED gate

- **ID:** M6-T5 · **WEIGHT:** 8 · **RISK:** High · **DEPENDENCIES:** M6-T1..T4 (**G8 PASS required**), M4-T6, Checkpoint M3-ID
- **GOAL:** Prove the whole MVP path on RC before cutover prep.
- **FILES:** `docs/superpowers/evidence/2026-08-28-rc-e2e-smoke.md`.
- **EXACT IMPLEMENTATION:** rehearsal bot (test token) on the `0111`+backfilled copy talking to the **rehearsal-passed candidate digest**: subscription purchase/renew; panel-user read/update **by numeric id** (or whatever M3-ID proved); sub link on `staging-host-sub`; cabinet login on `staging-host-cabinet`; FA+Toman+wholesale; C2C (G8 PASS).
- **VERIFICATION:** each sub-flow evidenced; G7 continuously holds.
- **FAILURE CONDITION:** any protected-behavior regression, or **G8 not PASS** → **MVP-VERIFIED = NO-GO**; block cutover.
- **COMMIT:** `docs(M6-T5): RC E2E MVP smoke` · **PUSH:** yes · **CHECKPOINT:** **Checkpoint MVP-VERIFIED** (requires G8 PASS).

**Batches:** M6.1={M6-T1,M6-T2,M6-T3}(9, NORMAL); M6.2={M6-T4}(5, HIGH-RISK); M6.3={M6-T5}(8, HIGH-RISK).

---

# M7 — Production cutover preparation

Do not start M7 without **MVP-VERIFIED** (G8 PASS). Record promotion identity: remnabot1 `prod-cutover` SHA, cabinet SHA, Remnawave **image digest**, Alembic head, G3/G6 evidence.

### Task M7-T1: Stage cutover Caddy blocks (repo single-source, inactive)

- **ID:** M7-T1 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint MVP-VERIFIED
- **GOAL:** Prepare `cabinet/hooks/master/sub/miniapp` production blocks without activating on `bot-v4`.
- **FILES:** `deploy/caddy/Caddyfile.cutover`.
- **EXACT IMPLEMENTATION:** author the five blocks per spec §9.3 (no `pgadmin/admin/rw/config/panel`); validate a merged copy in a scratch container. Do not serve `hooks.rookari.com` from RC until M8.
- **VERIFICATION:** `caddy validate` OK; upstreams correct; no production name active yet; SHA-256 of canonical file recorded.
- **COMMIT:** `feat(M7-T1): staged cutover Caddy blocks` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.1.

### Task M7-T2: Stage cutover secrets (class D) + arm production-token guard

- **ID:** M7-T2 · **WEIGHT:** 3 · **RISK:** High · **DEPENDENCIES:** Checkpoint MVP-VERIFIED, P5
- **GOAL:** Cutover-only secret file RC never references; compute production `BOT_TOKEN` fingerprint for the guard.
- **FILES:** `.env.cutover` (gitignored, NOT in any compose `env_file` until cutover); matrix note.
- **EXACT IMPLEMENTATION:** on production (read-only), compute `token_fingerprint(BOT_TOKEN)` → set `PRODUCTION_BOT_TOKEN_FINGERPRINT` in `.env.rehearsal` (fingerprint, not token). Place class-D secrets only in `.env.cutover`. `WEBHOOK_IP` unset.
- **VERIFICATION:** guard aborts if RC token equals the fingerprint; no compose references `.env.cutover`; no secret printed.
- **COMMIT:** `docs(M7-T2): armed prod-token guard (fingerprint only)` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.1.

### Task M7-T3: Rollback drill / tabletop (G13)

- **ID:** M7-T3 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint MVP-VERIFIED
- **GOAL:** Verify the rollback runbook without a live DNS revert or starting the old stack while production is live.
- **FILES:** `docs/superpowers/runbooks/rollback.md`.
- **EXACT IMPLEMENTATION:** document + dry-verify spec §12: stop new app → restore A to `91.107.249.43` → start frozen 3.60/2.8.1 on `Bot` → optional `setWebhook` → verify cabinet/sub/panel/C2C. Validate the frozen compose parses; confirm old 2.8.1 volume+dump untouched. Do NOT `docker compose start` on live `Bot`.
- **VERIFICATION (G13):** runbook complete; compose validated; DNS revert steps confirmed against actual record IDs (read-only).
- **COMMIT:** `docs(M7-T3): rollback runbook (G13)` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.2.

### Task M7-T4: Writer-freeze + fresh-dump/restore/migrate timing rehearsal (C3/E5)

- **ID:** M7-T4 · **WEIGHT:** 8 · **RISK:** High · **DEPENDENCIES:** Checkpoint M4.5, Checkpoint M3 (GO)
- **GOAL:** Rehearse the exact write-freeze + fresh-dump path and measure wall-clock to size the maintenance window.
- **FILES:** `docs/superpowers/evidence/2026-08-28-cutover-timing.md`; `docs/superpowers/runbooks/writer-freeze.md`.
- **EXACT IMPLEMENTATION:** define writers explicitly (bot container + scheduler; RW backend container). Rehearse: stop the (rehearsal) bot writer → `pg_dump -Fc` bot → stop the (rehearsal) RW writer → `pg_dump -Fc` RW → checksum both → restore onto `cutover_bot_pg15`/`cutover_rw_pg17` → apply remnabot `0104`+`0111` (bot), 2.8.1→**candidate digest** (RW) → backfill → time each phase.
- **VERIFICATION (E5):** timings recorded; SHA-256 present; gates G1/G2/G3/G5/G6 reproduce on the cutover volumes; write-freeze runbook names every writer.
- **COMMIT:** `docs(M7-T4): writer-freeze runbook + cutover timing (C3/E5)` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.3.

### Task M7-T5: Cloudflare DNS write-access verification (P2)

- **ID:** M7-T5 · **WEIGHT:** 3 · **RISK:** Medium · **DEPENDENCIES:** Checkpoint MVP-VERIFIED
- **GOAL:** Confirm the operational path to edit the five A records at cutover.
- **FILES:** `docs/superpowers/runbooks/dns-cutover.md`.
- **EXACT IMPLEMENTATION:** confirm who/what can edit `cabinet/hooks/master/sub/miniapp` A records (TTL 300, DNS-only); record record IDs + current `91.107.249.43` → target `91.107.144.95`. `panel` / `staging-host-*` must-not-move vs names that move — document both. Change nothing now. No AAAA.
- **VERIFICATION:** documented write access; named party/API can flip.
- **FAILURE CONDITION:** no confirmed write access → cutover blocker (P2).
- **COMMIT:** `docs(M7-T5): DNS cutover runbook + write access` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.4.

### Task M7-T6: Pre-issue production TLS certs (DNS-01) or document HTTP-01 window (H12)

- **ID:** M7-T6 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** M7-T1, P3
- **GOAL:** Eliminate HTTP-01 issuance as a hidden source of cutover downtime.
- **FILES:** `deploy/caddy/` (optional Cloudflare-plugin Caddy build), `docs/superpowers/runbooks/tls-cutover.md`.
- **EXACT IMPLEMENTATION:** **Preferred:** Caddy with Cloudflare DNS plugin on `bot-v4` and `tls { dns cloudflare <token> }` to **pre-issue** certs for the five production names **before** DNS flip (P3 token; class D). **Fallback (no plugin):** document that HTTP-01 issues after the A record points here; verify content pre-DNS via `curl --resolve name:443:91.107.144.95` and internal upstreams over HTTP.
- **VERIFICATION:** either certs present for the five names pre-flip, or the HTTP-01 window + `curl --resolve` plan documented.
- **COMMIT:** `docs(M7-T6): TLS cutover strategy` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M7.5.

**Batches:** M7.1={M7-T1,M7-T2}(8, HIGH-RISK); M7.2={M7-T3}(5); M7.3={M7-T4}(8, HIGH-RISK); M7.4={M7-T5}(3); M7.5={M7-T6}(5). Checkpoint **CUTOVER-READY** after all M7 + MVP-VERIFIED (with G8 PASS).

---

# M8 — Cutover (weight 21, standalone)

### Task M8-T1: Execute production cutover (writer-freeze first, pre-DNS verify)

- **ID:** M8-T1 · **WEIGHT:** 21 · **RISK:** Critical · **DEPENDENCIES:** Checkpoint CUTOVER-READY, Checkpoint M3 (GO), Checkpoint M3-ID, all M7, **explicit user authorization** (this plan does not authorize execution)
- **GOAL:** Move production application + data + hostnames to `bot-v4` with a single bot process, no lost writes, and a reversible DNS flip.
- **FILES:** live `/opt/caddy/Caddyfile` (deploy `Caddyfile.cutover`), production compose on `bot-v4` (loads `.env.cutover`), Cloudflare A records.
- **EXACT IMPLEMENTATION — order is a safety constraint (spec §10.2 + §13):**
  1. **Maintenance / quiesce.** Announce; stop admitting new work.
  2. **Freeze writers (C3):** stop the production **bot container** (webhook consumer + scheduler) and the production **Remnawave backend container**. Confirm no writer process remains. x-ui continues (out of scope).
  3. **Fresh dumps:** `pg_dump -Fc` the bot DB and the RW DB (now write-frozen) — THE cutover artifacts. SHA-256 checksum.
  4. **Restore/migrate** onto `cutover_bot_pg15`/`cutover_rw_pg17`: bot remnabot `0104`+`0111`; RW 2.8.1→**rehearsal-passed candidate digest**; run `remnawave_id` backfill; verify coverage ≥ threshold.
  5. **Pre-DNS verification (H12) — before touching DNS:** application health; DB counts/integrity (G1/G2); migration integrity (`alembic 0111`, RW candidate digest); `remnawave_id` backfill coverage (G6); internal routing via `curl --resolve {cabinet,hooks,master,sub,miniapp}.rookari.com:443:91.107.144.95` and internal upstream checks; data integrity spot-checks. Deploy `Caddyfile.cutover` to `/opt/caddy`; if M7-T6 pre-issued certs, confirm they load.
  6. **Stop remains:** old production bot + RW stay stopped (already frozen in step 2). **Never two production-token processes.**
  7. **Flip Cloudflare A records** → `91.107.144.95` (TTL 300). No AAAA. Do not move Primary IP. Do not move `panel` / `staging-host-*` unless the runbook says they move.
  8. **Start ONE** new bot with the production token (`ALLOW_PRODUCTION_BOT_TOKEN=1`, `.env.cutover`) + `WEBHOOK_URL=https://hooks.rookari.com`. `WEBHOOK_IP` unset.
  9. **Post-DNS verification (H12):** `getWebhookInfo` = `https://hooks.rookari.com/webhook` (single consumer); TLS/SNI for the five names; public HTTP 200/expected; subscription URLs fetch configs; C2C + FA. Optional `setWebhook` if stale.
  10. Leave `Bot` apps stopped, DBs intact, x-ui running.
- **VERIFICATION (G11, G12):** single webhook consumer; five names 200/expected on the new IP with valid TLS; C2C + FA verified; backfill coverage gate met.
- **FAILURE CONDITION:** pre-DNS verify fails → do not flip DNS (no downtime incurred). Post-flip TLS/webhook/data failure beyond TTL → invoke M7-T3 rollback.
- **RECOVERY/ROLLBACK:** stop new app → DNS back to `91.107.249.43` → start frozen 3.60/2.8.1 → verify. Never in-place downgrade 3.x/`0111`.
- **COMMIT:** post-cutover, commit the deployed Caddy snapshot + runbook outcomes (never secrets). **PUSH:** yes. **CHECKPOINT:** **Checkpoint CUTOVER-DONE** (standalone).

**Batch M8** = {M8-T1} (21, standalone). Requires explicit user go-ahead.

---

# M9 — Post-cutover validation / stabilization

### Task M9-T1: Full production completion-gate verification

- **ID:** M9-T1 · **WEIGHT:** 8 · **RISK:** High · **DEPENDENCIES:** Checkpoint CUTOVER-DONE
- **GOAL:** Confirm the completion gate on production names.
- **FILES:** `docs/superpowers/evidence/2026-08-28-postcutover.md`.
- **EXACT IMPLEMENTATION:** verify app health; DB integrity/counts; migration integrity (`alembic 0111`, RW candidate digest); Telegram single-consumer; C2C; wholesale; FA; Toman; cabinet; subscription/purchase; production routing; `remnawave_id` coverage.
- **VERIFICATION:** every completion-gate item evidenced.
- **FAILURE CONDITION:** protected-behavior regression → rollback decision.
- **COMMIT:** `docs(M9-T1): completion-gate evidence` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M9.1.

### Task M9-T2: Rollback readiness + freeze old stack

- **ID:** M9-T2 · **WEIGHT:** 5 · **RISK:** Medium · **DEPENDENCIES:** M9-T1
- **GOAL:** Keep `Bot` a valid rollback target for the agreed window.
- **FILES:** runbook update.
- **EXACT IMPLEMENTATION:** confirm old bot/RW stopped, old DBs intact+checksummed, x-ui active; document rollback expiry.
- **VERIFICATION:** old stack startable on demand; DBs unmutated.
- **COMMIT:** `docs(M9-T2): rollback readiness` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M9.2.

### Task M9-T3: RC/fossil cleanup (after stable)

- **ID:** M9-T3 · **WEIGHT:** 3 · **RISK:** Low · **DEPENDENCIES:** M9-T2 + stability window
- **GOAL:** Remove `rehearsal_*` volumes and donor fossils only after stability; keep `cutover_*` (live) and frozen rollback assets.
- **VERIFICATION:** `docker volume ls` shows only production + rollback assets.
- **FAILURE CONDITION:** accidental removal of a live/rollback volume.
- **RECOVERY/ROLLBACK:** restore from cutover dump.
- **COMMIT:** `chore(M9-T3): cleanup fossils` · **PUSH:** yes · **CHECKPOINT:** Checkpoint M9.3.

**Batch M9** = {M9-T1}(8), {M9-T2}(5), {M9-T3}(3).

---

# Backlog (not MVP)

Russian payment integrations; coupons; grace product; referral v2; legal consents; guest-purchase extras — unless M4-T1 proves a boot dependency (then schema-only, still disabled). Architecture A §7.5 `0112–0126` stays deferred.

---

## Fresh-conversation resume

Resume from: this plan; remnabot1 `prod-cutover` (once created); `/opt/cabinet` git; `/opt/remnabot` as read-only custom source; `docs/superpowers/evidence/*`; `docs/superpowers/specs/*-errata.md`; Superpowers state; runtime (`docker volume ls`, `alembic current`, Cloudflare A, `getWebhookInfo`).

**Do not execute M0 until the user explicitly starts execution.**

---

## Self-review

1. English `cabinet1` / remnabot1-origin=remnabot **rejected** with evidence.
2. User path notes **confirmed**.
3. Architecture inverted: port custom **into** 4.2, not 4.2 **into** 3.60.
4. Alembic graft required; collision documented; auto-upgrade / leftover `0105–0110` / `0001` / tests documented as graft hazards.
5. 3.3.2 = candidate, not pin; `:3`/`:latest` forbidden for promotion.
6. 4.2 client ≠ spec. `0111` DDL is candidate until M3-ID.
7. C2C hard gate; P6 bot dump path verified 2026-08-29.
8. No `git init` on cabinet.
9. Cutover write-freeze + pre-DNS + stop-old-bot-before-new-token retained.
10. M1 inlined (previous revision was not on disk). Spec recovered only with errata.
11. No application code changed in this revision. **No task executed.**

### Plan-review reception (2026-08-29)

| Item | Verdict | Action |
|---|---|---|
| M1 dangling “previous revision” | **Accepted** — VERIFIED, only this file exists under `docs/superpowers/plans/` | Inlined M1-T1…T5 |
| M0-T7 copies contradictory spec | **Accepted** — VERIFIED spec §2.2 cabinet1 and §7.3 “do not copy 0088–0110” | Spec + binding errata; plan is Alembic authority |
| Graft drop-in unsafe (auto-upgrade, leftover 0105–0110, 0001, tests) | **Accepted** — VERIFIED `run_alembic_upgrade` + `0105.down_revision='0104'` + `0001` create_all | Hazards + forbidden app-start until M4-T0 |
| DAG / wrong volumes | **Accepted** — VERIFIED volumes exist on host | Forbidden volume list; postgres-only restore; M4-T0 before remnabot1 app |
| Donor index/backfill copied as proven | **Accepted** as wording | M4-T3/T6 are candidate-after-M3-ID |
| M5–M9 too compressed | **Accepted** | Restored executable tasks with `/opt/cabinet` substitutions |
| “remnabot1 tree clean” | **Accepted** — VERIFIED `?? docs/superpowers/` | Claim corrected |
| Eight M0 evidence tasks are process-heavy | **Pushed back** | Human partner already required M0-T0…T7 in the topology revision. Did not add more M0 tasks; did not delete T2/T3 |
| Pin postgres 15 digest / not alpine | **Accepted** (was Minor) | M1-T1 uses `postgres:15.18` |

---

## Execution handoff

Plan revised and saved to `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md` on the remnabot1 tree. **No task executed.** File remains untracked until M0.

When the user starts execution: Batch **M0.1** first (governance, topology evidence, recover spec **with errata**, WIP inventory), then **M0-T3** (cabinet confirm), **M0-T6** (alembic strategy **with graft hazards**), **M0-T4** (record dump checksums; P6 already satisfied). Then M1 (inlined). **Do not start remnabot1 against the restored dump until M4-T0.**
