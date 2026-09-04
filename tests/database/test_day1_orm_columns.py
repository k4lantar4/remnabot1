from app.database.models import Subscription, User


def test_user_has_panel_brand_prefix() -> None:
    assert hasattr(User, 'panel_brand_prefix')


def test_subscription_has_purchase_note_and_user_disabled() -> None:
    assert hasattr(Subscription, 'purchase_note')
    assert hasattr(Subscription, 'user_disabled')
