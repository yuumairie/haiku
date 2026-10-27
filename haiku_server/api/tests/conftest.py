import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
  return APIClient()


@pytest.fixture
def user_factory(db):
  """テストユーザーを作るファクトリ。呼ぶたびに別のユーザーを1人作る。"""
  created = []

  def _create(email=None, password='pass12345', username=None, **kwargs):
    n = len(created) + 1
    user = User.objects.create_user(
      email=email or f'user{n}@example.com',
      password=password,
      username=username if username is not None else f'user{n}',
      **kwargs,
    )
    created.append(user)
    return user

  return _create


@pytest.fixture
def user(user_factory):
  return user_factory()


@pytest.fixture
def other_user(user_factory):
  return user_factory()


@pytest.fixture
def auth_client(api_client, user):
  """認証済みユーザー(user)としてリクエストするAPIClient。
  JWT発行そのものの検証はtest_auth.pyで別途行うので、ここでは
  force_authenticateで直接認証済み状態を作り、各テストの本題
  (パーミッションや業務ロジック)に集中できるようにする。"""
  api_client.force_authenticate(user=user)
  return api_client
