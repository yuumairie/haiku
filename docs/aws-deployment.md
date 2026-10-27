# AWSデプロイ手順（Lambda / ECS Fargate / Terraform / GitHub Actions）

このドキュメントは、本アプリ（Vue3+TypeScriptフロントエンド / Django REST Framework + MySQLバックエンド）を、できるだけ運用コストを抑えつつ AWS 上にデプロイするための設計方針と手順をまとめたものです。

## 1. 設計方針

個人開発規模のアプリでは、「常時起動しているリソースの固定費」がコストの大部分を占めます。特に以下の2つが典型的な構成で重くなりがちです。

- **NAT Gateway**: 東京リージョンで時間課金約0.062ドル/時 + データ処理料。月にすると固定費だけで4,000〜5,000円程度になる。
- **ALB**: 固定費だけで月2,000円前後 + わずかなLCU課金。

このうちNAT Gatewayは、ECS FargateのタスクをプライベートサブネットではなくパブリックサブネットでPublic IPを直付けし、セキュリティグループでALBからのインバウンドのみ許可する構成にすれば完全に省略できます（タスクが外部APIを呼ぶような処理がある場合はこの方式は使えませんが、本アプリには該当する処理はありません）。ALBはHTTPS終端とゼロダウンタイムデプロイの役割上、Fargateを使うなら実質必須なので固定費として受け入れます。

Fargateタスク自体はFargate Spotにすることで通常の7割程度の価格になります（個人アプリの可用性要件なら十分許容範囲）。さらに、24時間稼働させる必要がないため、深夜〜早朝はLambda + EventBridge Schedulerでdesired_countを0に落とし、朝にまた1に戻すことで稼働時間を半分前後に減らします。

RDSはdb.t4g.micro・シングルAZ・ストレージ20GBにしておけば、新規AWSアカウントなら12ヶ月間無料枠（750時間/月 + ストレージ20GB）でほぼ無料、無料枠終了後も月1,000〜1,500円程度に収まります（正確な最新料金はAWS Pricing Calculatorで確認）。

### Lambdaの役割（2箇所）

1. **ECSスケジュールスケーリング**: EventBridge Schedulerから定期実行し、夜間はECSサービスのdesired_countを0に、朝は1に戻す。Fargateの稼働時間削減が主目的。
2. **アバター画像のアップロード後処理**: S3への画像アップロードをトリガーに、サムネイル生成・リサイズを行う。既存の5MB上限バリデーションと相性の良いサーバーレスの使い道。

## 2. 構成要素マッピング

| レイヤ | AWSサービス | 補足 |
|---|---|---|
| 配信ドメイン | CloudFront 1枚（単一ドメイン） | `/*`→フロントS3、`/api/*` `/admin/*` `/authen/*` `/static/*`→ALB、`/media/*`→メディアS3、という単一ドメイン構成。フロントとAPIが同一オリジンになるのでCORS設定も最小限で済む |
| フロントエンド（Vueビルド） | S3（非公開、OAC経由） | SPAのクライアントサイドルーティングはCloudFront Functionで`index.html`にリライト |
| バックエンドAPI（Django/DRF） | ECR → ECS Fargate（Fargate Spot、0.25vCPU/0.5GB、desired_count=1）+ ALB | パブリックサブネット + Public IP直付けでNAT Gateway回避。ALBはCloudFrightの背後にいるのでHTTPのみでよい |
| DB | RDS for MySQL（db.t4g.micro、シングルAZ、20GB） | 自動バックアップは最小限の保持期間に |
| メディアファイル（アバター画像） | S3（非公開、OAC経由） | **重要**: Fargateのコンテナはローカルディスクが再デプロイ・再起動のたびに消える。`django-storages` + `boto3`でS3保存に切り替え済み（`settings.py`） |
| 静的ファイル（Django admin用） | whitenoise（コンテナ内配信） | adminしか使わないため、これが一番手間が少ない |
| シークレット（DB_PASSWORD, SECRET_KEY） | SSM Parameter Store（SecureString、無料） | タスク定義の`secrets`ブロックから参照し環境変数として注入 |
| CI/CD認証 | GitHub OIDC → IAMロール | AWSアクセスキーをGitHub Secretsに置かない |
| Terraform state | S3バックエンド + `use_lockfile = true` | Terraform 1.10以降の機能。ロック用DynamoDBテーブルも省略可能 |

## 3. コスト目安（東京リージョン、概算）

- NAT Gateway回避による削減額: 月4,000〜5,000円程度（最大の削減ポイント）
- ALB: 固定費のみで月2,000円前後 + わずかなLCU課金
- Fargate Spot（0.25vCPU/0.5GB、夜間停止込み）: 月500〜1,000円程度
- RDS db.t4g.micro: 無料枠内はほぼ0円、枠終了後は月1,000〜1,500円程度
- S3 / CloudFront / Lambda / SSM: トラフィック次第だが個人利用なら月数百円以内

合計で無料枠が効いている間は月1,000円未満、枠終了後も月3,000〜4,000円程度に収まる見込み。正確な最新料金は都度 AWS Pricing Calculator で確認すること。

## 4. Terraformディレクトリ構成（案）

```
infra/
  bootstrap/           # 最初に1回だけ手動apply（tfstate用S3バケット + GitHub OIDCロール）
    main.tf / variables.tf / outputs.tf / README.md
  modules/
    network/           # VPC, public subnets x2, SG（NAT Gatewayなし）
    ecr/                # backend / thumbnail-lambda の2リポジトリ
    rds/
    ecs/                # cluster, task definition, service, ALB, listener
    frontend/           # S3 (フロントビルド成果物置き場)
    media/              # S3 (アバター画像置き場)
    cdn/                # 上記3つをまとめる単一CloudFrontディストリビューション
    lambda_scheduler/   # 夜間のECSスケールダウン/アップ用
    lambda_thumbnail/   # S3トリガーの画像サムネイル生成用（コンテナイメージLambda）
    iam_oidc/           # GitHub Actions用OIDCプロバイダ + ロール（bootstrapから呼ばれる）
  envs/
    prod/
      backend.tf / providers.tf / main.tf / variables.tf / outputs.tf
      terraform.tfvars.example

.github/workflows/
  infra.yml   # terraform plan → (手動承認) → apply
  deploy.yml  # フロントビルド/S3sync、backendイメージbuild/push、migrate、ECSデプロイ、thumbnail-lambda更新

Dockerfile.prod                        # 本番用バックエンドイメージ
haiku_server/requirements-prod.txt     # gunicorn / django-storages / boto3 / whitenoise
```

## 5. アプリケーション側の変更（実施済み）

- `haiku_server/drfapi/settings.py`: `whitenoise`ミドルウェアを追加、`STATIC_ROOT`/`STATICFILES_STORAGE`を設定、`AWS_STORAGE_BUCKET_NAME`が設定されている場合のみ`DEFAULT_FILE_STORAGE`をS3向け（`django-storages`の`S3Boto3Storage`）に切り替える構成にした。ローカル開発時はこの環境変数を設定しないので、従来通りローカルディスクに保存される。
  - `DB_*`系の環境変数は元々設定済みだったため変更なし（RDSのエンドポイントをそのまま`DB_HOST`に渡せる）。
  - `ALLOWED_HOSTS`はCloudFront経由の単一ドメイン構成にしたため、`infra/modules/ecs`内でALBのDNS名 + `.cloudfront.net`を許可する形でTerraform側が自動設定する（コード側の変更は不要）。
- `Dockerfile.prod`: 本番用バックエンドイメージ（gunicorn起動、`collectstatic`実行）を新規作成。
- `haiku_server/requirements-prod.txt`: `gunicorn` / `django-storages` / `boto3` / `whitenoise`を追加（開発用の`requirements-dev.txt`とは別管理）。

## 6. 初回セットアップ手順

実際に以下の順番で手を動かす。`infra/`配下のコードは全て作成済み。

1. **bootstrap（手元の端末から1回だけ）**
   ```
   cd infra/bootstrap
   terraform init
   terraform apply
   ```
   出力される`tfstate_bucket`を`infra/envs/prod/backend.tf`の`bucket`に設定し、
   `github_actions_role_arn`をGitHubリポジトリの Settings > Secrets and variables > Actions に
   `AWS_GITHUB_ACTIONS_ROLE_ARN`として登録する。（詳細: `infra/bootstrap/README.md`）

2. **GitHub Environmentの作成**: `infra.yml`の本番apply前に手動承認を挟むため、
   GitHubリポジトリの Settings > Environments で `production` という名前のEnvironmentを作成し、
   Required reviewersを設定する。

3. **thumbnail Lambda用のダミーイメージを事前push（1回だけ）**: ECRリポジトリが空の状態では
   Lambda関数（コンテナイメージ）をTerraformが作成できないため、`infra/modules/lambda_thumbnail/README.md`
   の手順で先に1枚イメージをpushしておく。

4. **`infra.yml`を実行**（`master`にpush、または手動実行）: VPC・RDS・ECS・ALB・S3・CloudFront・Lambda等
   一式をTerraformで作成する。`terraform plan`の内容を確認してから本番apply（Environmentの承認）を行う。

5. **`deploy.yml`を実行**（`master`にpush、または手動実行）: フロントエンドビルド→S3配置→CloudFront invalidation、
   backendイメージのビルド→ECR push、DBマイグレーション（ECS RunTaskで1回限り実行）、
   タスク定義更新→ECSサービスのデプロイ、までが自動で流れる。

6. `terraform output cloudfront_domain_name`で確認できるCloudFrontのドメインにアクセスし、動作確認する。

## 7. GitHub Actionsのワークフロー構成

インフラ変更（terraform plan/apply）とアプリデプロイ（新イメージ・新フロントエンド）は別ワークフローに分けている。インフラは頻繁に変わらず、レビューを挟みたいため。このリポジトリのデフォルトブランチは`master`。

- `infra.yml`: `infra/`配下の変更を`master`にpushした時にトリガー。`terraform plan` → （`production` Environmentでの手動承認） → `apply`。
- `deploy.yml`: `haiku_front/` `haiku_server/` `Dockerfile.prod`等の変更を`master`にpushした時にトリガー。
  1. `test`: バックエンド(pytest)・フロントエンド(Vitest)のテストを実行する。他の全ジョブは`needs: test`で
     これに直列につながっているため、テストが1つでも落ちるとデプロイは一切行われない。
  2. `terraform-outputs`: 既にapply済みのstateからバケット名・ECR URL・ECSクラスタ名などを読み出す（applyはしない）
  3. `frontend`: ビルド → S3 sync → CloudFront invalidation
  4. `backend`: Dockerイメージビルド（`Dockerfile.prod`） → ECRへpush
  5. `migrate`: 新イメージ + `migrate`コマンド上書きでECS RunTaskを1回だけ実行し、終了コードを確認
  6. `deploy-service`: 新イメージでタスク定義の新リビジョンを登録 → ECSサービスを`force-new-deployment`
  7. `thumbnail-lambda`: `infra/modules/lambda_thumbnail/docker/`配下に変更があった時だけ、イメージを再build/pushしてLambdaを更新

認証はどちらも`aws-actions/configure-aws-credentials`の`role-to-assume`でOIDC経由にし、長期のアクセスキーは使わない。

## 8. 参考

- [AWS NAT Gateway Pricing: Complete Guide with Calculator](https://cloudburn.io/blog/aws-nat-gateway-pricing)
- [Amazon RDS for MySQL pricing](https://aws.amazon.com/rds/mysql/pricing/)
- [Terraform State Locking with S3 Without DynamoDB](https://devopscube.com/terraform-state-locking-with-s3/)
