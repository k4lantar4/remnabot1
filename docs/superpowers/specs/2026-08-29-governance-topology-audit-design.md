# Design: Governance, Topology, and Pre-Execution Audit

Date: 2026-08-29  
Status: Approved (user confirmed all sections)  
Scope: Align rules, workspace, specs, and plan with verified RC/prod reality before M0 execution  
Related: `docs/superpowers/plans/2026-08-28-production-cutover-mvp.md`

This document is the binding governance audit. It does **not** authorize cutover, restores, DNS changes, or production modification.

---

## 1. Problem statement

Agents and executors currently face **three conflicting authorities**:

| Source | Stale or wrong content |
|---|---|
| `10-remnabot.mdc` (local, gitignored) | `origin = k4lantar4/remnabot`; Alembic §18 forbids graft the plan requires |
| Architecture A spec (on remnabot remote only) | `/opt/cabinet1`; “do not copy donor 0088–0110” |
| MVP plan (topology revision 2026-08-29) | Correct topology; not yet backed by committed rules/specs on remnabot1 |

Without alignment, M0–M4 work will follow the wrong remote, reject the Alembic graft, or mount the wrong volumes.

---

## 2. Verified reality map

Evidence class: **VERIFIED** unless marked INFERRED.

### 2.1 RC host (`bot-v4` / `91.107.144.95`)

| Item | Value |
|---|---|
| Maintained bot | `/opt/remnabot1` · `origin` = `k4lantar4/remnabot1` · HEAD `89fa7dc5` (4.2.0) |
| Maintained cabinet | `/opt/cabinet` · HEAD `35e5aa9e` (1.67.0) · 0/0 vs origin and upstream |
| Production reference | `/opt/remnabot` · `origin` = `k4lantar4/remnabot` · HEAD `f36ec4ca` (3.60.0) |
| Upstream reference | `/opt/bot` · official upstream · HEAD = remnabot1 |
| Remnawave runtime | `backend:3`, `postgres:18.4`, `subscription-page:latest` · volume `remnawave-db-data` |
| Bot rehearsal dump | `/opt/remnabot/old_3.60_remnawave_bot.sql` · SHA-256 `b5fc023a…` · alembic `0103` · no `remnawave_id` |
| RW rehearsal dump | `/opt/remnawave/old(2.8.1)_remnawave.sql` · SHA-256 `11935de6…` |
| `/opt/bot-remnawave` | **Absent** on RC |

### 2.2 Production host (`Bot` / `91.107.249.43`)

| Item | Value |
|---|---|
| Live application | `/opt/bot-remnawave` (not `/opt/remnabot`) |
| Bot DB alembic | **`0103`** (remnabot lineage) |
| Bot PostgreSQL | `postgres:15-alpine` (not `15.18`) |
| Remnawave | `backend:2.8.1`, `postgres:17.6`, `subscription-page:7.2.6` |
| C2C | `C2C_ENABLED=true` in production `.env` |
| Caddy | `staging-host-*` blocks **already present** alongside production names |
| `/opt/bot-remnawave` | **Present** |

### 2.3 Alembic collision (binding)

- Last shared identical revision: **`0087`**
- From `0088` onward: same revision IDs, **different file semantics** (e.g. remnabot `0088` = C2C; remnabot1 `0088` = dedupe_tariff)
- Production DB at remnabot **`0103`**; remnabot1 disk graph ends at upstream **`0110`**
- remnabot1 `main.py` calls `run_alembic_upgrade()` before bot setup — **forbidden** on restored volumes until M4-T0

---

## 3. Binding authority hierarchy

Highest to lowest:

1. Live production runtime + verified dumps (Bot host, checksums)
2. MVP plan + this design + plan errata addendum (**Alembic authority**)
3. Architecture A spec + errata sibling (DNS, Telegram, C2C, rollback, gates)
4. `10-remnabot-migration.mdc` (committed machine-readable governance)
5. Historical `/opt/remnabot/.cursor/rules/*` (dev workflow only; not migration authority)
6. Obsolete names: `cabinet1`, `remnabot1 origin = remnabot`, Architecture A §2.2/§7.3 without errata

---

## 4. Six identities (do not conflate)

| # | Identity | Path / remote | Role |
|---|---|---|---|
| 1 | Production reference | `/opt/remnabot` · `k4lantar4/remnabot` · 3.60.0 | READ-ONLY custom source + rollback code reference |
| 2 | Maintained bot | `/opt/remnabot1` · `k4lantar4/remnabot1` · 4.2.0 | Implementation authority after ports |
| 3 | Upstream bot | `BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot` | Moving target; fetch/compare only |
| 4 | Upstream working tree | `/opt/bot` | READ-ONLY; never compose-up or restore |
| 5 | RC runtime | `bot-v4` / `91.107.144.95` | Rehearsal; test Telegram token |
| 6 | Production runtime | `Bot` / `91.107.249.43` | Live until cutover; rollback target |

**Cabinet:** maintained `/opt/cabinet` · `k4lantar4/cabinet` — never merged into remnabot1.

**Production live path on Bot:** `/opt/bot-remnawave` (distinct from `/opt/remnabot` reference clone on RC).

---

## 5. Workspace tree classes

| Class | Trees | Allowed |
|---|---|---|
| APPLICATION (maintained) | `/opt/remnabot1`, `/opt/cabinet` | Implement, test, commit, push on `prod-cutover` |
| AUTHORIZED INFRASTRUCTURE | `/opt/caddy`, `/opt/remnawave` | Orchestration only; Caddy from repo single-source when established |
| PRODUCTION REFERENCE | `/opt/remnabot`, `/opt/bot-remnawave` (Bot host) | Read-only inspect; never modify during RC |
| UPSTREAM REFERENCE | `/opt/bot` | Never compose-up, restore, or implement |

Workspace file must include `remnabot` and `caddy` folders so agents see reference trees without inferring paths from stale docs.

---

## 6. Alembic strategy (approved)

### 6.1 Primary: graft remnabot lineage (Approach 2)

1. Archive **all** remnabot1 `0088–0110` to `docs/superpowers/reference/upstream-alembic-0088-0110/`
2. Copy remnabot `0088–0104` into `versions/` in the **same commit**
3. Verify `alembic heads` = remnabot traffic-clamp **`0104`**
4. Add **`0111+`** only for 4.2 schema the running code needs (e.g. `remnawave_id` after M3-ID)

**§18.1 exception:** grafting production-lineage files `0088–0104` is authorized. “Never reuse donor revision IDs” applies to copying **upstream `/opt/bot`** files onto production data, not to recovering remnabot custom history.

### 6.2 Fallback: re-ID from 0103 (Approach 3)

Trigger: `PLAN REVISION REQUIRED: Alembic graft failed M4-T0`

- Stamp at production `0103`; additive `0111+` only
- Never run remnabot1 upstream `0088–0110` on restored production DB

### 6.3 Non-negotiable gates

- `SKIP_MIGRATION=true` on any container touching restored DB until M4-T0 PASS
- No remnabot1 app process on restored volume before graft verified
- Leftover `0105–0110` in `versions/` after partial graft = **fatal**

---

## 7. Remnawave two-track model (approved)

| Track | Purpose | Configuration |
|---|---|---|
| **Rehearsal-restore (authoritative)** | G2, G3, M3, cutover evidence | Pin `backend:2.8.1` digest; PG **17.6**; isolated `rehearsal_rw_pg17`; subscription pin matches prod (**7.2.6** baseline) |
| **RC dev sandbox (non-promotable)** | Exploratory API only | Current RC stack (`backend:3`, PG 18.4, `:latest`) — **must not** be cited as cutover proof |

PG 17→18 is a **separate gate** (plan E2). Do not combine RW 2.8→3.x migration with PG major bump in one cutover window.

Never promote moving tags: `backend:3`, `:latest`, unreviewed `main`.

---

## 8. Bot PostgreSQL and volumes

### 8.1 PostgreSQL

- Plan pin `postgres:15.18` is aspirational; **production uses `15-alpine`**
- Rehearsal: pin digest from production `15-alpine` **or** prove 15.18 compatibility before cutover
- Do not assume alpine vs minor pin are interchangeable without evidence

### 8.2 Forbidden restore targets (per host)

**RC host (verified 2026-08-29):** only `remnawave-db-data` exists from legacy list; still treat as forbidden for rehearsal restore. Use only `rehearsal_*` / `cutover_*` volume names.

**Bot host (verified):** includes `bot-remnawave_postgres_data`, `remnawave-db-data`, `remnawave-admin_postgres_data`, `remnawave-staging_staging_postgres_data`, and other `bot-remnawave*` volumes — never restore rehearsal onto these.

---

## 9. Failure points (ranked)

| Rank | Failure | Severity | Mitigation |
|---|---|---|---|
| F1 | Startup auto-upgrade on restored DB | Critical | `SKIP_MIGRATION`; no app until M4-T0 |
| F2 | Governance triple-conflict | Critical | This design + `10-remnabot-migration.mdc` + errata |
| F3 | Leftover `0105–0110` after graft | Critical | Single-commit archive + verification |
| F4 | RC RW moving tags as cutover proof | High | Two-track model; immutable digests |
| F5 | C2C absent from remnabot1 | High | M4-T7 port; G8 NO-GO |
| F6 | Caddy drift | Medium | `remnabot1/deploy/caddy/` single-source + SHA-256 |
| F7 | Workspace hides reference trees | Medium | Workspace update |
| F8 | Rules gitignored | Medium | `.gitignore` whitelist |
| F9 | Prod `staging-host-*` already live | Medium | M1-T4 must not duplicate prod routes on RC |
| F10 | `remnawave_id` absent in prod dump | Expected | M3-ID + M4-T3/T6 |

---

## 10. Deliverables (this approval)

| # | Artifact | Location |
|---|---|---|
| 1 | This design | `docs/superpowers/specs/2026-08-29-governance-topology-audit-design.md` |
| 2 | Migration rule | `.cursor/rules/10-remnabot-migration.mdc` |
| 3 | Gitignore whitelist | `.gitignore` |
| 4 | Workspace | `/opt/remnawave-stack.code-workspace` |
| 5 | Architecture A + errata | `docs/superpowers/specs/2026-08-28-production-cutover-architecture-design.md` + `-errata.md` |
| 6 | Plan errata | `docs/superpowers/plans/2026-08-28-production-cutover-mvp-errata.md` |
| 7 | Evidence | `docs/superpowers/evidence/2026-08-29-git-topology.md`, `2026-08-29-host-inventory-rc.md`, `2026-08-29-host-inventory-prod.md` |

**Execution order:** governance artifacts (this commit) → M0 batches per MVP plan → do not start remnabot1 app on restored dump until M4-T0.

---

## 11. Non-goals

- Live cutover or DNS changes
- Alembic file edits (M4-T0)
- Rewriting Architecture A spec body (errata only)
- Deleting `/opt/remnabot/.cursor/rules/` (historical; not workspace authority)

---

## 12. Success criteria

- Committed rule names `remnabot1` origin and `/opt/cabinet` (not `cabinet1`)
- Errata file explicitly overrides Architecture A Alembic and cabinet paths
- Workspace exposes reference and infra trees
- Evidence files contain full SHAs and host-specific volume lists
- No agent following committed docs can retarget remnabot1 origin to `k4lantar4/remnabot`
