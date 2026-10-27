import pytest
from django.db import IntegrityError

from api.models import Follow

pytestmark = pytest.mark.django_db


class TestFollowViewSet:
  def test_create_requires_authentication(self, api_client, user_factory):
    target = user_factory()
    response = api_client.post('/api/follows/', {'following': target.id})
    assert response.status_code == 401

  def test_create_normal_sets_follower(self, auth_client, user, other_user):
    response = auth_client.post('/api/follows/', {'following': other_user.id})

    assert response.status_code == 201
    assert Follow.objects.filter(follower=user, following=other_user).exists()

  def test_cannot_follow_self(self, auth_client, user):
    response = auth_client.post('/api/follows/', {'following': user.id})

    assert response.status_code == 400
    assert not Follow.objects.filter(follower=user, following=user).exists()

  def test_duplicate_follow_raises_integrity_error(self, auth_client, user, other_user):
    # FollowSerializerは自己フォローだけ明示的にバリデーションしており、
    # 重複フォローに対するアプリ側のバリデーションは無いため、DBの
    # UniqueConstraint由来のIntegrityErrorがそのまま発生する。
    Follow.objects.create(follower=user, following=other_user)

    with pytest.raises(IntegrityError):
      auth_client.post('/api/follows/', {'following': other_user.id})

  def test_delete_by_follower_succeeds(self, auth_client, user, other_user):
    follow = Follow.objects.create(follower=user, following=other_user)

    response = auth_client.delete(f'/api/follows/{follow.id}/')

    assert response.status_code == 204
    assert not Follow.objects.filter(id=follow.id).exists()

  def test_delete_by_non_follower_is_forbidden(
    self, auth_client, other_user, user_factory
  ):
    bystander = user_factory()
    follow = Follow.objects.create(follower=bystander, following=other_user)

    response = auth_client.delete(f'/api/follows/{follow.id}/')

    assert response.status_code == 403
    assert Follow.objects.filter(id=follow.id).exists()

  def test_filter_by_follower(self, auth_client, user, other_user, user_factory):
    unrelated = user_factory()
    Follow.objects.create(follower=user, following=other_user)
    Follow.objects.create(follower=unrelated, following=other_user)

    response = auth_client.get('/api/follows/', {'follower': user.id})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['follower']['id'] == user.id
