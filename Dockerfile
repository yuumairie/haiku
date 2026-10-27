# バックエンド(Python/Django)とフロントエンド(Node/Vue)の両方を1つのコンテナに
# まとめた開発用Dockerfile。VS Codeのウィンドウを1つだけ開けば両方を編集・実行できる。

# Node.jsは公式イメージからマルチステージビルドでコピーしている(apt-get/NodeSource
# ではインストールしない)。このプロジェクトのビルド環境ではapt-getで何か新しい
# パッケージを入れようとすると、dpkgのパッケージ展開処理自体が毎回落ちてしまう
# 問題があったため、apt-getを一切使わない構成にして回避している。
#
# Node 22 (2026年10月現在のActive/Maintenance LTS。Node 20は2026年4月でEOL済み)。
# Vitest 1.x系 ≒ VS CodeのVitest拡張機能(vitest.explorer)がテストサイドバーに
# 表示するための要件(Node >=18)を満たすために上げた。以前はNode 16だったが、
# それに合わせてVitestも0.34系に下げていたため拡張機能がテストを検出できなかった。
FROM node:22-bookworm-slim AS node_base

FROM python:3.8-slim

COPY --from=node_base /usr/local /usr/local

WORKDIR /workspace

# git / openssh-client: コンテナ内でgitコマンドを使うために必要。
# このイメージ(python:3.8-slim)にはデフォルトで含まれていないため、apt-getで
# インストールする。
# 補足: 以前、apt-getで新規パッケージを入れようとするとdpkgの展開処理自体が
# 落ちるというビルド環境固有の問題が見つかっていた(このDockerfileで他の依存を
# apt-getではなくマルチステージのCOPYで入れているのはそのため)。もしここで
# ビルドが失敗する場合は、同じくマルチステージCOPYでgitバイナリを持ってくる方式に
# 切り替える必要があるので報告してください。
RUN apt-get update && \
    apt-get install -y --no-install-recommends git openssh-client && \
    rm -rf /var/lib/apt/lists/*

# バックエンドの依存パッケージ。bind mountとは別にここでインストールしておくことで、
# requirements.txtが変わらない限り再ビルド時にpip installをやり直さずに済む。
# ここに書かれているパッケージは全てビルド済みのmanylinux wheelが存在するため、
# Cコンパイラやapt側のパッケージ(build-essential, libjpeg-dev, zlib1g-dev)は不要。
# --progress-bar off: このビルド環境は新しいスレッドを作成できず、pipの標準の
# 進捗バー表示がクラッシュしてしまうため無効化している。
COPY haiku_server/requirements.txt haiku_server/requirements-dev.txt haiku_server/
RUN pip install --no-cache-dir --progress-bar off \
      -r haiku_server/requirements.txt \
      -r haiku_server/requirements-dev.txt

# フロントエンドの依存パッケージ。package-lock.json内の"resolved"のURLは、
# 元々使われていた中国のnpmミラー(registry.npm.taobao.org、TLS証明書が期限切れ)
# から、同じバージョン・内容のまま本家registry.npmjs.orgのURLに書き換え済み。
# --legacy-peer-deps: 未使用だったvue-cli-plugin-vuetify(Vue 2向けのpeer依存を
# 宣言していた)は削除済みだが、@vue/cli-plugin-*系(4.5系)のpeer依存の範囲が
# 新しいTypeScript/Vueに追従しきれていないため、念のため引き続き付けている。
COPY haiku_front/package.json haiku_front/package-lock.json haiku_front/
RUN cd haiku_front && npm install --no-progress --legacy-peer-deps

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000 8080
ENTRYPOINT ["/workspace/entrypoint.sh"]
