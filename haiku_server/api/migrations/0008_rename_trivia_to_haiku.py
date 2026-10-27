# Trivia -> Haiku のモデル名変更がmodels.py側だけ行われていて、
# マイグレーション側には一度も反映されていなかった。
# （これが「Table 'haiku.api_haiku' doesn't exist」の原因）
#
# 調査の結果、実際のDBでは下記の通りだった:
#   - api_trivia -> api_haiku のテーブルリネームは既にDB上で完了している
#     （Djangoのマイグレーションを経由せず行われたため django_migrations には
#      記録されていない）
#   - api_haiku の genre / explanation 列も既に削除済み
#   - api_good の外部キー列は trivia_id のまま（haiku_id に未変更）
#   - api_genre テーブルはまだ削除されていない
#
# また、api_good の unique_set 制約 (user_id, trivia_id) は先頭列がuser_id側の
# 外部キーを支えるインデックスとしても使われているため、先に制約を消そうとすると
# MySQLに拒否される。列のリネームだけならMySQLがインデックス定義を自動で
# 追従させてくれるので、先にリネームしてから、Django側の管理状態
# （Meta.constraintsの内容）だけを合わせる。

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('api', '0007_auto_20261003_1615'),
  ]

  operations = [
    # Trivia -> Haiku （テーブルリネームは既にDB上で完了しているので、
    # Djangoの管理状態だけ合わせる。SQLは発行しない）
    migrations.SeparateDatabaseAndState(
      state_operations=[
        migrations.RenameModel(
          old_name='Trivia',
          new_name='Haiku',
        ),
      ],
      database_operations=[],
    ),
    # genre / explanation フィールドも既にDB上で削除済みなので、
    # こちらも状態だけ合わせる
    migrations.SeparateDatabaseAndState(
      state_operations=[
        migrations.RemoveField(
          model_name='haiku',
          name='genre',
        ),
        migrations.RemoveField(
          model_name='haiku',
          name='explanation',
        ),
      ],
      database_operations=[],
    ),
    # Good.trivia -> Good.haiku はまだDB上で未対応なので、実際に列をリネームする
    # （unique_set制約はMySQLが自動で(user_id, haiku_id)に追従させてくれるので
    #  ここでは触らない）
    migrations.RenameField(
      model_name='good',
      old_name='trivia',
      new_name='haiku',
    ),
    migrations.AlterField(
      model_name='good',
      name='haiku',
      field=models.ForeignKey(
        on_delete=django.db.models.deletion.CASCADE,
        related_name='haiku_relationships',
        to='api.haiku',
      ),
    ),
    # unique_set制約の対象フィールドが変わったことをDjangoの管理状態にだけ反映する
    # （実体のインデックスは上のRenameFieldで既に(user_id, haiku_id)に追従済み）
    migrations.SeparateDatabaseAndState(
      state_operations=[
        migrations.RemoveConstraint(
          model_name='good',
          name='unique_set',
        ),
        migrations.AddConstraint(
          model_name='good',
          constraint=models.UniqueConstraint(
            fields=('user', 'haiku'), name='unique_set'
          ),
        ),
      ],
      database_operations=[],
    ),
    # api_genreテーブルもまだ実在するので、こちらは実際に削除する
    migrations.DeleteModel(
      name='Genre',
    ),
  ]
