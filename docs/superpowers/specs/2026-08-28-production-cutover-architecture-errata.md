# Architecture A — Binding errata (topology inversion)

Date: 2026-08-29  
Supersedes stale sections of `2026-08-28-production-cutover-architecture-design.md`  
Authority: Alembic and cabinet paths = **MVP plan + governance audit design**, not Architecture A body.

Recover the spec body from `k4lantar4/remnabot` `origin/chore/mcp-dev-tools` @ `70476c0e`. Do not follow §2.2, §7.2–7.3, or `cabinet1` paths without this errata.

| Spec location | Spec says (STALE) | Binding replacement |
|---|---|---|
| §2.2 Maintained trees | `/opt/cabinet1`; remnabot1 keeps custom `0001–0104` | Cabinet = **`/opt/cabinet`**. remnabot1 is **4.2** (`0001` + upstream `0088–0110` on disk). Custom Alembic `0088–0104` is **grafted from `/opt/remnabot`**. |
| Non-goal / §7.3 | Do **not** copy donor Alembic `0088–0110` into remnabot1 | After topology inversion: **archive** remnabot1 `0088–0110` and **copy remnabot `0088–0104`**. “Donor” meant `/opt/bot`; do not copy `/opt/bot` files. |
| §7.2 | Production `0103` is remnabot1-lineage `subscription_user_disabled` | Production `0103` is remnabot-lineage `subscription_user_disabled`. remnabot1 `0103` is `add_legal_consents`. Same ID, different file. |
| §2.1 identities | Five identities; `/opt/cabinet` is a donor | Six identities in MVP plan. `/opt/cabinet` is **maintained**. `/opt/bot` is the only bot upstream working tree. |
| §6.1 / G3 | Pin Remnawave **3.3.2** | **Candidate**, not pin. Promote only verified image digest after G3. |
| §13 step 5 | “Cabinet1” | `/opt/cabinet` |
| Dump name | `old(3.60)_remnawave_bot.sql` | Live path: `/opt/remnabot/old_3.60_remnawave_bot.sql` |
| Production app path | Implied `/opt/remnabot` on Bot | Live production on Bot: **`/opt/bot-remnawave`**. RC reference clone: `/opt/remnabot`. |
| Alembic §18 “never reuse IDs” | Applies to all donor copies | **§18.1:** graft remnabot `0088–0104` is authorized; forbids upstream `/opt/bot` `0088–0110` on production DB only. |

Architecture A remains authority for: DNS (no Primary IP move, no Floating IP, no AAAA, DNS-only), Telegram isolation, C2C isolation, rollback (DNS + frozen 3.60/2.8.1), writer freeze, pre-DNS verify, gates G1–G13.
