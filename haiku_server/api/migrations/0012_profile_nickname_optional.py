# Profileのnickname（表示名）は現状アプリ上では未使用（表示名にはUserの
# usernameを使っている）ため、必須項目から外して空文字を許可する。

from django.db import migrations, models


class Migration(migrations.Migration):

  dependencies = [
    ('api', '0011_kigo'),
  ]

  operations = [
    migrations.AlterField(
      model_name='profile',
      name='nickName',
      field=models.CharField(blank=True, default='', max_length=20),
    ),
  ]
