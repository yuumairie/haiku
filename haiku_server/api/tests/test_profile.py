import pytest

from api.models import Profile

pytestmark = pytest.mark.django_db


class TestProfileViewSet:
  def test_create_requires_authentication(self, api_client):
    response = api_client.post('/api/profiles/', {'nickName': 'ニックネーム'})
    assert response.status_code == 401

  def test_create_normal_sets_owner(self, auth_client, user):
    response = auth_client.post('/api/profiles/', {'nickName': 'わたし'})

    assert response.status_code == 201
    profile = Profile.objects.get(id=response.data['id'])
    assert profile.userProfile == user

  def test_list_can_be_filtered_by_user_profile(self, api_client, user_factory):
    a = user_factory()
    b = user_factory()
    Profile.objects.create(userProfile=a, nickName='Aのニックネーム')
    Profile.objects.create(userProfile=b, nickName='Bのニックネーム')

    response = api_client.get('/api/profiles/', {'userProfile': a.id})

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['nickName'] == 'Aのニックネーム'

  def test_update_by_non_owner_is_forbidden(self, auth_client, other_user):
    profile = Profile.objects.create(userProfile=other_user, nickName='他人の名前')

    response = auth_client.patch(f'/api/profiles/{profile.id}/', {'nickName': '書き換え'})

    assert response.status_code == 403

  def test_update_by_owner_succeeds(self, auth_client, user):
    profile = Profile.objects.create(userProfile=user, nickName='元の名前')

    response = auth_client.patch(f'/api/profiles/{profile.id}/', {'nickName': '新しい名前'})

    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.nickName == '新しい名前'

  def test_read_does_not_require_authentication(self, api_client, user):
    profile = Profile.objects.create(userProfile=user, nickName='誰でも見れる')

    response = api_client.get(f'/api/profiles/{profile.id}/')

    assert response.status_code == 200


class TestMyProfileListView:
  def test_returns_only_the_logged_in_user(self, auth_client, user, other_user):
    response = auth_client.get('/api/myprofile/')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == user.id

  def test_requires_authentication(self, api_client):
    response = api_client.get('/api/myprofile/')
    assert response.status_code == 401


class TestMyProfileUpdateView:
  def test_get_returns_own_user(self, auth_client, user):
    response = auth_client.get('/api/me/')

    assert response.status_code == 200
    assert response.data['id'] == user.id

  def test_patch_updates_own_username(self, auth_client, user):
    response = auth_client.patch('/api/me/', {'username': '新しい表示名'})

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.username == '新しい表示名'

  def test_patch_blank_username_is_rejected(self, auth_client):
    response = auth_client.patch('/api/me/', {'username': ''})
    assert response.status_code == 400

  def test_requires_authentication(self, api_client):
    response = api_client.get('/api/me/')
    assert response.status_code == 401


class TestUserSearchView:
  def test_search_by_username_does_not_require_authentication(
    self, api_client, user_factory
  ):
    user_factory(username='はるか')
    user_factory(username='なつき')

    response = api_client.get('/api/users/', {'username': 'はる'})

    assert response.status_code == 200
    usernames = [item['username'] for item in response.data]
    assert usernames == ['はるか']

  def test_search_without_keyword_returns_all(self, api_client, user_factory):
    user_factory(username='user_a')
    user_factory(username='user_b')

    response = api_client.get('/api/users/')

    assert response.status_code == 200
    assert len(response.data) == 2
