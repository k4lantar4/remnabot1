# MVP plan errata addendum

Date: 2026-08-29  
Parent: `2026-08-28-production-cutover-mvp.md`  
Authority: Same as parent; this file patches verified drift only.

---

## E1. Host-scoped volume forbidden lists

The parent plan lists volume names observed on **Bot**. On **RC** (`91.107.144.95`, 2026-08-29), only `remnawave-db-data` exists from that legacy set.

**Rule:** forbidden = any volume not named `rehearsal_*` or `cutover_*` when performing restore/rehearsal on either host. Additionally on Bot, never touch `bot-remnawave_postgres_data`, `bot-remnawave_*`, `remnawave-admin_postgres_data`, `remnawave-staging_staging_postgres_data`.

---

## E2. Production application path

| Host | Path | Role |
|---|---|---|
| Bot (`91.107.249.43`) | `/opt/bot-remnawave` | **Live** production compose + `.env` |
| RC | `/opt/remnabot` | READ-ONLY 3.60 reference clone |
| RC | `/opt/bot-remnawave` | **Absent** |

P5 read-only production env/compose: inspect **`/opt/bot-remnawave`** on Bot via `ssh bot`.

---

## E3. Bot PostgreSQL image

Parent M1-T1 pins `postgres:15.18`. Production Bot runs **`postgres:15-alpine`**.

Rehearsal must either:
- pin the **same digest** as production `remnawave_bot_db`, or
- document and test 15.18 compatibility before cutover.

Do not treat 15.18 as verified merely because it is a newer 15.x tag.

---

## E4. Remnawave two-track model (RC)

| Track | Stack | Promotable? |
|---|---|---|
| Rehearsal-restore | `backend:2.8.1` digest, PG **17.6**, subscription **7.2.6** (prod baseline) | Yes, after G3 |
| RC dev sandbox | Current RC: `backend:3`, PG **18.4**, `subscription-page:latest` | **No** — exploratory only |

M3-T1/G3 evidence must come from rehearsal-restore track, not the live RC dev sandbox.

PG 17→18 remains plan E2 separate track; do not combine with 2.8→3.x cutover.

---

## E5. Production Caddy staging-host blocks

**VERIFIED:** Bot `/opt/caddy-remnawave/Caddyfile` already routes `staging-host-{hooks,cabinet,miniapp,sub}.rookari.com`.

M1-T4 on RC must:
- not add production application hostnames to RC Caddy,
- confirm DNS for staging names points to the intended host before HTTP-01,
- avoid duplicating prod staging routes if DNS already targets Bot.

---

## E6. Governance artifacts (completed pre-M0)

| Artifact | Path |
|---|---|
| Audit design | `docs/superpowers/specs/2026-08-29-governance-topology-audit-design.md` |
| Migration rule | `.cursor/rules/10-remnabot-migration.mdc` |
| Architecture errata | `docs/superpowers/specs/2026-08-28-production-cutover-architecture-errata.md` |
| Git topology evidence | `docs/superpowers/evidence/2026-08-29-git-topology.md` |
| Host inventories | `docs/superpowers/evidence/2026-08-29-host-inventory-{rc,prod}.md` |

M0-T0 rule filename: use **`10-remnabot-migration.mdc`** (not `10-remnabot.mdc`, which remains local/gitignored legacy).

---

## E7. Alembic fallback trigger

If M4-T0 graft verification fails after good-faith archive+copy: invoke Approach 3 (re-ID from `0103`, additive `0111+` only) per governance audit design §6.2. Do not proceed to app boot on restored data until a graph strategy passes M4-T0 gates.
