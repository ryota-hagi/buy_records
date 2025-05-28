# 🎯 PROJECT MANAGER - buy_records

## 🏗️ プロジェクト管理方針
**最大のレバレッジを効かせるため、私（PM）が技術的作業を直接実行し、部下エージェントには明確に定義された単純タスクのみを割り当てます。**

### 📊 役割分担の原則

#### 🎯 プロジェクトマネージャー（私）が行うこと
1. **技術的判断が必要な作業**
   - ブランチの作成・管理
   - コードの統合とマージ
   - アーキテクチャの決定
   - 複雑な問題の解決

2. **プロジェクト全体に影響する作業**
   - ファイル構造の整理
   - 命名規則の統一
   - 依存関係の管理
   - CI/CD設定

#### 👥 部下エージェントに任せること
1. **明確に定義された単純タスク**
   - 特定のAPIエンドポイントのテスト
   - ドキュメントの作成・更新
   - 定型的なコード修正
   - データ収集・分析

2. **独立して実行可能なタスク**
   - 特定プラットフォームの動作確認
   - パフォーマンステストの実行
   - エラーログの分析
   - 設定ファイルの更新

## 📋 プロジェクト概要
買い物比較プラットフォーム - 複数のECサイトから商品情報を収集・比較

### 現在のステータス: 🟢 稼働中
最終更新: 2025-05-28

## 🚀 クイックコマンド

### 開発環境起動
```bash
# 1. ローカルSeleniumサーバー起動（別ターミナル）
cd /Users/hagiryouta/my-claude-project/buy_records
python3 scripts/local_selenium_server.py

# 2. Next.js開発サーバー起動
npm run dev
```

### ヘルスチェック
```bash
# 全プラットフォーム動作確認
curl -X GET "http://localhost:3000/api/health"

# 個別プラットフォームテスト
./scripts/test_all_platforms.sh
```

## 📊 プラットフォーム状況

| プラットフォーム | 状態 | 最終確認 | 備考 |
|--------------|------|---------|------|
| 楽天 | ✅ | 2025-05-28 | APIキー設定済み |
| Yahoo!ショッピング | ✅ | 2025-05-28 | 安定動作 |
| eBay | ✅ | 2025-05-28 | OpenAI翻訳使用 |
| メルカリ | ✅ | 2025-05-28 | aria-label対応 |
| PayPayフリマ | ✅ | 2025-05-28 | 重複除去実装済み |
| ヨドバシ | ✅ | 2025-05-28 | リトライロジック有 |
| au PAYマーケット | ❌ | 2025-05-28 | ドメイン問題 |
| ラクマ | ❓ | - | 未確認 |
| Amazon | ❌ | - | API認証未設定 |

## 📊 現在のタスク管理状況

### 🚀 PM（私）が直接実行中のタスク
| タスク | ブランチ | 進捗 | 次のアクション |
|--------|---------|------|----------------|
| スクリプト整理 | refactor/cleanup-scripts | 0% | ブランチ作成→ファイル移動 |
| ラクマ修正 | feature/fix-rakuma | 20% | デバッグ継続 |
| ブランチ管理システム | - | 0% | 方針決定→実装 |

### 👥 エージェントに割り当て可能なタスク
| タスク種別 | 具体例 | 必要スキル | 期待成果 |
|-----------|--------|-----------|----------|
| テスト実行 | 各プラットフォームの動作確認 | APIテスト | テスト結果レポート |
| ドキュメント作成 | API使用例の文書化 | 技術文書作成 | Markdownファイル |
| データ収集 | エラーログの分析 | ログ解析 | 問題点リスト |
| 設定更新 | 環境変数の文書化 | 設定管理 | .env.example更新 |

## 🔧 トラブルシューティング

### よくある問題と対処法

#### 1. メルカリのタイトルが価格のみ
```bash
# 修正スクリプトを実行
python3 scripts/fix_mercari_title.py
```

#### 2. eBay認証エラー
```bash
# トークンをリフレッシュ
python3 scripts/refresh_ebay_token.py
```

#### 3. 統合検索タイムアウト
```bash
# タイムアウト設定を確認
grep -n "timeout" src/app/api/search/all/route.ts
```

## 📈 パフォーマンス指標

### 目標値
- 統合検索レスポンス: < 15秒
- 個別検索レスポンス: < 5秒
- 同時検索プラットフォーム数: 7

### 現在値
- 統合検索平均: 14秒
- 個別検索平均: 3-5秒
- 稼働率: 85.7% (6/7)

## 🗓️ メンテナンススケジュール

### 日次タスク
- [ ] ヘルスチェック実行
- [ ] エラーログ確認
- [ ] Seleniumサーバー再起動

### 週次タスク
- [ ] APIトークン有効期限確認
- [ ] パフォーマンステスト
- [ ] 依存関係アップデート確認

### 月次タスク
- [ ] セキュリティパッチ適用
- [ ] バックアップ実行
- [ ] コスト分析

## 🚨 緊急連絡先

### システムダウン時
1. ローカルSeleniumサーバー確認（Port 5001）
2. Next.jsプロセス確認
3. 環境変数確認（.env）

### APIエラー時
1. 各プラットフォームのAPI状態確認
2. レート制限確認
3. 認証情報の有効期限確認

## 📝 変更履歴

### 2025-05-28
- ✅ メルカリタイトル取得修正（aria-label対応）- PM実行
- ✅ PayPayフリマ重複除去実装 - PM実行
- ✅ ヨドバシタイムアウト対策 - PM実行
- ✅ eBay翻訳をOpenAI APIに移行 - PM実行
- ⏳ スクリプトファイル整理（未実行、エージェント報告は仮想）
- ⏳ プロジェクト文書整備（未確認、要検証）

### 次の実行計画

#### PM直接実行（優先度順）
1. [ ] スクリプト整理の実施（ブランチ作成→実装）
2. [ ] ラクマ修正の完了
3. [ ] ブランチ管理システムの確立

#### エージェント割り当て可能
1. [ ] 各プラットフォームの動作テスト実行
2. [ ] エラーログの収集と分類
3. [ ] APIレスポンス時間の測定

## 💡 改善提案

1. **キャッシュ機能の実装**
   - Redis導入で応答速度向上
   - 同一検索の重複防止

2. **エラー監視強化**
   - Sentryなどのエラートラッキング
   - アラート通知設定

3. **自動スケーリング**
   - 負荷に応じたSeleniumインスタンス管理
   - Dockerコンテナ化

## 🔄 ワークフロー管理

### ブランチ戦略
```
main
├── develop (統合ブランチ)
│   ├── feature/* (新機能)
│   ├── fix/* (バグ修正)
│   ├── refactor/* (リファクタリング)
│   └── docs/* (ドキュメント)
└── hotfix/* (緊急修正)
```

### Git操作手順
```bash
# 新機能ブランチ作成（PM実行）
git checkout -b feature/[機能名]

# 作業完了後（エージェント報告後）
git add .
git commit -m "feat: [変更内容]"
git push origin feature/[機能名]

# マージ（PM実行）
git checkout develop
git merge feature/[機能名]
git branch -d feature/[機能名]
```

## 📝 エージェントへの指示テンプレート

### 単純タスク用（エージェント向け）
```
【タスク】: [具体的なアクション]
【作業ディレクトリ】: [明確なパス]
【使用コマンド】: [実行すべきコマンド]
【期待する出力】: [具体的な成果物]

【手順】:
1. cd [作業ディレクトリ]
2. [コマンド1]
3. [コマンド2]
4. 結果を[ファイル名]に保存

【完了確認】:
- [ ] コマンドが正常終了
- [ ] 出力ファイルが作成
- [ ] エラーがないこと
```

### 技術タスク用（PM実行）
```
【タスク】: [技術的な課題]
【影響範囲】: [関連ファイル/システム]
【リスク】: [潜在的な問題]
【解決方針】: [アプローチ]

【実装計画】:
1. 現状分析
2. 設計決定
3. 実装
4. テスト
5. 統合
```

## 📋 タスク実行マトリックス

### どのタスクを誰が実行すべきか

| タスクカテゴリ | PM実行 | エージェント実行 | 理由 |
|--------------|--------|----------------|------|
| ブランチ作成・管理 | ✅ | ❌ | 全体構造への影響大 |
| アーキテクチャ設計 | ✅ | ❌ | 技術的判断必要 |
| コード統合・マージ | ✅ | ❌ | 競合解決が複雑 |
| ファイル整理 | ✅ | ❌ | 全体理解が必要 |
| API動作テスト | ❌ | ✅ | 手順が明確 |
| ドキュメント作成 | ❌ | ✅ | テンプレート化可能 |
| ログ分析 | ❌ | ✅ | パターン認識可能 |
| 性能測定 | ❌ | ✅ | 自動化可能 |

### 効率的な進め方
1. **PMが基盤を整備** → エージェントが詳細作業
2. **PMが方針決定** → エージェントが実行
3. **PMが統合** → エージェントが検証

## 🐳 Docker環境管理

### Docker-リポジトリ同期チェックリスト

#### 定期確認項目（CI/CD実行時・週次）
- [ ] package.jsonの変更時 → Dockerfileの再ビルド必要性確認
- [ ] requirements.txtの変更時 → Dockerfile.visual の更新確認
- [ ] 新規ディレクトリ作成時 → Docker内のCOPYコマンド確認
- [ ] .env.exampleの変更時 → .env.dockerの同期確認

#### 自動同期スクリプト
```bash
# Docker環境同期チェック（scripts/check_docker_sync.sh）
#!/bin/bash

echo "🐳 Docker環境同期チェック開始..."

# 1. package.jsonの更新確認
if git diff --name-only HEAD~1 | grep -q "package.json"; then
    echo "⚠️  package.jsonが更新されています。Dockerイメージの再ビルドが必要です。"
    echo "実行: docker-compose build --no-cache app app-dev"
fi

# 2. Python依存関係の確認
if git diff --name-only HEAD~1 | grep -E "requirements.*\.txt"; then
    echo "⚠️  Python依存関係が更新されています。"
    echo "実行: docker-compose build --no-cache visual"
fi

# 3. 環境変数の同期確認
diff .env.example .env.docker > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  .env.exampleと.env.dockerに差異があります。"
    echo "環境変数の同期を確認してください。"
fi

# 4. ボリュームマウントの確認
echo "📁 現在のボリュームマウント設定:"
grep -A5 "volumes:" docker-compose*.yml

echo "✅ チェック完了"
```

### Docker更新手順

#### 1. 依存関係更新時
```bash
# Node.js依存関係更新
npm install [package]
docker-compose build --no-cache app app-dev

# Python依存関係更新
echo "[package]" >> requirements-visual.txt
docker-compose build --no-cache visual
```

#### 2. 新規ファイル・ディレクトリ追加時
```bash
# Dockerfileを確認し、必要に応じてCOPYコマンドを追加
# 例: 新規scriptsディレクトリ追加時
# Dockerfile内に追加: COPY scripts/ ./scripts/
```

#### 3. 環境変数追加時
```bash
# 1. .env.exampleに追加
echo "NEW_VAR=example_value" >> .env.example

# 2. .env.dockerにも追加
echo "NEW_VAR=docker_value" >> .env.docker

# 3. docker-compose.ymlで必要に応じて参照
```

### Docker同期状態の可視化

```bash
# 同期状態レポート生成（月次実行推奨）
python3 scripts/generate_docker_sync_report.py

# 出力例:
# 📊 Docker同期レポート (2025-05-28)
# ✅ package.json: 同期済み
# ✅ requirements.txt: 同期済み
# ⚠️  環境変数: 3個の差異
# ✅ ディレクトリ構造: 一致
```

### トラブルシューティング

#### よくある同期問題

1. **node_modulesの不整合**
   ```bash
   # コンテナ内のnode_modulesを再構築
   docker-compose run --rm app npm ci
   ```

2. **Pythonパッケージの不整合**
   ```bash
   # requirements.txtを再生成
   docker-compose run --rm visual pip freeze > requirements-visual.txt
   ```

3. **ビルドキャッシュの問題**
   ```bash
   # 完全なクリーンビルド
   docker-compose down
   docker system prune -af
   docker-compose build --no-cache
   ```

### CI/CD統合

```yaml
# .github/workflows/docker-sync.yml
name: Docker Sync Check

on:
  push:
    paths:
      - 'package*.json'
      - 'requirements*.txt'
      - 'Dockerfile*'
      - '.env.example'

jobs:
  check-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check Docker Sync
        run: |
          chmod +x scripts/check_docker_sync.sh
          ./scripts/check_docker_sync.sh
```

## 🔗 関連ドキュメント

- [開発環境セットアップ](./docs/development_environment_setup.md)
- [API仕様書](./docs/api_specification.md)
- [トラブルシューティングガイド](./docs/troubleshooting_guide.md)
- [メモリーバンク](./MEMORY_BANK.md)
- [ToDoリスト](./TODO.md)