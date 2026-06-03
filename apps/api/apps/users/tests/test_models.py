"""Users + ConsumerProfile tests."""

import pytest

from apps.users.factories import ConsumerProfileFactory, UserFactory


@pytest.mark.django_db
def test_user_factory_creates_consumer():
    user = UserFactory()
    assert user.pk is not None
    assert user.role == "consumer"
    assert user.check_password("test-pass-123")


@pytest.mark.django_db
def test_consumer_profile_autogenerates_referral_code():
    profile = ConsumerProfileFactory()
    assert profile.referral_code.startswith("YAPA")
    assert len(profile.referral_code) == 7


@pytest.mark.django_db
def test_referral_codes_are_unique():
    p1 = ConsumerProfileFactory()
    p2 = ConsumerProfileFactory()
    assert p1.referral_code != p2.referral_code
