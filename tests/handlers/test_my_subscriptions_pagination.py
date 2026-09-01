"""My Subscriptions must paginate; dumping every row overflows Telegram captions.

M6-T5: admin 1713374557 has 116 subscriptions. show_my_subscriptions sent them
all into a logo-mode photo caption → TelegramBadRequest message/caption too long.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.handlers.subscription.my_subscriptions import (
    MY_SUBS_PAGE_SIZE,
    _build_subscriptions_keyboard,
    _format_subscription_line,
    paginate_items,
    parse_my_subs_page,
)


def _fake_sub(i: int):
    return SimpleNamespace(
        id=i,
        tariff=SimpleNamespace(name=f'Tariff {i}'),
        actual_status='active',
        traffic_limit_gb=10,
        traffic_used_gb=1.0,
        device_limit=1,
        end_date=datetime(2026, 12, 1, tzinfo=UTC),
    )


def test_parse_my_subs_page_defaults_and_ms_pg() -> None:
    assert parse_my_subs_page('my_subscriptions') == 1
    assert parse_my_subs_page('menu_subscription') == 1
    assert parse_my_subs_page('ms_pg:3') == 3
    assert parse_my_subs_page('ms_pg:0') == 1
    assert parse_my_subs_page('ms_pg:nope') == 1


def test_paginate_116_subscriptions_fits_page_size() -> None:
    items = [_fake_sub(i) for i in range(116)]
    page_items, page, total_pages = paginate_items(items, 1, MY_SUBS_PAGE_SIZE)
    assert page == 1
    assert total_pages == 24
    assert len(page_items) == MY_SUBS_PAGE_SIZE
    last, last_page, _ = paginate_items(items, 99, MY_SUBS_PAGE_SIZE)
    assert last_page == 24
    assert len(last) == 1


def test_page_caption_fits_telegram_limit() -> None:
    items = [_fake_sub(i) for i in range(116)]
    page_items, _, total_pages = paginate_items(items, 1, MY_SUBS_PAGE_SIZE)
    lines = [f'📋 <b>Мои подписки</b> (1/{total_pages})\n']
    for idx, sub in enumerate(page_items, 1):
        lines.append(_format_subscription_line(sub, idx))
        lines.append('')
    text = '\n'.join(lines)
    assert len(text) <= 1024


def test_keyboard_keeps_buy_and_does_not_dump_all_rows() -> None:
    page_items = [_fake_sub(i) for i in range(1, 6)]
    keyboard = _build_subscriptions_keyboard(
        page_items,
        'fa',
        gift_enabled=False,
        page=1,
        total_pages=24,
    )
    callbacks = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert 'menu_buy' in callbacks
    assert 'ms_pg:2' in callbacks
    assert 'ms_pg:1' not in callbacks
    assert len(callbacks) < 20
    assert all(cb != 'sm:100' for cb in callbacks)
