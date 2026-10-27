# フォロー機能のためのFollowモデルを追加する

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('api', '0009_haiku_content_max_length'),
  ]

  operations = [
    migrations.CreateModel(
      name='Follow',
      fields=[
        (
          'id',
          models.AutoField(
            auto_created=True,
            primary_key=True,
            serialize=False,
            verbose_name='ID',
          ),
        ),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        (
          'follower',
          models.ForeignKey(
            on_delete=django.db.models.deletion.CASCADE,
            related_name='following_relationships',
            to=settings.AUTH_USER_MODEL,
          ),
        ),
        (
          'following',
          models.ForeignKey(
            on_delete=django.db.models.deletion.CASCADE,
            related_name='follower_relationships',
            to=settings.AUTH_USER_MODEL,
          ),
        ),
      ],
    ),
    migrations.AddConstraint(
      model_name='follow',
      constraint=models.UniqueConstraint(
        fields=('follower', 'following'), name='unique_follow'
      ),
    ),
  ]
