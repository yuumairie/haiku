from rest_framework import serializers
from .models import Haiku, Profile, Comment, Good, Follow
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
  # プロフィール画像（Profile.img）のURL。プロフィール未作成・画像未設定の
  # 場合はNULL。短冊などで名前の上にアイコンとして表示するために使う
  avatar = serializers.SerializerMethodField()

  class Meta:
    model = get_user_model()
    fields = ('id', 'email', 'password', 'username', 'avatar')
    extra_kwargs = {
        'password': {'write_only': True, 'required': True},
        'email': {'write_only': True},
        # モデル側はblank=Trueだが、画面上の表示名として使うため登録時は必須にする
        'username': {'required': True, 'allow_blank': False},
    }

  def get_avatar(self, obj):
    try:
      profile = obj.userProfile
    except Profile.DoesNotExist:
      return None
    if not profile.img:
      return None
    request = self.context.get('request')
    url = profile.img.url
    return request.build_absolute_uri(url) if request else url

  def create(self, validated_data):
    user = get_user_model().objects.create_user(**validated_data)
    return user


class MyUsernameSerializer(serializers.ModelSerializer):
  # プロフィール画面で、ログイン中のユーザ自身の表示名（username）だけを
  # 確認・編集できるようにするための専用シリアライザ。
  # email/passwordはここでは一切扱わない。
  class Meta:
    model = get_user_model()
    fields = ('id', 'username')
    extra_kwargs = {
        'username': {'required': True, 'allow_blank': False},
    }


class ProfileSerializer(serializers.ModelSerializer):
  created_on = serializers.DateTimeField(
      format='%Y-%m-%d %H:%M', read_only=True)

  class Meta:
    model = Profile
    fields = ('id', 'nickName', 'userProfile', 'created_on', 'img')
    extra_kwargs = {'userProfile': {'read_only': True}}


class GoodSerializer(serializers.ModelSerializer):
  class Meta:
    model = Good
    fields = (
        'id',
        'user',
        'haiku',
    )


class HaikuWriteSerializer(serializers.ModelSerializer):
  class Meta:
    model = Haiku
    fields = (
        'id',
        'userPost',
        'content',
        'created_at',
        'good',
        'kigo',
        'season',
        'is_public',
    )
    extra_kwargs = {
        'userPost': {'read_only': True},
        # 投稿時はサーバー側で自動判定するため必須にしない。
        # 編集時はユーザが画面上で編集できる。
        'kigo': {'required': False, 'allow_null': True, 'allow_blank': True},
        'season': {'required': False, 'allow_null': True, 'allow_blank': True},
        # 省略時はモデルのdefault(True=公開)が使われる
        'is_public': {'required': False},
    }

  def validate(self, data):
    # 季語を編集した場合は、その季語が俳句の本文に含まれているか検証する。
    # 季語が空にされた場合は季節も合わせてクリアする。
    if 'kigo' in data or 'content' in data:
      kigo = data.get('kigo', getattr(self.instance, 'kigo', None))
      content = data.get('content', getattr(self.instance, 'content', None))
      if kigo and content and kigo not in content:
        raise serializers.ValidationError(
            {'kigo': '入力した季語が俳句の本文に含まれていません。'}
        )
      if 'kigo' in data and not kigo:
        data['season'] = None
    return data


class HaikuReadSerializer(serializers.ModelSerializer):
  userPost = UserSerializer(read_only=True)
  good = UserSerializer(many=True)
  created_at = serializers.DateTimeField(format='%Y/%m/%d %H:%M')

  class Meta:
    model = Haiku
    fields = (
        'id',
        'userPost',
        'content',
        'created_at',
        'good',
        'kigo',
        'season',
        'is_public',
    )
    extra_kwargs = {'userPost': {'read_only': True}}


class CommentSerializer(serializers.ModelSerializer):
  class Meta:
    model = Comment
    fields = ('id', 'text', 'userComment', 'post')
    extra_kwargs = {'userComment': {'read_only': True}}


class CommentReadSerializer(serializers.ModelSerializer):
  userComment = UserSerializer(read_only=True)

  class Meta:
    model = Comment
    fields = ('id', 'text', 'userComment', 'post')


class FollowSerializer(serializers.ModelSerializer):
  class Meta:
    model = Follow
    fields = ('id', 'follower', 'following')
    extra_kwargs = {'follower': {'read_only': True}}

  def validate(self, data):
    request = self.context.get('request')
    if request and data.get('following') == request.user:
      raise serializers.ValidationError('自分自身をフォローすることはできません。')
    return data


class FollowReadSerializer(serializers.ModelSerializer):
  follower = UserSerializer(read_only=True)
  following = UserSerializer(read_only=True)

  class Meta:
    model = Follow
    fields = ('id', 'follower', 'following')
