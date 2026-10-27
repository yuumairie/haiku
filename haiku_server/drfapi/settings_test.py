"""
pytest実行時に使うDjango設定。

ローカル開発(docker-compose)のMySQLユーザー(haiku/haiku)は`haiku`データベース
にしか権限を持っておらず、Djangoのデフォルトのテスト実行(settings.DATABASES
の`NAME`の前に`test_`を付けたDBをCREATE DATABASEする)が権限エラーで失敗する
恐れがある。これを避けるため、テスト専用にSQLite(インメモリ)を使うよう
本来のsettings.pyを上書きする。

さらに、api/migrations/0008_rename_trivia_to_haiku.py は「DB側では既に手動で
テーブルリネーム等が完了している」という本番/開発DBの実際の状態を前提に
SeparateDatabaseAndStateでDB操作をスキップしている。真っ白なテスト用DBに
対して普通にマイグレーションを順番に適用すると、このマイグレーションの
前提が崩れてテーブル名の不整合が起きる。pytest.ini側で--no-migrationsを
指定し、マイグレーション履歴を経由せず「現在のmodels.pyの定義から直接
テーブルを作る」ことでこの問題を回避している(pytest-djangoの仕組み)。
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
  }
}

# テスト実行を速くするため、パスワードハッシュを軽量なものに差し替える
PASSWORD_HASHERS = [
  'django.contrib.auth.hashers.MD5PasswordHasher',
]
