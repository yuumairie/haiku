import pytest
from django.db import IntegrityError

from api.models import Comment, Good, Haiku

pytestmark = pytest.mark.django_db


class TestGoodViewSet:
  def test_create_requires_authentication(self, api_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = api_client.post('/api/goods/', {'haiku': haiku.id})

    assert response.status_code == 401

  def test_create_normal(self, auth_client, user, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = auth_client.post('/api/goods/', {'haiku': haiku.id, 'user': user.id})

    assert response.status_code == 201
    assert Good.objects.filter(user=user, haiku=haiku).exists()

  def test_duplicate_good_raises_integrity_error(self, auth_client, user, user_factory):
    # 現状のGoodSerializer/GoodViewSetには一意制約違反に対するアプリ側の
    # バリデーションが無く、DB(UniqueConstraint)由来のIntegrityErrorがそのまま
    # 発生する(綺麗な400を返すには別途バリデーションの追加が必要)。
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')
    Good.objects.create(user=user, haiku=haiku)

    with pytest.raises(IntegrityError):
      auth_client.post('/api/goods/', {'haiku': haiku.id, 'user': user.id})

  def test_list_hides_good_on_someone_elses_private_haiku(
    self, auth_client, user_factory
  ):
    author = user_factory()
    liker = user_factory()
    private_haiku = Haiku.objects.create(
      userPost=author, content='非公開句', is_public=False
    )
    Good.objects.create(user=liker, haiku=private_haiku)

    response = auth_client.get('/api/goods/')

    assert response.status_code == 200
    haiku_ids = [item['haiku'] for item in response.data]
    assert private_haiku.id not in haiku_ids

  def test_list_shows_good_on_own_private_haiku(self, auth_client, user, user_factory):
    liker = user_factory()
    own_private_haiku = Haiku.objects.create(
      userPost=user, content='自分の非公開句', is_public=False
    )
    Good.objects.create(user=liker, haiku=own_private_haiku)

    response = auth_client.get('/api/goods/')

    assert response.status_code == 200
    haiku_ids = [item['haiku'] for item in response.data]
    assert own_private_haiku.id in haiku_ids


class TestCommentViewSet:
  def test_create_requires_authentication(self, api_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = api_client.post('/api/comments/', {'text': 'いいね', 'post': haiku.id})

    assert response.status_code == 401

  def test_create_normal_sets_comment_owner(self, auth_client, user, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = auth_client.post(
      '/api/comments/', {'text': 'いいコメント', 'post': haiku.id}
    )

    assert response.status_code == 201
    comment = Comment.objects.get(id=response.data['id'])
    assert comment.userComment == user

  def test_create_without_text_is_rejected(self, auth_client, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')

    response = auth_client.post('/api/comments/', {'post': haiku.id})

    assert response.status_code == 400
    assert 'text' in response.data

  def test_update_by_owner_succeeds(self, auth_client, user, user_factory):
    author = user_factory()
    haiku = Haiku.objects.create(userPost=author, content='句')
    comment = Comment.objects.create(text='元のコメント', userComment=user, post=haiku)

    response = auth_client.patch(f'/api/comments/{comment.id}/', {'text': '直したコメント'})

    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.text == '直したコメント'

  def test_update_by_non_owner_is_forbidden(self, auth_client, user, other_user):
    haiku = Haiku.objects.create(userPost=user, content='句')
    comment = Comment.objects.create(
      text='元のコメント', userComment=other_user, post=haiku
    )

    response = auth_client.patch(f'/api/comments/{comment.id}/', {'text': '書き換え'})

    assert response.status_code == 403

  def test_list_filtered_by_post_hides_comments_on_private_haiku_of_others(
    self, auth_client, user_factory
  ):
    author = user_factory()
    private_haiku = Haiku.objects.create(
      userPost=author, content='非公開句', is_public=False
    )
    Comment.objects.create(text='見えないコメント', userComment=author, post=private_haiku)

    response = auth_client.get('/api/comments/', {'post': private_haiku.id})

    assert response.status_code == 200
    assert response.data == []
