# Host inventory — RC (bot-v4)

Date: 2026-08-29  
IP: `91.107.144.95`  
Role: Release Candidate / rehearsal host

## Application trees

| Path | Present | Notes |
|---|---|---|
| `/opt/remnabot1` | yes | Maintained bot 4.2.0 |
| `/opt/cabinet` | yes | Maintained cabinet 1.67.0 |
| `/opt/remnabot` | yes | Production reference 3.60.0 READ-ONLY |
| `/opt/bot` | yes | Upstream reference READ-ONLY |
| `/opt/bot-remnawave` | **no** | Live prod path exists only on Bot |
| `/opt/remnawave` | yes | RW runtime |
| `/opt/caddy` | yes | Caddy infra |
| `/opt/remnawave-admin` | yes | Admin tooling (not MVP cutover scope) |

## Docker volumes (sample)

| Volume | Notes |
|---|---|
| `remnawave-db-data` | Legacy — **forbidden** for rehearsal restore |
| `caddy-ssl-data` | Caddy certs |
| `valkey-socket` | RW redis socket |

No `rehearsal_*` or `cutover_*` volumes yet (pre-M1).

## Running containers (2026-08-29)

| Container | Image |
|---|---|
| `remnawave` | `remnawave/backend:3` |
| `remnawave-db` | `postgres:18.4` |
| `remnawave-subscription-page` | `remnawave/subscription-page:latest` |
| `caddy` | `caddy:2.9` |

**Non-promotable** for cutover evidence until replaced by rehearsal-restore track (plan errata E4).

## Rehearsal input dumps

| File | SHA-256 | Notes |
|---|---|---|
| `/opt/remnabot/old_3.60_remnawave_bot.sql` | `b5fc023a23e99471ab9a4a61f834989ff7ff21c7f6061af4f926e404c093cb85` | alembic `0103`; not cutover artifact |
| `/opt/remnawave/old(2.8.1)_remnawave.sql` | `11935de69fc6dc318419753916ff840f950f5b4be7a27be46e2ccf2142347377` | RW 2.8.1 rehearsal input |

## Caddy (local)

Live `/opt/caddy/Caddyfile` includes legacy comment referencing `cabinet1` on `panel.rookari.com` — drift vs maintained topology; single-source under `remnabot1/deploy/caddy/` not yet created.
