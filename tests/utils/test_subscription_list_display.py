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
