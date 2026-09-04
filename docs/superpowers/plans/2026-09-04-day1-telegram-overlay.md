# Day-1 Telegram overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overlay production Iran chrome on remnabot1 4.2 Telegram: Persian rich `/start` with Jalali dates, production My Subscriptions list (search, page/total, brand+serial, تعداد کاربر), partner note/brand at confirm, and Telegram pause — without restoring the 3.60 start grid or copying donor handlers.

**Architecture:** Surgical overlay on `/opt/remnabot1` `prod-cutover`. New helpers own list chrome, partner checkout fields, and pause toggle. Hot files (`my_subscriptions.py`, `rich_menu.py`, `tariff_purchase.py`, `models.py`) get thin callsites only. Cabinet Layer A is a **separate plan** on `/opt/cabinet` and is not re-implemented here. Joint operator smoke is the last task.

**Tech Stack:** Python 3.13, aiogram 3, SQLAlchemy, Alembic (map only — no autogenerate), pytest via `uv run pytest`, `jdatetime` for fa dates.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-04-day1-remaining-overlay-design.md` (operator تایید 2026-09-04).
- Tree: `/opt/remnabot1` only for Tasks 1–9. Do not edit `/opt/remnabot`. Cabinet work is `docs/superpowers/plans/2026-09-03-cabinet-layer-a-user-ui.md` on `/opt/cabinet`.
- Keep the 4.2 rich `/start` shell (Connect / Subscription / Balance). Do not restore the 3.60 keyboard grid.
- Do not copy `/opt/remnabot/app/handlers/subscription/my_subscriptions.py` over the 4.2 file.
- 4.2 gift row on My Subscriptions **stays**.
- Do not start M7-T1, touch DNS, production token, or Layer C (`/sales`, Earn, `PartnerCheckoutFields`).
- Do not `alembic revision --autogenerate`. Columns already exist via grafted `0095` and `0103`.
- Do not unwind C2C / Toman / FA / `PricingEngine` into plugins.
- English digits in new fa strings (0-9). Missing fa keys keep `fa → en → ru`.
- One concern per commit on `prod-cutover`. Do not force-push.
- After each code task: `uv run pytest` on the task's test file(s). `import main` smoke is not required unless the task touches `main.py`.
- Fail-open: unmapped ORM fields hide extra UI; missing `jdatetime` falls back to Gregorian.

**Parallel track (not this file):** execute cabinet Layer A in `/opt/cabinet` so Task 10 smoke can include `https://panel.rookari.com`.

---

## File map

| File | Responsibility |
|---|---|
| `/opt/remnabot1/pyproject.toml` + `uv.lock` | Add `jdatetime>=5.2.0` so fa Jalali actually converts |
| `/opt/remnabot1/app/database/models.py` | Map `users.panel_brand_prefix`, `subscriptions.purchase_note`, `subscriptions.user_disabled` |
| `/opt/remnabot1/app/localization/locales/fa.json` | List / search / pause / partner keys; rich-menu سرویس / تعداد کاربر |
| `/opt/remnabot1/app/utils/subscription_list_display.py` | Identity, list line, search filter (new) |
| `/opt/remnabot1/app/handlers/subscription/my_subscriptions.py` | Call helper; search FSM; pause buttons; drop hardcoded Cyrillic |
| `/opt/remnabot1/app/utils/rich_menu.py` | Jalali fallback text in subscription table |
| `/opt/remnabot1/app/handlers/subscription/purchase.py` | Register search / pause / partner callbacks |
| `/opt/remnabot1/app/states.py` | `searching_my_subscriptions`, `waiting_for_purchase_note` |
| `/opt/remnabot1/app/utils/remnawave_panel_identity.py` | Brand prefix validate + note sanitize (new) |
| `/opt/remnabot1/app/utils/partner_checkout_telegram.py` | Partner confirm extras, fail-open (new) |
| `/opt/remnabot1/app/handlers/subscription/tariff_purchase.py` | Thin hook: extra confirm buttons + persist note/prefix |
| `/opt/remnabot1/app/services/subscription_user_toggle_service.py` | Pause/resume using `remnawave_id` (new) |
| `/opt/remnabot1/tests/utils/test_subscription_list_display.py` | Formatter / identity / search |
| `/opt/remnabot1/tests/handlers/test_my_subscriptions_pagination.py` | Update callsites; search button; no Cyrillic |
| `/opt/remnabot1/tests/database/test_day1_orm_columns.py` | ORM attributes exist |
| `/opt/remnabot1/tests/utils/test_partner_checkout_telegram.py` | Fail-open + persist helpers |
| `/opt/remnabot1/tests/services/test_subscription_user_toggle.py` | Pause rules without panel |
| `/opt/remnabot1/tests/utils/test_rich_menu.py` | Jalali fallback string in table |

---

### Task 1: Install jdatetime

**Files:**
- Modify: `/opt/remnabot1/pyproject.toml`
- Modify: `/opt/remnabot1/uv.lock` (via `uv add`)
- Test: `/opt/remnabot1/tests/utils/test_jalali_datetime.py` (create)

**Interfaces:**
- Consumes: existing `app/utils/jalali_datetime.py::format_user_datetime`
- Produces: runtime `jdatetime` so `language='fa'` converts instead of Gregorian fallback

- [ ] **Step 1: Write the failing test**

Create `/opt/remnabot1/tests/utils/test_jalali_datetime.py`:

```python
from datetime import UTC, datetime

from app.utils.jalali_datetime import format_user_datetime, is_jalali_language


def test_fa_is_jalali_language() -> None:
    assert is_jalali_language('fa') is True
    assert is_jalali_language('ru') is False


def test_fa_converts_known_gregorian_anchor() -> None:
    # 2026-07-09 → 18.04.1405 (same anchor as production jalali tests)
    dt = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    assert format_user_datetime(dt, language='fa', fmt='%d.%m.%Y') == '18.04.1405'


def test_ru_stays_gregorian() -> None:
    dt = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    out = format_user_datetime(dt, language='ru', fmt='%d.%m.%Y')
    assert '1405' not in out
    assert '09.07.2026' in out or '07' in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/test_jalali_datetime.py::test_fa_converts_known_gregorian_anchor -v`

Expected: FAIL (`ModuleNotFoundError: jdatetime` inside the helper, which then returns Gregorian — assertion `18.04.1405` fails) **or** FAIL if the helper swallows ImportError and returns a Gregorian string.

- [ ] **Step 3: Add the dependency**

```bash
cd /opt/remnabot1 && uv add 'jdatetime>=5.2.0'
```

Do not change `format_user_datetime` unless the test still fails after the package is installed.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/test_jalali_datetime.py -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock tests/utils/test_jalali_datetime.py
git commit -m "feat(day1): add jdatetime so fa dates convert to Jalali"
```

---

### Task 2: Map 0095 and 0103 columns on ORM

**Files:**
- Modify: `/opt/remnabot1/app/database/models.py` (User ~2251 after `wholesale_discount_bps`; Subscription after `remnawave_short_id` ~2425)
- Test: `/opt/remnabot1/tests/database/test_day1_orm_columns.py` (create)

**Interfaces:**
- Consumes: grafted tables `users.panel_brand_prefix`, `subscriptions.purchase_note`, `subscriptions.user_disabled` (Alembic `0095` / `0103` already in the remnabot lineage). `User.is_partner` already exists.
- Produces: `User.panel_brand_prefix: str | None`, `Subscription.purchase_note: str | None`, `Subscription.user_disabled: bool`

- [ ] **Step 1: Inspect DB (no migration)**

If a rehearsal/RC postgres for the grafted graph is running, confirm columns exist. Do **not** autogenerate. Example (adjust container name if different):

```bash
docker ps --format '{{.Names}}' | rg -i 'rehearsal|remnabot1.*postgres' || true
```

If you can exec into the grafted bot DB:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name IN ('panel_brand_prefix', 'purchase_note', 'user_disabled');
```

Expected: three rows. If a column is missing, **stop** with `PLAN REVISION REQUIRED: day-1 ORM column missing` — do not invent a new revision in this task.

- [ ] **Step 2: Write the failing test**

Create `/opt/remnabot1/tests/database/test_day1_orm_columns.py`:

```python
from app.database.models import Subscription, User


def test_user_has_panel_brand_prefix() -> None:
    assert hasattr(User, 'panel_brand_prefix')


def test_subscription_has_purchase_note_and_user_disabled() -> None:
    assert hasattr(Subscription, 'purchase_note')
    assert hasattr(Subscription, 'user_disabled')
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/database/test_day1_orm_columns.py -v`

Expected: FAIL (`AttributeError` / assert on `hasattr`)

- [ ] **Step 4: Write minimal implementation**

On `User`, immediately after `wholesale_discount_bps = Column(...)`:

```python
    panel_brand_prefix = Column(String(24), nullable=True)
```

On `Subscription`, immediately after the `remnawave_short_id = Column(...)` block:

```python
    purchase_note = Column(Text, nullable=True)
    user_disabled = Column(Boolean, default=False, nullable=False)
```

`Text` is already imported in `models.py` (used elsewhere). If the import is missing, add `Text` next to the other SQLAlchemy types at the top of the file.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/database/test_day1_orm_columns.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/database/models.py tests/database/test_day1_orm_columns.py
git commit -m "feat(day1): map brand prefix, purchase note, and user_disabled on ORM"
```

---

### Task 3: fa.json keys for list, search, pause, partner, rich wording

**Files:**
- Modify: `/opt/remnabot1/app/localization/locales/fa.json` (merge keys only; never replace the file)
- Test: `/opt/remnabot1/tests/localization/test_day1_fa_keys.py` (create)

**Interfaces:**
- Consumes: existing `load_locale` / `fa.json`
- Produces: keys listed in the test below

- [ ] **Step 1: Write the failing test**

Create `/opt/remnabot1/tests/localization/test_day1_fa_keys.py`:

```python
import json
from pathlib import Path

FA = Path('app/localization/locales/fa.json')

REQUIRED = (
    'MY_SUB_LIST_TITLE',
    'MY_SUB_LIST_EMPTY',
    'MY_SUB_TRAFFIC_LINE',
    'MY_SUB_DEVICES_LINE',
    'MY_SUB_DEVICES_COUNT_SHORT',
    'MY_SUB_UNTIL_LINE',
    'MY_SUB_STATUS_EXPIRED',
    'MY_SUB_STATUS_DISABLED',
    'MY_SUB_STATUS_LIMITED',
    'MY_SUB_DEFAULT_NAME',
    'MY_SUB_SEARCH',
    'MY_SUB_SEARCH_PROMPT',
    'MY_SUB_SEARCH_RESET',
    'MY_SUB_SEARCH_CANCEL',
    'MY_SUB_SEARCH_CANCELLED',
    'MY_SUB_SEARCH_EMPTY_QUERY',
    'MY_SUB_SEARCH_STATE_LOST',
    'MY_SUB_SEARCH_ACTIVE',
    'MY_SUB_SEARCH_NO_RESULTS',
    'MY_SUB_BACK',
    'MY_SUB_BTN_DISABLE',
    'MY_SUB_BTN_ENABLE',
    'PARTNER_PURCHASE_NOTE_BTN',
    'PARTNER_PURCHASE_NOTE_PROMPT',
    'PARTNER_BRAND_TOGGLE_ON',
    'PARTNER_BRAND_TOGGLE_OFF',
)


def test_day1_fa_keys_present_and_persian() -> None:
    data = json.loads(FA.read_text(encoding='utf-8'))
    for key in REQUIRED:
        assert key in data, key
        assert data[key].strip()
    assert 'تعرفه' not in data['MAIN_MENU_RICH_TABLE_TARIFF']
    assert 'سرویس' in data['MAIN_MENU_RICH_TABLE_TARIFF']
    assert 'دستگاه' not in data['MAIN_MENU_RICH_DEVICES']
    assert 'کاربر' in data['MAIN_MENU_RICH_DEVICES']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/localization/test_day1_fa_keys.py -v`

Expected: FAIL (missing keys and/or still `تعرفه` / `دستگاه` on those two rich keys)

- [ ] **Step 3: Merge keys into fa.json**

Keep JSON valid. Update existing rich keys in place:

- `MAIN_MENU_RICH_TABLE_TARIFF`: `سرویس`
- `MAIN_MENU_RICH_TARIFF`: `📦 سرویس: {tariff}`
- `MAIN_MENU_RICH_DEVICES`: `📱 تعداد کاربر: {devices}`

Add (values must use English digits):

```json
"MY_SUB_LIST_TITLE": "📋 <b>اشتراک‌های من</b>",
"MY_SUB_LIST_EMPTY": "📋 <b>اشتراک‌های من</b>\n\nاشتراکی ندارید.",
"MY_SUB_TRAFFIC_LINE": "   📊 ترافیک: {traffic}",
"MY_SUB_DEVICES_LINE": "   👥 تعداد کاربر: {devices}",
"MY_SUB_DEVICES_COUNT_SHORT": "{count} کاربر",
"MY_SUB_UNTIL_LINE": "   📅 تا: {end_date}",
"MY_SUB_STATUS_EXPIRED": " (منقضی)",
"MY_SUB_STATUS_DISABLED": " (غیرفعال)",
"MY_SUB_STATUS_LIMITED": " (اتمام حجم)",
"MY_SUB_DEFAULT_NAME": "اشتراک",
"MY_SUB_SEARCH": "جستجو 🔍",
"MY_SUB_SEARCH_PROMPT": "نام، سریال یا یادداشت را بفرستید.",
"MY_SUB_SEARCH_RESET": "❌ حذف جستجو",
"MY_SUB_SEARCH_CANCEL": "✖️ انصراف",
"MY_SUB_SEARCH_CANCELLED": "✖️ جستجو لغو شد",
"MY_SUB_SEARCH_EMPTY_QUERY": "❌ متن جستجو خالی است",
"MY_SUB_SEARCH_STATE_LOST": "❌ جلسه منقضی شد. دوباره «اشتراک‌های من» را باز کنید.",
"MY_SUB_SEARCH_ACTIVE": "جستجو: <b>{query}</b>",
"MY_SUB_SEARCH_NO_RESULTS": "نتیجه‌ای پیدا نشد.",
"MY_SUB_BACK": "◀️ قبلی",
"MY_SUB_BTN_DISABLE": "⏸ توقف اشتراک",
"MY_SUB_BTN_ENABLE": "🟢 روشن کردن اشتراک",
"PARTNER_PURCHASE_NOTE_BTN": "📝 یادداشت خرید",
"PARTNER_PURCHASE_NOTE_PROMPT": "یادداشت این خرید را بفرستید (حداکثر 500 نویسه).",
"PARTNER_BRAND_TOGGLE_ON": "🏷 برند: روشن",
"PARTNER_BRAND_TOGGLE_OFF": "🏷 برند: خاموش"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/localization/test_day1_fa_keys.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/localization/locales/fa.json tests/localization/test_day1_fa_keys.py
git commit -m "i18n(fa): day-1 My Subscriptions, search, pause, and rich wording"
```

---

### Task 4: List display helper

**Files:**
- Create: `/opt/remnabot1/app/utils/subscription_list_display.py`
- Test: `/opt/remnabot1/tests/utils/test_subscription_list_display.py`

**Interfaces:**
- Consumes: `format_user_datetime`; Task 2 ORM fields via `getattr` (fail-open); `User.is_partner`
- Produces:
  - `subscription_list_identity(sub, user, texts) -> str`
  - `format_subscription_list_line(sub, idx, texts, language, user) -> str`
  - `filter_subscriptions_by_query(subscriptions, query, texts, user) -> list`

- [ ] **Step 1: Write the failing test**

Create `/opt/remnabot1/tests/utils/test_subscription_list_display.py`:

```python
from datetime import UTC, datetime
from types import SimpleNamespace

from app.utils.subscription_list_display import (
    filter_subscriptions_by_query,
    format_subscription_list_line,
    subscription_list_identity,
)


class DummyTexts:
    language = 'fa'

    def t(self, key, default=None):
        return {
            'MY_SUB_DEFAULT_NAME': 'اشتراک',
            'MY_SUB_TRAFFIC_LINE': '   📊 ترافیک: {traffic}',
            'MY_SUB_DEVICES_LINE': '   👥 تعداد کاربر: {devices}',
            'MY_SUB_DEVICES_COUNT_SHORT': '{count} کاربر',
            'MY_SUB_UNTIL_LINE': '   📅 تا: {end_date}',
            'MY_SUB_STATUS_EXPIRED': ' (منقضی)',
            'MY_SUB_STATUS_DISABLED': ' (غیرفعال)',
            'MY_SUB_STATUS_LIMITED': ' (اتمام حجم)',
        }.get(key, default or key)


def _sub(**kwargs):
    base = dict(
        id=1,
        tariff=SimpleNamespace(name='تانل شده (همه نت ها)'),
        actual_status='active',
        traffic_limit_gb=50,
        traffic_used_gb=31.6,
        device_limit=5,
        end_date=datetime(2026, 7, 9, tzinfo=UTC),
        remnawave_short_id='67258',
        purchase_note=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_identity_brand_serial_for_partner() -> None:
    user = SimpleNamespace(is_partner=True, panel_brand_prefix='Moonvpn')
    assert subscription_list_identity(_sub(), user, DummyTexts()) == 'Moonvpn_67258'


def test_identity_falls_back_to_tariff() -> None:
    user = SimpleNamespace(is_partner=False, panel_brand_prefix=None)
    assert 'تانل' in subscription_list_identity(_sub(), user, DummyTexts())


def test_line_is_jalali_fa_and_not_cyrillic() -> None:
    user = SimpleNamespace(is_partner=True, panel_brand_prefix='Moonvpn')
    line = format_subscription_list_line(_sub(), 1, DummyTexts(), 'fa', user)
    assert '18.04.1405' in line
    assert 'کاربر' in line
    assert 'Устройства' not in line
    assert 'Трафик' not in line
    assert 'Moonvpn_67258' in line


def test_search_matches_serial_and_brand() -> None:
    user = SimpleNamespace(is_partner=True, panel_brand_prefix='Moonvpn')
    subs = [_sub(), _sub(id=2, remnawave_short_id='1159', tariff=SimpleNamespace(name='دیگر'))]
    hit = filter_subscriptions_by_query(subs, '67258', DummyTexts(), user)
    assert len(hit) == 1
    hit2 = filter_subscriptions_by_query(subs, 'moonvpn', DummyTexts(), user)
    assert {s.remnawave_short_id for s in hit2} == {'67258'}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/test_subscription_list_display.py -v`

Expected: FAIL (`ModuleNotFoundError: subscription_list_display`)

- [ ] **Step 3: Write minimal implementation**

Create `/opt/remnabot1/app/utils/subscription_list_display.py`:

```python
from __future__ import annotations

from typing import Any

from app.utils.jalali_datetime import format_user_datetime


def _status_emoji(sub: Any) -> str:
    actual = getattr(sub, 'actual_status', None)
    if actual in ('active', 'trial'):
        return '🟢'
    if actual == 'limited':
        return '🟡'
    return '🔴'


def _status_label(sub: Any, texts: Any) -> str:
    actual = getattr(sub, 'actual_status', None)
    if actual == 'expired':
        return texts.t('MY_SUB_STATUS_EXPIRED', ' (Истекла)')
    if actual == 'disabled':
        return texts.t('MY_SUB_STATUS_DISABLED', ' (Отключена)')
    if actual == 'limited':
        return texts.t('MY_SUB_STATUS_LIMITED', ' (Лимит)')
    return ''


def subscription_list_identity(sub: Any, user: Any, texts: Any) -> str:
    brand = (getattr(user, 'panel_brand_prefix', None) or '').strip()
    serial = (getattr(sub, 'remnawave_short_id', '') or '').strip()
    if getattr(user, 'is_partner', False) and brand and serial:
        return f'{brand}_{serial}'
    tariff = getattr(sub, 'tariff', None)
    if tariff and getattr(tariff, 'name', None):
        return str(tariff.name)
    return texts.t('MY_SUB_DEFAULT_NAME', 'Подписка')


def format_subscription_list_line(
    sub: Any,
    idx: int,
    texts: Any,
    language: str,
    user: Any,
) -> str:
    name = subscription_list_identity(sub, user, texts)
    emoji = _status_emoji(sub)
    label = _status_label(sub, texts)
    if getattr(sub, 'traffic_limit_gb', 0) == 0:
        traffic = '∞'
    else:
        used = f'{sub.traffic_used_gb:.1f}' if getattr(sub, 'traffic_used_gb', None) else '0'
        traffic = f'{used}/{sub.traffic_limit_gb} GB'
    devices = ''
    if getattr(sub, 'device_limit', None) is not None:
        count = texts.t('MY_SUB_DEVICES_COUNT_SHORT', '{count} устр.').format(count=sub.device_limit)
        devices = count
    end_date = (
        format_user_datetime(sub.end_date, language=language, fmt='%d.%m.%Y')
        if getattr(sub, 'end_date', None)
        else '—'
    )
    parts = [f'{emoji} <b>{idx}. {name}</b>{label}']
    parts.append(texts.t('MY_SUB_TRAFFIC_LINE', '   📊 Трафик: {traffic}').format(traffic=traffic))
    if devices:
        parts.append(texts.t('MY_SUB_DEVICES_LINE', '   📱 Устройства: {devices}').format(devices=devices))
    parts.append(texts.t('MY_SUB_UNTIL_LINE', '   📅 До: {end_date}').format(end_date=end_date))
    return '\n'.join(parts)


def _matches(sub: Any, query: str, texts: Any, user: Any) -> bool:
    q = (query or '').strip().lower()
    if not q:
        return True
    identity = subscription_list_identity(sub, user, texts).lower()
    if q in identity:
        return True
    if q in str(getattr(sub, 'id', '')):
        return True
    serial = (getattr(sub, 'remnawave_short_id', '') or '').strip().lower()
    if serial and q in serial:
        return True
    note = (getattr(sub, 'purchase_note', None) or '').strip().lower()
    if note and q in note:
        return True
    tariff = getattr(sub, 'tariff', None)
    tariff_name = (getattr(tariff, 'name', None) or '').strip().lower()
    return bool(tariff_name and q in tariff_name)


def filter_subscriptions_by_query(
    subscriptions: list,
    query: str,
    texts: Any,
    user: Any,
) -> list:
    q = (query or '').strip()
    if not q:
        return list(subscriptions)
    return [s for s in subscriptions if _matches(s, q, texts, user)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/test_subscription_list_display.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/utils/subscription_list_display.py tests/utils/test_subscription_list_display.py
git commit -m "feat(day1): subscription list identity, Jalali line, and search filter"
```

---

### Task 5: Wire helper into My Subscriptions (drop hardcoded Cyrillic)

**Files:**
- Modify: `/opt/remnabot1/app/handlers/subscription/my_subscriptions.py`
- Modify: `/opt/remnabot1/tests/handlers/test_my_subscriptions_pagination.py`

**Interfaces:**
- Consumes: `format_subscription_list_line`, `subscription_list_identity`, `get_texts`
- Produces: list caption and gear buttons use helper; `_format_subscription_line` either delegates or is deleted

- [ ] **Step 1: Extend pagination tests (they will fail until the handler changes)**

In `/opt/remnabot1/tests/handlers/test_my_subscriptions_pagination.py`, add a user to `_fake_sub` usage and replace caption builder + add guards. Keep existing pagination tests working by changing `_format_subscription_line` to accept optional texts/user **or** switch caption test to the helper.

Add:

```python
from pathlib import Path

from app.utils.subscription_list_display import format_subscription_list_line


def test_list_source_has_no_hardcoded_cyrillic() -> None:
    src = Path('app/handlers/subscription/my_subscriptions.py').read_text(encoding='utf-8')
    for needle in ('Устройства', 'Мои подписки', 'Трафик:', 'Назад'):
        assert needle not in src, needle


def test_page_caption_uses_helper_and_fits() -> None:
    items = [_fake_sub(i) for i in range(5)]
    user = SimpleNamespace(is_partner=False, panel_brand_prefix=None)

    class T:
        language = 'fa'

        def t(self, key, default=None):
            return default or key

    lines = ['title\n']
    for idx, sub in enumerate(items, 1):
        lines.append(format_subscription_list_line(sub, idx, T(), 'fa', user))
    assert len('\n'.join(lines)) <= 1024
```

Update `test_page_caption_fits_telegram_limit` so it no longer requires the Russian title `Мои подписки`. If it still calls `_format_subscription_line(sub, idx)`, change it to the helper as above **in the same edit as the handler** if the old function signature changes.

- [ ] **Step 2: Run tests to see Cyrillic guard fail**

Run: `uv run pytest tests/handlers/test_my_subscriptions_pagination.py::test_list_source_has_no_hardcoded_cyrillic -v`

Expected: FAIL (`Устройства` / `Мои подписки` still in the handler)

- [ ] **Step 3: Wire the handler**

In `my_subscriptions.py`:

1. Import:

```python
from app.utils.subscription_list_display import (
    format_subscription_list_line,
    subscription_list_identity,
)
```

2. Replace `_format_subscription_line` body with a delegate (keep the name if pagination tests still import it):

```python
def _format_subscription_line(sub, idx: int, texts=None, language: str = 'ru', db_user=None) -> str:
    texts = texts or get_texts(language)
    user = db_user or SimpleNamespace(is_partner=False, panel_brand_prefix=None)
    return format_subscription_list_line(sub, idx, texts, texts.language, user)
```

Add `from types import SimpleNamespace` if used.

3. In `_build_subscriptions_keyboard`, add `db_user=None`. Button label:

```python
label = subscription_list_identity(sub, db_user or SimpleNamespace(is_partner=False), texts)
text=f'⚙️ {label}'
```

Back button:

```python
types.InlineKeyboardButton(text=texts.t('MY_SUB_BACK', '◀️ Назад'), callback_data='back_to_menu')
```

4. In `show_my_subscriptions`, replace hardcoded titles:

```python
if not subscriptions:
    text = texts.t('MY_SUB_LIST_EMPTY', '📋 <b>Мои подписки</b>\n\nУ вас нет подписок.')
else:
    page_items, page, total_pages = paginate_items(subscriptions, page, MY_SUBS_PAGE_SIZE)
    start_idx = (page - 1) * MY_SUBS_PAGE_SIZE
    title = texts.t('MY_SUB_LIST_TITLE', '📋 <b>Мои подписки</b>')
    lines = [f'{title} ({page}/{total_pages})\n']
    for idx, sub in enumerate(page_items, start_idx + 1):
        lines.append(format_subscription_list_line(sub, idx, texts, db_user.language, db_user))
        lines.append('')
    text = '\n'.join(lines)
    keyboard = _build_subscriptions_keyboard(
        page_items,
        db_user.language,
        gift_enabled=gift_enabled,
        page=page,
        total_pages=total_pages,
        db_user=db_user,
    )
```

Pass `db_user` into `_build_subscriptions_keyboard` from the empty-list branch too if it builds buy/gift/back only (no identity).

5. In `show_subscription_detail`, replace Cyrillic status/traffic/device/date strings with `texts.t(...)` and `format_user_datetime(..., language=db_user.language)`. Title uses `subscription_list_identity(subscription, db_user, texts)`.

6. Replace remaining hardcoded `'◀️ К списку подписок'`, `'◀️ Назад'` in this file with `texts.t`.

Do **not** add search in this task.

- [ ] **Step 4: Fix pagination tests for the new keyboard signature**

`_build_subscriptions_keyboard(..., db_user=None)` must remain valid for `test_keyboard_keeps_buy_and_does_not_dump_all_rows`.

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/handlers/test_my_subscriptions_pagination.py tests/utils/test_subscription_list_display.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/handlers/subscription/my_subscriptions.py tests/handlers/test_my_subscriptions_pagination.py
git commit -m "feat(day1): overlay My Subscriptions list chrome via helper"
```

---

### Task 6: Search FSM on My Subscriptions

**Files:**
- Modify: `/opt/remnabot1/app/states.py` (`SubscriptionStates`)
- Modify: `/opt/remnabot1/app/handlers/subscription/my_subscriptions.py`
- Modify: `/opt/remnabot1/app/handlers/subscription/purchase.py` (`register_handlers`)
- Modify: `/opt/remnabot1/tests/handlers/test_my_subscriptions_pagination.py`

**Interfaces:**
- Consumes: `filter_subscriptions_by_query`; FSM key `my_subs_search_query`
- Produces: callbacks `my_subs_search`, `my_subs_search_reset`; state `SubscriptionStates.searching_my_subscriptions`

- [ ] **Step 1: Write failing keyboard test**

Append to `test_my_subscriptions_pagination.py`:

```python
def test_keyboard_includes_search_and_keeps_gift() -> None:
    page_items = [_fake_sub(i) for i in range(1, 3)]
    keyboard = _build_subscriptions_keyboard(
        page_items,
        'fa',
        gift_enabled=True,
        page=1,
        total_pages=1,
        show_search=True,
    )
    callbacks = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert 'my_subs_search' in callbacks
    assert 'subscription_gift' in callbacks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/handlers/test_my_subscriptions_pagination.py::test_keyboard_includes_search_and_keeps_gift -v`

Expected: FAIL (`TypeError` unknown kwarg `show_search` or missing callback)

- [ ] **Step 3: Implement search**

`states.py` — inside `SubscriptionStates`:

```python
    searching_my_subscriptions = State()
```

`_build_subscriptions_keyboard`: add `show_search: bool = False`, `search_query: str = ''`. After the buy row, if `show_search`:

```python
if search_query:
    buttons.append([
        types.InlineKeyboardButton(
            text=texts.t('MY_SUB_SEARCH_RESET', '❌ Сбросить поиск'),
            callback_data='my_subs_search_reset',
        )
    ])
else:
    buttons.append([
        types.InlineKeyboardButton(
            text=texts.t('MY_SUB_SEARCH', '🔍 Поиск'),
            callback_data='my_subs_search',
        )
    ])
```

`show_my_subscriptions`: read FSM:

```python
search_query = ''
if state:
    data = await state.get_data()
    search_query = (data.get('my_subs_search_query') or '').strip()
from app.utils.subscription_list_display import filter_subscriptions_by_query
visible = (
    filter_subscriptions_by_query(subscriptions, search_query, texts, db_user)
    if search_query
    else subscriptions
)
```

Paginate `visible`, not the unfiltered list. If `search_query` and not `visible`, show `MY_SUB_SEARCH_NO_RESULTS` plus reset. Pass `show_search=True`, `search_query=search_query` into the keyboard.

Add handlers in `my_subscriptions.py`:

```python
async def start_my_subs_search(callback, db_user, db, state: FSMContext):
    texts = get_texts(db_user.language)
    await callback.answer()
    await state.set_state(SubscriptionStates.searching_my_subscriptions)
    await callback.message.answer(texts.t('MY_SUB_SEARCH_PROMPT', 'Введите текст поиска'))


async def reset_my_subs_search(callback, db_user, db, state: FSMContext):
    await state.update_data(my_subs_search_query=None)
    await show_my_subscriptions(callback, db_user, db, state)


async def receive_my_subs_search(message: types.Message, db_user, db, state: FSMContext):
    texts = get_texts(db_user.language)
    raw = (message.text or '').strip()
    if not raw:
        await message.answer(texts.t('MY_SUB_SEARCH_EMPTY_QUERY', '❌ Введите текст'))
        return
    await state.update_data(my_subs_search_query=raw)
    await state.set_state(None)
    await message.answer(texts.t('MY_SUB_SEARCH_ACTIVE', 'Поиск: {query}').format(query=raw))
```

Empty query / lost state: keyed messages from Task 3; do not crash.

In `purchase.py` `register_handlers`, after `ms_pg:`:

```python
from app.handlers.subscription.my_subscriptions import (
    receive_my_subs_search,
    reset_my_subs_search,
    start_my_subs_search,
)
from app.states import SubscriptionStates

dp.callback_query.register(start_my_subs_search, F.data == 'my_subs_search')
dp.callback_query.register(reset_my_subs_search, F.data == 'my_subs_search_reset')
dp.message.register(receive_my_subs_search, SubscriptionStates.searching_my_subscriptions)
```

Export the new functions from `app/handlers/subscription/__init__.py` only if that module already re-exports `show_my_subscriptions` and a test imports from there; otherwise skip.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/handlers/test_my_subscriptions_pagination.py tests/utils/test_subscription_list_display.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/states.py app/handlers/subscription/my_subscriptions.py app/handlers/subscription/purchase.py tests/handlers/test_my_subscriptions_pagination.py
git commit -m "feat(day1): My Subscriptions search overlay on 4.2 list"
```

---

### Task 7: Rich `/start` Jalali + purchase expire date

**Files:**
- Modify: `/opt/remnabot1/app/utils/rich_menu.py` (`_build_subscriptions_table`, ~403–410)
- Modify: `/opt/remnabot1/app/handlers/subscription/purchase.py` (~563 `expire_date = purchase.expires_at.strftime`)
- Modify: `/opt/remnabot1/tests/utils/test_rich_menu.py`

**Interfaces:**
- Consumes: `format_user_datetime`; `texts.language`
- Produces: table fallback string Jalali for `fa`; keyboard structure unchanged

- [ ] **Step 1: Write failing rich-menu test**

In `tests/utils/test_rich_menu.py` add (reuse `_make_subscription` already in that file):

```python
def test_subscriptions_table_fa_fallback_is_jalali():
    from datetime import UTC, datetime, timedelta

    class FaTexts(DummyTexts):
        language = 'fa'

    now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    sub = _make_subscription(now, tariff_name='Plan-A')
    sub.end_date = datetime(2026, 7, 9, tzinfo=UTC)
    html_out = rich_menu._build_subscriptions_table([sub], FaTexts())
    assert '18.04.1405' in html_out
```

If `_make_subscription` forces `end_date = now + timedelta(...)`, set `end_date` after as above. If the helper name differs, use the same factory the file already uses for `_build_subscriptions_table`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/test_rich_menu.py::test_subscriptions_table_fa_fallback_is_jalali -v`

Expected: FAIL (Gregorian `09.07.2026` from `format_local_datetime`)

- [ ] **Step 3: Implement**

`rich_menu.py`:

```python
from app.utils.jalali_datetime import format_user_datetime
```

Replace the fallback line in `_build_subscriptions_table`:

```python
end_date_text = (
    format_user_datetime(end_date, language=getattr(texts, 'language', 'ru'), fmt='%d.%m.%Y')
    if end_date
    else ''
)
```

Keep `_tg_time(...)` as-is (client timezone widget). Wrap formatting in try/except `Exception` and fall back to `format_local_datetime` so `/start` cannot crash.

`purchase.py` around the gift/expire strftime:

```python
from app.utils.jalali_datetime import format_user_datetime
expire_date = format_user_datetime(
    purchase.expires_at, language=db_user.language, fmt='%d.%m.%Y'
)
```

Use the actual local variable name for the user in that function (`db_user` or `user`).

Do **not** add 3.60 grid buttons. Do **not** change callback_data `menu_subscription` / `menu_balance`.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/utils/test_rich_menu.py tests/utils/test_jalali_datetime.py -v`

Expected: PASS. Existing `test_build_subscriptions_table` still looks for `[MAIN_MENU_RICH_DAYS_LEFT]` with `DummyTexts.language = 'ru'`.

- [ ] **Step 5: Commit**

```bash
git add app/utils/rich_menu.py app/handlers/subscription/purchase.py tests/utils/test_rich_menu.py
git commit -m "feat(day1): Jalali fallback on rich-menu table and purchase expire date"
```

---

### Task 8: Partner checkout overlay (Telegram confirm)

**Files:**
- Create: `/opt/remnabot1/app/utils/remnawave_panel_identity.py`
- Create: `/opt/remnabot1/app/utils/partner_checkout_telegram.py`
- Modify: `/opt/remnabot1/app/states.py`
- Modify: `/opt/remnabot1/app/handlers/subscription/tariff_purchase.py` (`get_tariff_confirm_keyboard`, confirm screen ~1698, `confirm_tariff_purchase`)
- Modify: `/opt/remnabot1/app/handlers/subscription/purchase.py` (register note/brand callbacks)
- Test: `/opt/remnabot1/tests/utils/test_partner_checkout_telegram.py`

**Interfaces:**
- Consumes: `User.is_partner`, `User.panel_brand_prefix`, `Subscription.purchase_note`
- Produces:
  - `validate_brand_prefix(raw: str) -> str | None`
  - `sanitize_purchase_note(value: str | None) -> str | None`
  - `checkout_partner_options(user, state_data) -> dict`
  - `extend_confirm_keyboard(buttons, user, tariff_id, period, texts) -> list`
  - `apply_partner_checkout_from_state(db, user, subscription, state_data) -> None` (no-op if not partner or fields missing)

- [ ] **Step 1: Write failing tests**

Create `/opt/remnabot1/tests/utils/test_partner_checkout_telegram.py`:

```python
from types import SimpleNamespace

from app.utils.partner_checkout_telegram import (
    checkout_partner_options,
    extend_confirm_keyboard,
    sanitize_purchase_note,
)
from app.utils.remnawave_panel_identity import validate_brand_prefix


def test_validate_brand_prefix() -> None:
    assert validate_brand_prefix('Moonvpn') == 'Moonvpn'
    assert validate_brand_prefix('ab') is None


def test_options_fail_open_without_partner() -> None:
    user = SimpleNamespace(is_partner=False, panel_brand_prefix='Moonvpn')
    opts = checkout_partner_options(user, {'purchase_note': 'x', 'use_brand_prefix': True})
    assert opts['use_brand_prefix'] is False


class DummyTexts:
    def t(self, key, default=None):
        return default or key


def test_extend_keyboard_noop_for_non_partner() -> None:
    user = SimpleNamespace(is_partner=False, panel_brand_prefix=None)
    buttons = [['confirm']]
    assert extend_confirm_keyboard(buttons, user, 1, 30, DummyTexts()) == buttons
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/utils/test_partner_checkout_telegram.py -v`

Expected: FAIL (import error)

- [ ] **Step 3: Implement helpers**

`/opt/remnabot1/app/utils/remnawave_panel_identity.py`:

```python
from __future__ import annotations

import re

MAX_PURCHASE_NOTE_LEN = 500
BRAND_PREFIX_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,20}$')


def validate_brand_prefix(raw: str | None) -> str | None:
    value = (raw or '').strip()
    if not BRAND_PREFIX_PATTERN.fullmatch(value):
        return None
    return value
```

`/opt/remnabot1/app/utils/partner_checkout_telegram.py`:

```python
from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton

from app.utils.remnawave_panel_identity import MAX_PURCHASE_NOTE_LEN, validate_brand_prefix


def sanitize_purchase_note(value: str | None) -> str | None:
    note = (value or '').strip()
    if not note:
        return None
    return note[:MAX_PURCHASE_NOTE_LEN]


def checkout_partner_options(user: Any, state_data: dict) -> dict:
    if not getattr(user, 'is_partner', False):
        return {'purchase_note': None, 'use_brand_prefix': False, 'has_brand_prefix': False}
    if not hasattr(user, 'panel_brand_prefix'):
        return {'purchase_note': None, 'use_brand_prefix': False, 'has_brand_prefix': False}
    has_brand = bool((getattr(user, 'panel_brand_prefix', None) or '').strip())
    use_brand = state_data.get('use_brand_prefix')
    if use_brand is None:
        use_brand = has_brand
    return {
        'purchase_note': sanitize_purchase_note(state_data.get('purchase_note')),
        'use_brand_prefix': bool(use_brand) if has_brand else False,
        'has_brand_prefix': has_brand,
    }


def extend_confirm_keyboard(buttons: list, user: Any, tariff_id: int, period: int) -> list:
    if not getattr(user, 'is_partner', False) or not hasattr(user, 'panel_brand_prefix'):
        return buttons
    extra = [
        [InlineKeyboardButton(text='📝', callback_data=f'pnote:{tariff_id}:{period}')],
        [InlineKeyboardButton(text='🏷', callback_data=f'pbrand:{tariff_id}:{period}')],
    ]
    # Insert before the last row (Back)
    return buttons[:-1] + extra + buttons[-1:]
```

Use `texts.t` for button labels inside `extend_confirm_keyboard` by passing `language` if tests stay icon-only; for production, pass `get_texts` into the extender:

```python
def extend_confirm_keyboard(buttons, user, tariff_id, period, texts) -> list:
    ...
    extra = [
        [InlineKeyboardButton(text=texts.t('PARTNER_PURCHASE_NOTE_BTN', '📝'), callback_data=f'pnote:{tariff_id}:{period}')],
        [InlineKeyboardButton(text=texts.t('PARTNER_BRAND_TOGGLE_ON' if opts['use_brand_prefix'] else 'PARTNER_BRAND_TOGGLE_OFF', '🏷'), callback_data=f'pbrand:{tariff_id}:{period}')],
    ]
```

Update the unit test to pass a DummyTexts. Keep fail-open: if `panel_brand_prefix` is missing on the class, return `buttons` unchanged.

- [ ] **Step 4: Hook tariff confirm**

`get_tariff_confirm_keyboard` — add optional `db_user=None`. After building `buttons`, if `db_user` is not None:

```python
from app.utils.partner_checkout_telegram import extend_confirm_keyboard
buttons = extend_confirm_keyboard(buttons, db_user, tariff_id, period, texts)
```

At the confirm **display** callsite (~1698) pass `db_user=db_user`. Leave other callsites working (`db_user` default None = no extra buttons).

`states.py`:

```python
    waiting_for_purchase_note = State()
```

Add handlers in `partner_checkout_telegram.py` or `my_subscriptions.py` is the wrong file — put handlers in `/opt/remnabot1/app/handlers/subscription/partner_checkout.py` (new, thin):

- `pnote:{tariff_id}:{period}` → set state, prompt `PARTNER_PURCHASE_NOTE_PROMPT`
- message in that state → `state.update_data(purchase_note=sanitize...)` → re-show confirm
- `pbrand:{tariff_id}:{period}` → toggle `use_brand_prefix` in FSM → re-show confirm

Register those in `purchase.py` `register_handlers`.

In `confirm_tariff_purchase`, after the subscription row exists (the `existing_sub` or newly created sub variable in that function — use the name the function already uses for the saved subscription), call:

```python
from app.utils.partner_checkout_telegram import apply_partner_checkout_from_state

state_data = await state.get_data()
await apply_partner_checkout_from_state(db, db_user, saved_sub, state_data)
```

Implement `apply_partner_checkout_from_state`:

```python
async def apply_partner_checkout_from_state(db, user, subscription, state_data: dict) -> None:
    if subscription is None or not getattr(user, 'is_partner', False):
        return
    if not hasattr(subscription, 'purchase_note'):
        return
    opts = checkout_partner_options(user, state_data)
    subscription.purchase_note = opts['purchase_note']
    if opts['use_brand_prefix'] is False:
        return
    # prefix already on user; nothing else if validate would fail
```

Do not reimplement `PricingEngine`. Do not touch cabinet forms.

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/utils/test_partner_checkout_telegram.py tests/test_tariff_insufficient_balance_keyboard.py -v`

Expected: PASS (`get_tariff_confirm_keyboard` extra optional arg must not break existing tests)

- [ ] **Step 6: Commit**

```bash
git add app/utils/remnawave_panel_identity.py app/utils/partner_checkout_telegram.py app/handlers/subscription/partner_checkout.py app/handlers/subscription/tariff_purchase.py app/handlers/subscription/purchase.py app/states.py tests/utils/test_partner_checkout_telegram.py
git commit -m "feat(day1): partner note and brand overlay on 4.2 tariff confirm"
```

---

### Task 9: Telegram pause (`user_disabled`)

**Files:**
- Create: `/opt/remnabot1/app/services/subscription_user_toggle_service.py`
- Modify: `/opt/remnabot1/app/handlers/subscription/my_subscriptions.py` (`_build_subscription_detail_keyboard`, new handlers)
- Modify: `/opt/remnabot1/app/handlers/subscription/purchase.py` (register `sub_disable:` / `sub_enable:`)
- Test: `/opt/remnabot1/tests/services/test_subscription_user_toggle.py`

**Interfaces:**
- Consumes: `Subscription.user_disabled`, `Subscription.remnawave_id` (int, 3.x), `deactivate_subscription`, `reactivate_subscription`, `SubscriptionService.disable_remnawave_user` / `enable_remnawave_user`
- Produces: `disable_user_subscription`, `enable_user_subscription`, `SubscriptionToggleError`

- [ ] **Step 1: Write failing tests**

Create `/opt/remnabot1/tests/services/test_subscription_user_toggle.py`:

```python
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.subscription_user_toggle_service import (
    SubscriptionToggleError,
    disable_user_subscription,
)


@pytest.mark.asyncio
async def test_disable_rejects_expired() -> None:
    sub = SimpleNamespace(actual_status='expired', user_disabled=False)
    with pytest.raises(SubscriptionToggleError) as exc:
        await disable_user_subscription(AsyncMock(), sub, SimpleNamespace())
    assert exc.value.code == 'not_active'


@pytest.mark.asyncio
async def test_disable_sets_flag_and_calls_panel() -> None:
    sub = SimpleNamespace(
        actual_status='active',
        user_disabled=False,
        remnawave_id=99,
        is_daily_tariff=False,
        id=1,
        user_id=2,
    )
    db = AsyncMock()
    with (
        patch(
            'app.services.subscription_user_toggle_service.deactivate_subscription',
            new_callable=AsyncMock,
        ) as deact,
        patch(
            'app.services.subscription_user_toggle_service.SubscriptionService'
        ) as svc_cls,
    ):
        svc_cls.return_value.disable_remnawave_user = AsyncMock(return_value=True)
        result = await disable_user_subscription(db, sub, SimpleNamespace(id=2))
    assert result.user_disabled is True
    deact.assert_awaited()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/services/test_subscription_user_toggle.py -v`

Expected: FAIL (import error)

- [ ] **Step 3: Implement service**

Port donor logic but **use numeric `subscription.remnawave_id`**, not uuid:

```python
panel_id = getattr(subscription, 'remnawave_id', None)
if panel_id:
    ok = await SubscriptionService().disable_remnawave_user(int(panel_id), db=db)
```

Match donor rules: only `active`/`trial`/`limited` can disable; enable only when `user_disabled` and not expired. On panel failure raise `SubscriptionToggleError('panel_error', ...)`.

Hide the button when `not hasattr(subscription, 'user_disabled')`.

- [ ] **Step 4: Wire detail keyboard + handlers**

In `_build_subscription_detail_keyboard`, after building the inactive/active rows, if `sub is not None and hasattr(sub, 'user_disabled')` and `sub.actual_status in ('active', 'trial', 'limited')`:

```python
if getattr(sub, 'user_disabled', False):
    # enable-only keyboard (donor behavior): enable + back
else:
    buttons.append([types.InlineKeyboardButton(
        text=texts.t('MY_SUB_BTN_DISABLE', '⏸'),
        callback_data=f'sub_disable:{sub_id}',
    )])
```

Pass `language` into this builder (it currently has no language — add `language: str = 'ru'` and `get_texts(language)` for the new labels). Existing Russian button strings can stay for this task **except** the new pause labels, or replace them if the Cyrillic guard from Task 5 already forbids remaining Cyrillic in this file.

Handlers `handle_subscription_user_disable` / `handle_subscription_user_enable`: `callback.answer()` first, then service, then `show_subscription_detail`.

Register in `purchase.py`:

```python
dp.callback_query.register(handle_subscription_user_disable, F.data.startswith('sub_disable:'))
dp.callback_query.register(handle_subscription_user_enable, F.data.startswith('sub_enable:'))
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/services/test_subscription_user_toggle.py tests/handlers/test_my_subscriptions_pagination.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/subscription_user_toggle_service.py app/handlers/subscription/my_subscriptions.py app/handlers/subscription/purchase.py tests/services/test_subscription_user_toggle.py
git commit -m "feat(day1): Telegram pause/resume via user_disabled"
```

---

### Task 10: Joint day-1 operator smoke (no code)

**Files:** none in remnabot1 app. Optional evidence note under `docs/superpowers/evidence/` only if the operator asks to record PASS.

**Depends on:** Tasks 1–9 **and** cabinet Layer A plan (`docs/superpowers/plans/2026-09-03-cabinet-layer-a-user-ui.md`) on `/opt/cabinet`.

Do **not** start M7. Do **not** use the production bot token. RC bot is the test token / `@mrj7_bot`.

- [ ] **Step 1: Telegram `/start`**

On the RC test bot: rich 4.2 shell still shows Connect / Subscription / Balance (not the 3.60 grid). Chrome is Persian. Subscription preview fallback date is Jalali for fa. Balance is Toman (already ported).

- [ ] **Step 2: My Subscriptions**

Opens paginated list. Title Persian with page/total. Lines use ترافیک / تعداد کاربر / Jalali. Search button works. Gift button still present. If the account has `panel_brand_prefix` + serial, identity looks like `Moonvpn_67258`.

- [ ] **Step 3: Pause (if an active test sub exists)**

Detail shows pause. Toggle does not crash. Skip if no safe test subscription.

- [ ] **Step 4: Partner confirm (optional)**

If an **isolated** approved partner test account exists: confirm keyboard shows note/brand; purchase still uses `PricingEngine` wholesale. Skip if no such account — do not use production C2C admin chat.

- [ ] **Step 5: Cabinet**

`https://panel.rookari.com` first paint fa/RTL, Jalali, wording, subscription sheets — per Layer A smoke map. If Layer A is not finished, report **INCOMPLETE** for the web half; do not block recording Telegram PASS separately.

- [ ] **Step 6: Stop**

Do not start M7-T1 from this smoke. Next cutover pointer remains the MVP plan named-start.

---

## Self-review (author)

| Spec requirement | Task |
|---|---|
| Keep 4.2 rich `/start` | 7 (strings/dates only); 10 verifies callbacks |
| Jalali on rich preview + list + purchase date | 1, 4, 5, 7 |
| My Subs search, page/total, brand+serial, تعداد کاربر | 3, 4, 5, 6 |
| Gift stays | 6 test |
| No 3.60 file replace | 5 overlay |
| ORM map 0095/0103, no autogenerate | 2 |
| Partner confirm overlay, fail-open | 8 |
| Pause Telegram only | 9 |
| Cabinet Layer A | existing plan; Task 10 |
| No M7 / Layer C | Global constraints + Task 10 |

No TBD remaining. Helper signatures in Tasks 5–6 match Task 4. Pause uses `remnawave_id` (4.2 / Remnawave 3.x), not donor uuid.
