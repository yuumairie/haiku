import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRegister:
  def test_register_normal(self, api_client):
    response = api_client.post(
      '/api/register/',
      {
        'email': 'newuser@example.com',
        'password': 'strongpass123',
        'username': 'newuser',
      },
    )

    assert response.status_code == 201
    assert User.objects.filter(email='newuser@example.com').exists()
    # password/emailはwrite_onlyなのでレスポンスには含まれない
    assert 'password' not in response.data
    assert 'email' not in response.data

  def test_register_without_username_is_rejected(self, api_client):
    # usernameはallow_blank=Falseで必須
    response = api_client.post(
      '/api/register/',
      {
        'email': 'nouser@example.com',
        'password': 'strongpass123',
        'username': '',
      },
    )

    assert response.status_code == 400
    assert 'username' in response.data
    assert not User.objects.filter(email='nouser@example.com').exists()

  def test_register_duplicate_email_is_rejected(self, api_client, user_factory):
    user_factory(email='dup@example.com')

    response = api_client.post(
      '/api/register/',
      {
        'email': 'dup@example.com',
        'password': 'strongpass123',
        'username': 'dupuser',
      },
    )

    assert response.status_code == 400
    assert 'email' in response.data


class TestJwtLogin:
  def test_login_normal_returns_tokens(self, api_client, user_factory):
    user_factory(email='login@example.com', password='mypassword1')

    response = api_client.post(
      '/authen/jwt/create/',
      {'email': 'login@example.com', 'password': 'mypassword1'},
    )

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data

  def test_login_wrong_password_is_rejected(self, api_client, user_factory):
    user_factory(email='login2@example.com', password='mypassword1')

    response = api_client.post(
      '/authen/jwt/create/',
      {'email': 'login2@example.com', 'password': 'wrongpassword'},
    )

    assert response.status_code == 401

  def test_login_unknown_email_is_rejected(self, api_client):
    response = api_client.post(
      '/authen/jwt/create/',
      {'email': 'nobody@example.com', 'password': 'whatever123'},
    )

    assert response.status_code == 401

  def test_access_token_grants_access_to_protected_endpoint(
    self, api_client, user_factory
  ):
    created_user = user_factory(email='login3@example.com', password='mypassword1')

    login_response = api_client.post(
      '/authen/jwt/create/',
      {'email': 'login3@example.com', 'password': 'mypassword1'},
    )
    access_token = login_response.data['access']

    # SIMPLE_JWTのAUTH_HEADER_TYPESが'JWT'なので、ヘッダーも"JWT <token>"にする
    api_client.credentials(HTTP_AUTHORIZATION=f'JWT {access_token}')
    response = api_client.get('/api/me/')

    assert response.status_code == 200
    assert response.data['id'] == created_user.id

  def test_protected_endpoint_without_token_is_unauthorized(self, api_client):
    response = api_client.get('/api/me/')
    assert response.status_code == 401
