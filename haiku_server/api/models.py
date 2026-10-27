from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.conf import settings


def upload_avatar_path(instance, filename):
  ext = filename.split('.')[-1]
  return f'avatars/{instance.userProfile.id}{instance.nickName}.{ext}'


# アバター画像のアップロード上限
MAX_AVATAR_SIZE_MB = 5
MAX_AVATAR_SIZE_BYTES = MAX_AVATAR_SIZE_MB * 1024 * 1024


def validate_avatar_size(file):
  if file.size > MAX_AVATAR_SIZE_BYTES:
    raise ValidationError(
        f'画像サイズは{MAX_AVATAR_SIZE_MB}MB以下にしてください。'
    )


def upload_post_path(instance, filename):
  ext = filename.split('.')[-1]
  return f'posts/{instance.userPost.id}{instance.content}.{ext}'


class UserManager(BaseUserManager):
  def create_user(self, email, password, username='', **extra_fields):

    if not email:
      raise ValueError('email is must')

    user = self.model(
        email=self.normalize_email(email), username=username, **extra_fields
    )
    user.set_password(password)
    user.save(using=self._db)

    return user

  def create_superuser(self, email, password, username='', **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)

    return self.create_user(email, password, username, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
  email = models.EmailField(max_length=50, unique=True)
  username = models.CharField(max_length=20, blank=True)
  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)

  objects = UserManager()

  USERNAME_FIELD = 'email'

  def __str__(self):
    return self.email


class Profile(models.Model):
  # プロフィール画面では現状avatar画像のみ編集対象にしており、
  # 表示名は（投稿等と同じく）Userモデルのusernameを使うため必須にしない
  nickName = models.CharField(max_length=20, blank=True, default='')
  userProfile = models.OneToOneField(
      settings.AUTH_USER_MODEL, related_name='userProfile', on_delete=models.CASCADE
  )
  created_on = models.DateTimeField(auto_now_add=True)
  img = models.ImageField(
      blank=True,
      null=True,
      upload_to=upload_avatar_path,
      validators=[validate_avatar_size],
  )

  def __str__(self):
    return self.nickName


# 季語の季節。KigoモデルとHaikuモデルの両方で共通して使う
SEASON_CHOICES = (
    ('春', '春'),
    ('夏', '夏'),
    ('秋', '秋'),
    ('冬', '冬'),
    ('新年', '新年'),
)


class Kigo(models.Model):
  # 季語辞書。メンテナンスは管理画面（/admin/）から行う想定
  word = models.CharField(max_length=20, unique=True)
  season = models.CharField(max_length=10, choices=SEASON_CHOICES)

  def __str__(self):
    return self.word


class Haiku(models.Model):
  userPost = models.ForeignKey(
      settings.AUTH_USER_MODEL, related_name='userPost', on_delete=models.CASCADE
  )
  # 改行(最大2個：五・七・五の区切り)を含めずに50文字まで許可するため、
  # 実際のカラム長は余裕を持たせて52にしている
  content = models.CharField(max_length=52)
  good = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Good')
  created_at = models.DateTimeField(auto_now_add=True)
  # 投稿時にサーバー側で自動判定した季語・季節（無ければNULL）。
  # ユーザが後から編集することもできる
  kigo = models.CharField(max_length=20, blank=True, null=True)
  season = models.CharField(
      max_length=10, choices=SEASON_CHOICES, blank=True, null=True
  )


class Comment(models.Model):
  text = models.CharField(max_length=100)
  userComment = models.ForeignKey(
      settings.AUTH_USER_MODEL, related_name='userComment', on_delete=models.CASCADE
  )
  post = models.ForeignKey(Haiku, on_delete=models.CASCADE)

  def __str__(self):
    return self.text


class Good(models.Model):
  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='user_relationships',
  )
  haiku = models.ForeignKey(
      Haiku, on_delete=models.CASCADE, related_name='haiku_relationships'
  )

  class Meta:
    constraints = [
        models.UniqueConstraint(fields=['user', 'haiku'], name='unique_set')
    ]


class Follow(models.Model):
  # フォローしている側
  follower = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='following_relationships',
  )
  # フォローされている側
  following = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='follower_relationships',
  )
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['follower', 'following'], name='unique_follow'
        )
    ]
