from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.subscription_user_toggle_service import (
    SubscriptionToggleError,
    disable_user_subscription,
    enable_user_subscription,
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
        patch('app.services.subscription_user_toggle_service.SubscriptionService') as svc_cls,
    ):
        svc_cls.return_value.disable_remnawave_user = AsyncMock(return_value=True)
        result = await disable_user_subscription(db, sub, SimpleNamespace(id=2))
    assert result.user_disabled is True
    deact.assert_awaited()
    svc_cls.return_value.disable_remnawave_user.assert_awaited_once_with(99, db=db)


@pytest.mark.asyncio
async def test_disable_panel_failure_raises() -> None:
    sub = SimpleNamespace(
        actual_status='active',
        user_disabled=False,
        remnawave_id=99,
        is_daily_tariff=False,
        id=1,
        user_id=2,
    )
    with (
        patch(
            'app.services.subscription_user_toggle_service.deactivate_subscription',
            new_callable=AsyncMock,
        ),
        patch('app.services.subscription_user_toggle_service.SubscriptionService') as svc_cls,
    ):
        svc_cls.return_value.disable_remnawave_user = AsyncMock(return_value=False)
        with pytest.raises(SubscriptionToggleError) as exc:
            await disable_user_subscription(AsyncMock(), sub, SimpleNamespace(id=2))
    assert exc.value.code == 'panel_error'


@pytest.mark.asyncio
async def test_enable_rejects_not_user_disabled() -> None:
    sub = SimpleNamespace(user_disabled=False, status='disabled', end_date=datetime.now(UTC) + timedelta(days=1))
    with pytest.raises(SubscriptionToggleError) as exc:
        await enable_user_subscription(AsyncMock(), sub, SimpleNamespace())
    assert exc.value.code == 'not_user_disabled'


@pytest.mark.asyncio
async def test_enable_rejects_expired() -> None:
    sub = SimpleNamespace(
        user_disabled=True,
        status='disabled',
        end_date=datetime.now(UTC) - timedelta(days=1),
    )
    with pytest.raises(SubscriptionToggleError) as exc:
        await enable_user_subscription(AsyncMock(), sub, SimpleNamespace())
    assert exc.value.code == 'expired'


@pytest.mark.asyncio
async def test_enable_sets_flag_and_calls_panel() -> None:
    sub = SimpleNamespace(
        user_disabled=True,
        status='disabled',
        remnawave_id=99,
        is_daily_tariff=False,
        end_date=datetime.now(UTC) + timedelta(days=7),
        id=1,
        user_id=2,
    )
    db = AsyncMock()
    with (
        patch(
            'app.services.subscription_user_toggle_service.reactivate_subscription',
            new_callable=AsyncMock,
        ) as react,
        patch('app.services.subscription_user_toggle_service.SubscriptionService') as svc_cls,
    ):
        svc_cls.return_value.enable_remnawave_user = AsyncMock(return_value=True)
        result = await enable_user_subscription(db, sub, SimpleNamespace(id=2))
    assert result.user_disabled is False
    react.assert_awaited()
    svc_cls.return_value.enable_remnawave_user.assert_awaited_once_with(99, db=db)
