import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from api.models import (
  Good,
  Follow,
  Haiku,
  validate_avatar_size,
  MAX_AVATAR_SIZE_BYTES,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserManager:
  def test_create_user_normal(self):
    user = User.objects.create_user(
      email='a@example.com', password='pass12345', username='alice'
    )
    assert user.email == 'a@example.com'
    assert user.username == 'alice'
    assert user.check_password('pass12345')
    assert user.is_active is True
    assert user.is_staff is False

  def test_create_user_without_email_raises(self):
    with pytest.raises(ValueError):
      User.objects.create_user(email='', password='pass12345')

  def test_create_superuser_sets_staff_and_superuser(self):
    admin = User.objects.create_superuser(
      email='admin@example.com', password='pass12345'
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True


class TestValidateAvatarSize:
  def test_file_within_limit_is_accepted(self):
    fake_file = type('FakeFile', (), {'size': MAX_AVATAR_SIZE_BYTES})()
    # 例外が起きないことを確認する
    validate_avatar_size(fake_file)

  def test_file_over_limit_raises(self):
    fake_file = type('FakeFile', (), {'size': MAX_AVATAR_SIZE_BYTES + 1})()
    with pytest.raises(ValidationError):
      validate_avatar_size(fake_file)


class TestHaikuModel:
  def test_default_is_public_true(self, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='古池や蛙飛び込む水の音')
    assert haiku.is_public is True


class TestGoodModel:
  def test_duplicate_good_violates_unique_constraint(self, user_factory):
    author = user_factory()
    liker = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='古池や蛙飛び込む水の音')
    Good.objects.create(user=liker, haiku=haiku)
    with pytest.raises(IntegrityError):
      Good.objects.create(user=liker, haiku=haiku)


class TestFollowModel:
  def test_duplicate_follow_violates_unique_constraint(self, user_factory):
    follower = user_factory()
    following = user_factory()
    Follow.objects.create(follower=follower, following=following)
    with pytest.raises(IntegrityError):
      Follow.objects.create(follower=follower, following=following)
