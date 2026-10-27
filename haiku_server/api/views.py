from django.shortcuts import render
from rest_framework.permissions import (
  IsAuthenticated,
  AllowAny,
  IsAuthenticatedOrReadOnly,
)
from rest_framework import generics
from .models import Haiku, Profile, Comment, User, Good, Follow, Kigo
from rest_framework import viewsets
from . import serializers
from .ownpermissions import (
  ProfilePermission,
  HaikuPermission,
  CommentPermission,
  FollowPermission,
)


class CreateUserView(generics.CreateAPIView):
  serializer_class = serializers.UserSerializer
  permission_classes = (AllowAny,)


class ProfileViewSet(viewsets.ModelViewSet):
  # IsAuthenticatedOrReadOnly: 読み取りは誰でも、書き込みはログインユーザーのみ
  # ProfilePermission: 更新・削除はさらに本人のみに限定する
  permission_classes = (IsAuthenticatedOrReadOnly, ProfilePermission)
  queryset = Profile.objects.all()
  serializer_class = serializers.ProfileSerializer

  def get_queryset(self):
    queryset = Profile.objects.all()

    # ?userProfile=<ユーザID> で本人のプロフィールを絞り込めるようにする
    user_id = self.request.query_params.get('userProfile')
    if user_id:
      queryset = queryset.filter(userProfile_id=user_id)

    return queryset

  def perform_create(self, selializer):
    selializer.save(userProfile=self.request.user)


class MyProfileListView(generics.ListAPIView):
  queryset = User.objects.all()
  serializer_class = serializers.UserSerializer

  def get_queryset(self):
    return self.queryset.filter(email=self.request.user)


class MyProfileUpdateView(generics.RetrieveUpdateAPIView):
  # プロフィール画面：ログイン中のユーザ自身の表示名（username）の確認・編集用。
  # 対象は常にログイン中の自分自身なので、URLにidは含めない。
  permission_classes = (IsAuthenticated,)
  serializer_class = serializers.MyUsernameSerializer

  def get_object(self):
    return self.request.user


class GoodViewSet(viewsets.ModelViewSet):
  queryset = Good.objects.all()
  serializer_class = serializers.GoodSerializer
  permission_classes = (IsAuthenticatedOrReadOnly,)
  # def get_queryset(self):
  #   return self.queryset.filter(user=self.request.user)


def _detect_kigo(content):
  # contentに含まれる季語のうち、最長一致のものを採用する
  # （「桜」と「桜前線」のように短い季語が長い季語に含まれる場合に、
  # より具体的な方を優先するため）。
  # 該当する季語が無ければ (None, None) を返す。
  matched = None
  for kigo in Kigo.objects.all():
    if kigo.word in content and (
        matched is None or len(kigo.word) > len(matched.word)
    ):
      matched = kigo
  if matched:
    return matched.word, matched.season
  return None, None


class HaikuViewSet(viewsets.ModelViewSet):
  # IsAuthenticatedOrReadOnly: 読み取りは誰でも、書き込みはログインユーザーのみ
  # HaikuPermission: 更新・削除はさらに投稿者本人のみに限定する
  permission_classes = (IsAuthenticatedOrReadOnly, HaikuPermission)
  queryset = Haiku.objects.all()

  # 一覧取得時、userPostで絞り込まない場合に返す最大件数
  DEFAULT_LIMIT = 100

  def get_queryset(self):
    queryset = Haiku.objects.all().order_by('-created_at')

    # ?userPost=<ユーザID> で投稿者を絞り込めるようにする
    user_id = self.request.query_params.get('userPost')
    if user_id:
      queryset = queryset.filter(userPost_id=user_id)

    # ?content=<キーワード> で句の内容をキーワード検索できるようにする
    keyword = self.request.query_params.get('content')
    if keyword:
      queryset = queryset.filter(content__icontains=keyword)

    # ?season=<季節> で季節を絞り込めるようにする
    season = self.request.query_params.get('season')
    if season:
      queryset = queryset.filter(season=season)

    # 絞り込み条件が無い一覧取得（list）の場合は最大100件に制限する。
    # 1件取得（retrieve）・更新・削除・絞り込み検索時はここで制限せず、全件から探せるようにする。
    if not user_id and not keyword and not season and self.action == 'list':
      return queryset[: self.DEFAULT_LIMIT]

    return queryset

  def get_serializer_class(self):
    if self.request.method == 'GET':
      return serializers.HaikuReadSerializer
    return serializers.HaikuWriteSerializer

  def perform_create(self, serializer):
    # 季語はクライアントの入力に関わらず、投稿内容からサーバー側で自動判定する
    kigo, season = _detect_kigo(serializer.validated_data.get('content', ''))
    serializer.save(userPost=self.request.user, kigo=kigo, season=season)


class UserSearchView(generics.ListAPIView):
  # ユーザ名での検索。誰でも検索できるようにする。
  permission_classes = (AllowAny,)
  serializer_class = serializers.UserSerializer

  # キーワード無しの場合に返す最大件数
  DEFAULT_LIMIT = 100

  def get_queryset(self):
    queryset = User.objects.all().order_by('username')

    # ?username=<キーワード> でユーザ名を部分一致検索できるようにする
    keyword = self.request.query_params.get('username')
    if keyword:
      return queryset.filter(username__icontains=keyword)

    return queryset[: self.DEFAULT_LIMIT]


class CommentViewSet(viewsets.ModelViewSet):
  # IsAuthenticatedOrReadOnly: 読み取りは誰でも、書き込みはログインユーザーのみ
  # CommentPermission: 更新・削除はさらにコメント投稿者本人のみに限定する
  permission_classes = (IsAuthenticatedOrReadOnly, CommentPermission)
  queryset = Comment.objects.all()

  def get_queryset(self):
    queryset = Comment.objects.all().order_by('id')

    # ?post=<俳句ID> でその句へのコメントだけに絞り込めるようにする
    post_id = self.request.query_params.get('post')
    if post_id:
      return queryset.filter(post_id=post_id)

    return queryset

  def get_serializer_class(self):
    if self.request.method == 'GET':
      return serializers.CommentReadSerializer
    return serializers.CommentSerializer

  def perform_create(self, serializer):
    serializer.save(userComment=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
  # IsAuthenticatedOrReadOnly: 読み取りは誰でも、書き込みはログインユーザーのみ
  # FollowPermission: 削除はさらにフォローした本人のみに限定する
  permission_classes = (IsAuthenticatedOrReadOnly, FollowPermission)
  queryset = Follow.objects.all()

  def get_queryset(self):
    queryset = Follow.objects.all().order_by('-created_at')

    # ?follower=<ユーザID> でそのユーザがフォローしている相手一覧に絞り込む
    follower_id = self.request.query_params.get('follower')
    if follower_id:
      queryset = queryset.filter(follower_id=follower_id)

    # ?following=<ユーザID> でそのユーザをフォローしているユーザ一覧に絞り込む
    following_id = self.request.query_params.get('following')
    if following_id:
      queryset = queryset.filter(following_id=following_id)

    return queryset

  def get_serializer_class(self):
    if self.request.method == 'GET':
      return serializers.FollowReadSerializer
    return serializers.FollowSerializer

  def perform_create(self, serializer):
    serializer.save(follower=self.request.user)
