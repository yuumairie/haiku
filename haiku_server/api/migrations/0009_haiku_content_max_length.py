# 短冊の入力では改行(五・七・五の区切り、最大2個)を文字数制限に含めないようにしたため、
# 実際に保存される文字列は「本文50文字 + 改行最大2個」で最大52文字になる可能性がある。
# そのため content カラムの長さを50から52に広げる。

from django.db import migrations, models


class Migration(migrations.Migration):

  dependencies = [
    ('api', '0008_rename_trivia_to_haiku'),
  ]

  operations = [
    migrations.AlterField(
      model_name='haiku',
      name='content',
      field=models.CharField(max_length=52),
    ),
  ]
