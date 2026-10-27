import pytest
from rest_framework.test import APIClient

from api.models import Haiku, Kigo

pytestmark = pytest.mark.django_db


@pytest.fixture
def kigo_sakura(db):
  return Kigo.objects.create(word='桜', season='春')


class TestHaikuList:
  def test_anonymous_sees_only_public_haikus(self, api_client, user_factory):
    author = user_factory()
    Haiku.objects.create(userPost=author, content='公開句その1', is_public=True)
    Haiku.objects.create(userPost=author, content='非公開句その1', is_public=False)

    response = api_client.get('/api/haikus/')

    assert response.status_code == 200
    contents = [item['content'] for item in response.data]
    assert '公開句その1' in contents
    assert '非公開句その1' not in contents

  def test_owner_sees_own_private_haiku(self, auth_client, user):
    Haiku.objects.create(userPost=user, content='自分だけの非公開句', is_public=False)

    response = auth_client.get('/api/haikus/')

    contents = [item['content'] for item in response.data]
    assert '自分だけの非公開句' in contents

  def test_other_user_does_not_see_someone_elses_private_haiku(
    self, auth_client, other_user
  ):
    Haiku.objects.create(userPost=other_user, content='他人の非公開句', is_public=False)

    response = auth_client.get('/api/haikus/')

    contents = [item['content'] for item in response.data]
    assert '他人の非公開句' not in contents

  def test_filter_by_content_keyword(self, api_client, user_factory):
    author = user_factory()
    Haiku.objects.create(userPost=author, content='桜が咲く春の句')
    Haiku.objects.create(userPost=author, content='全く関係ない句')

    response = api_client.get('/api/haikus/', {'content': '桜'})

    contents = [item['content'] for item in response.data]
    assert contents == ['桜が咲く春の句']

  def test_filter_by_user_post(self, api_client, user_factory):
    a = user_factory()
    b = user_factory()
    Haiku.objects.create(userPost=a, content='Aさんの句')
    Haiku.objects.create(userPost=b, content='Bさんの句')

    response = api_client.get('/api/haikus/', {'userPost': a.id})

    contents = [item['content'] for item in response.data]
    assert contents == ['Aさんの句']

  def test_filter_by_season(self, api_client, user_factory):
    author = user_factory()
    Haiku.objects.create(userPost=author, content='春の句', season='春')
    Haiku.objects.create(userPost=author, content='夏の句', season='夏')

    response = api_client.get('/api/haikus/', {'season': '春'})

    contents = [item['content'] for item in response.data]
    assert contents == ['春の句']


class TestHaikuRetrieve:
  def test_retrieve_other_users_private_haiku_returns_404(
    self, auth_client, other_user
  ):
    haiku = Haiku.objects.create(
      userPost=other_user, content='見えないはずの句', is_public=False
    )

    response = auth_client.get(f'/api/haikus/{haiku.id}/')

    assert response.status_code == 404

  def test_retrieve_public_haiku_as_anonymous(self, api_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='誰でも見られる句')

    response = api_client.get(f'/api/haikus/{haiku.id}/')

    assert response.status_code == 200
    assert response.data['content'] == '誰でも見られる句'

  def test_retrieve_nonexistent_haiku_returns_404(self, api_client):
    response = api_client.get('/api/haikus/999999/')
    assert response.status_code == 404


class TestHaikuCreate:
  def test_create_requires_authentication(self, api_client):
    response = api_client.post('/api/haikus/', {'content': '誰の句でもない'})
    assert response.status_code == 401

  def test_create_normal_sets_owner_and_defaults_public(self, auth_client, user):
    response = auth_client.post('/api/haikus/', {'content': '新しい句'})

    assert response.status_code == 201
    haiku = Haiku.objects.get(id=response.data['id'])
    assert haiku.userPost == user
    assert haiku.is_public is True

  def test_create_private_haiku(self, auth_client):
    response = auth_client.post(
      '/api/haikus/', {'content': '秘密の句', 'is_public': False}
    )

    assert response.status_code == 201
    haiku = Haiku.objects.get(id=response.data['id'])
    assert haiku.is_public is False

  def test_create_auto_detects_kigo_and_season(self, auth_client, kigo_sakura):
    response = auth_client.post('/api/haikus/', {'content': '桜咲く道を歩く'})

    assert response.status_code == 201
    haiku = Haiku.objects.get(id=response.data['id'])
    assert haiku.kigo == '桜'
    assert haiku.season == '春'

  def test_create_ignores_client_supplied_kigo(self, auth_client, kigo_sakura):
    # 季語はサーバー側で自動判定するため、辞書に無い季語をクライアントが
    # 送っても無視される(自動判定の結果である None で上書きされる)
    response = auth_client.post(
      '/api/haikus/',
      {'content': '月を見ながら歩く句', 'kigo': '月', 'season': '秋'},
    )

    assert response.status_code == 201
    haiku = Haiku.objects.get(id=response.data['id'])
    assert haiku.kigo is None
    assert haiku.season is None

  def test_create_blank_content_is_rejected(self, auth_client):
    response = auth_client.post('/api/haikus/', {'content': ''})
    assert response.status_code == 400

  def test_create_content_too_long_is_rejected(self, auth_client):
    response = auth_client.post('/api/haikus/', {'content': 'あ' * 53})
    assert response.status_code == 400

  def test_create_without_content_is_rejected(self, auth_client):
    response = auth_client.post('/api/haikus/', {})
    assert response.status_code == 400
    assert 'content' in response.data


class TestHaikuUpdate:
  def test_update_by_owner_succeeds(self, auth_client, user):
    haiku = Haiku.objects.create(userPost=user, content='元の句')

    response = auth_client.patch(f'/api/haikus/{haiku.id}/', {'content': '直した句'})

    assert response.status_code == 200
    haiku.refresh_from_db()
    assert haiku.content == '直した句'

  def test_update_by_non_owner_is_forbidden(self, auth_client, other_user):
    haiku = Haiku.objects.create(userPost=other_user, content='他人の句')

    response = auth_client.patch(f'/api/haikus/{haiku.id}/', {'content': '書き換え'})

    assert response.status_code == 403
    haiku.refresh_from_db()
    assert haiku.content == '他人の句'

  def test_update_requires_authentication(self, api_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = api_client.patch(f'/api/haikus/{haiku.id}/', {'content': '書き換え'})

    assert response.status_code == 401

  def test_update_kigo_not_contained_in_content_is_rejected(
    self, auth_client, user, kigo_sakura
  ):
    haiku = Haiku.objects.create(userPost=user, content='何もない句')

    response = auth_client.patch(f'/api/haikus/{haiku.id}/', {'kigo': '桜'})

    assert response.status_code == 400
    assert 'kigo' in response.data

  def test_clearing_kigo_also_clears_season(self, auth_client, user):
    haiku = Haiku.objects.create(
      userPost=user, content='桜咲く句', kigo='桜', season='春'
    )

    response = auth_client.patch(f'/api/haikus/{haiku.id}/', {'kigo': ''})

    assert response.status_code == 200
    haiku.refresh_from_db()
    assert haiku.kigo in (None, '')
    assert haiku.season is None

  def test_toggle_to_private_hides_it_from_others(self, auth_client, user, other_user):
    haiku = Haiku.objects.create(userPost=user, content='公開していた句', is_public=True)

    response = auth_client.patch(f'/api/haikus/{haiku.id}/', {'is_public': False})
    assert response.status_code == 200

    anonymous_client = APIClient()
    list_response = anonymous_client.get('/api/haikus/')
    contents = [item['content'] for item in list_response.data]
    assert '公開していた句' not in contents


class TestHaikuDelete:
  def test_delete_by_owner_succeeds(self, auth_client, user):
    haiku = Haiku.objects.create(userPost=user, content='消す句')

    response = auth_client.delete(f'/api/haikus/{haiku.id}/')

    assert response.status_code == 204
    assert not Haiku.objects.filter(id=haiku.id).exists()

  def test_delete_by_non_owner_is_forbidden(self, auth_client, other_user):
    haiku = Haiku.objects.create(userPost=other_user, content='残る句')

    response = auth_client.delete(f'/api/haikus/{haiku.id}/')

    assert response.status_code == 403
    assert Haiku.objects.filter(id=haiku.id).exists()

  def test_delete_requires_authentication(self, api_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = api_client.delete(f'/api/haikus/{haiku.id}/')

    assert response.status_code == 401
    assert Haiku.objects.filter(id=haiku.id).exists()
