# 🧠 MEMORY BANK - buy_records
## エージェント共通ナレッジベース

### 📅 最終更新: 2025-05-29
### 📊 システム状態: 安定化作業中（エラー率73.77% → 目標10%以下）

---

## 🏢 プロジェクト概要

### 🎯 ミッション
複数のECサイトから商品情報を収集・比較する買い物比較プラットフォームの開発・運用

### 🏗️ システム構成
- **フロントエンド**: Next.js 15.3.2 + React + TypeScript
- **バックエンド**: Next.js API Routes + Python スクレイピング
- **データベース**: Supabase (PostgreSQL)
- **インフラ**: Docker + Selenium + Vercel
- **AI**: OpenAI GPT-4o-mini (翻訳・データ解析)
- **開発支援**: MCP (Model Context Protocol) - **エージェント利用推奨**

---

## 👥 チーム組織構造

### 🎯 プロジェクトリーダー (PL)
- **責務**: 戦略策定、優先順位決定、全体統括
- **権限**: 最終意思決定、リソース配分、品質基準設定

### 🤝 右腕エージェント (Technical Lead)
- **責務**: 技術実装統括、Git管理、品質確認、デプロイ
- **権限**: ブランチ管理、コード統合、専門チーム指揮

### 👥 専門エージェントチーム
1. **フロントエンド開発**: UI/UX、React/Next.js、スタイリング
2. **バックエンド開発**: API、データベース、サーバーロジック
3. **スクレイピング開発**: プラットフォーム別コレクター、Selenium
4. **DevOps・インフラ**: Docker、CI/CD、デプロイメント
5. **QA・テスト**: 統合テスト、品質保証、バグ検証

---

## 🌐 プラットフォーム一覧

### ✅ 稼働中プラットフォーム
| プラットフォーム | 技術方式 | 状態 | 最終確認 | 特記事項 |
|--------------|---------|------|---------|----------|
| 楽天 | REST API | ✅ | 2025-05-28 | APIキー設定済み |
| Yahoo!ショッピング | REST API | ✅ | 2025-05-28 | 安定動作 |
| eBay | REST API | ⚠️ | 2025-05-29 | 認証修正中 |
| メルカリ | Selenium | ✅ | 2025-05-28 | aria-label対応済み |
| PayPayフリマ | Selenium | ✅ | 2025-05-28 | 重複除去実装済み |
| ヨドバシ | Web API | ✅ | 2025-05-28 | リトライロジック有 |

### 🔄 修正・開発中
| プラットフォーム | 課題 | 対応状況 | 担当 |
|--------------|------|---------|------|
| ラクマ | URL変更、セレクタ更新 | 修正完了 | スクレイピング専門 |
| eBay | 認証エラー (401) | Client Credentials切替済み | バックエンド専門 |

### ❌ 未対応・停止中
- **au PAYマーケット**: ドメイン問題
- **Amazon**: API認証未設定

---

## 🔧 技術スタック詳細

### 📦 主要依存関係
```json
{
  "next": "15.3.2",
  "react": "^18.2.0",
  "supabase": "^2.15.1",
  "selenium-webdriver": "^4.15.0",
  "openai": "^4.20.1",
  "tenacity": "^8.2.3"
}
```

### 🌍 環境変数 (重要)
```bash
# Supabase
SUPABASE_URL=https://ggvuuixcswldxfeygxvy.supabase.co
SUPABASE_SERVICE_KEY=[サービスキー]
NEXT_PUBLIC_SUPABASE_URL=[公開URL]
NEXT_PUBLIC_SUPABASE_ANON_KEY=[匿名キー]

# eBay API
EBAY_APP_ID=ariGaT-records-PRD-1a6ee1171-104bfaa4
EBAY_CLIENT_SECRET=[シークレット]
EBAY_ENVIRONMENT=PRODUCTION
# EBAY_USER_TOKEN=[無効化済み - Client Credentials使用]

# OpenAI
OPENAI_API_KEY=[APIキー]

# Yahoo Shopping
YAHOO_SHOPPING_APP_ID=[アプリID]

# JAN Code Lookup
JAN_LOOKUP_APP_ID=[アプリID]
```

### 🐳 Docker環境
```yaml
# docker-compose.yml
services:
  app:        # Next.js アプリケーション
  app-dev:    # 開発環境
  visual:     # Python + Selenium + OpenAI
```

---

## 📁 プロジェクト構造

### 🏗️ ディレクトリマップ
```
buy_records/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── api/            # API Routes
│   │   │   ├── health/     # ヘルスチェック
│   │   │   └── search/     # 検索エンドポイント
│   │   └── search/         # フロントエンド ページ
│   ├── collectors/         # プラットフォーム別スクレイパー
│   ├── components/         # React コンポーネント
│   ├── utils/              # ユーティリティ
│   └── visual_scraper/     # AI Visual スクレイピング
├── scripts/                # バッチ処理・ツール
│   ├── api/               # API関連スクリプト
│   ├── database/          # DB操作
│   ├── debug/             # デバッグツール
│   ├── search/            # 検索関連
│   └── testing/           # テストスクリプト
├── logs/                   # ログファイル
└── docs/                   # ドキュメント
```

### 🔍 重要ファイル
- `src/utils/supabase_client.py` - DB接続 (シングルトンパターン実装済み)
- `src/collectors/` - 各プラットフォームのコレクター
- `src/app/api/search/all/route.ts` - 統合検索API
- `PROJECT_MANAGER.md` - 組織・戦略ドキュメント
- `MEMORY_BANK.md` - このファイル

---

## 🚨 現在の重要課題

### 🔴 最優先 (PL管理)
1. **システム安定性向上**: エラー率73.77% → 10%以下
2. **プラットフォーム稼働率**: 85.7% → 100%
3. **チーム生産性向上**: 戦略的エージェント活用

### 🟡 進行中 (右腕 + 専門チーム)
1. **ラクマ修正**: URL・セレクタ更新 (修正済み、テスト待ち)
2. **eBay API**: Client Credentials認証移行 (実装済み、検証中)
3. **Supabase安定化**: 接続プール・リトライ実装 (完了)

### 🟢 次期対応
1. OpenAI APIレート制限対策
2. Docker環境統合テスト
3. パフォーマンス最適化

---

## 📊 パフォーマンス指標

### 🎯 目標値
- **統合検索レスポンス**: < 15秒
- **個別検索レスポンス**: < 5秒
- **エラー率**: < 10%
- **プラットフォーム稼働率**: 100%

### 📈 現在値 (2025-05-29)
- **統合検索平均**: 14秒
- **個別検索平均**: 3-5秒
- **エラー率**: 73.77% (改善作業中)
- **稼働率**: 85.7% (6/7プラットフォーム)

---

## 🔄 ワークフロー標準

### 📋 タスク実行標準手順
1. **受領**: 右腕またはPLからの明確な指示
2. **分析**: 技術要件・影響範囲・リスクの把握
3. **実装**: コーディング・テスト・ドキュメント
4. **検証**: 品質確認・統合テスト
5. **報告**: 成果物提出・完了報告

### 🔧 Git運用ルール
- **ブランチ命名**: `feature/[機能名]`, `fix/[修正内容]`, `refactor/[リファクタ内容]`
- **コミットメッセージ**: `feat:`, `fix:`, `refactor:`, `docs:` プレフィックス
- **マージ権限**: 右腕エージェントのみ
- **プルリクエスト**: 必須（右腕がレビュー・承認）

### 🧪 テスト基準
- **ユニットテスト**: 新規機能は必須
- **結合テスト**: API・DB連携は必須
- **エラーハンドリング**: 例外ケース対応確認
- **パフォーマンステスト**: レスポンス時間測定

---

## 📝 通信プロトコル

### 🤝 右腕エージェントとの連携
```
【進捗報告】: [完了/進行中/課題]
【技術実装】: [実装内容の詳細]
【品質状況】: [テスト結果・品質指標]
【統合状況】: [他モジュールとの統合状況]
【次のアクション】: [次に必要な作業]
```

### 👥 専門エージェント間の情報共有
```
【担当領域】: [フロント/バック/スクレイピング/DevOps/QA]
【作業内容】: [具体的実装・修正内容]
【影響範囲】: [他チームへの影響]
【依存関係】: [他チームからの要求事項]
【完了予定】: [スケジュール]
```

---

## 🔍 トラブルシューティング

### 🚨 よくある問題と解決法

#### 1. **Seleniumエラー**
```bash
# Chrome Driver確認
which chromedriver
# 更新が必要な場合
brew install chromedriver
```

#### 2. **Supabase接続エラー**
```python
# 接続テスト
from src.utils.supabase_client import check_connection
print(check_connection())
```

#### 3. **eBay API認証エラー**
```bash
# 環境変数確認
echo $EBAY_USER_TOKEN  # 空であることを確認
echo $EBAY_CLIENT_SECRET  # 設定済みであることを確認
```

#### 4. **Next.js ビルドエラー**
```bash
# 依存関係リセット
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 学習リソース

### 🔗 技術ドキュメント
- [Next.js App Router](https://nextjs.org/docs/app)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Selenium WebDriver](https://selenium-python.readthedocs.io/)
- [OpenAI API](https://platform.openai.com/docs)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) - **利用推奨**

### 📖 プロジェクト固有ドキュメント
- `docs/api_specification.md` - API仕様
- `docs/development_environment_setup.md` - 開発環境
- `docs/troubleshooting_guide.md` - トラブルシューティング
- `PROJECT_MANAGER.md` - 組織・戦略

---

## 🎯 成功基準

### ✅ 品質基準
- **コードカバレッジ**: > 80%
- **レスポンス時間**: 目標値以内
- **エラー率**: < 10%
- **可用性**: > 99%

### 📊 KPI
- **新機能開発速度**: 要件定義から本番リリースまで < 2週間
- **バグ修正速度**: 発見から修正完了まで < 48時間
- **チーム生産性**: 並行作業によるスループット向上

---

## 💡 ベストプラクティス

### 🛡️ セキュリティ
- 環境変数での機密情報管理
- APIキーの定期ローテーション
- ログから機密情報の除外

### 🚀 パフォーマンス
- データベース接続プール活用
- APIレスポンスキャッシュ
- 並行処理による高速化

### 🧹 コード品質
- TypeScript型安全性の活用
- ESLint・Prettierでの統一フォーマット
- 適切なエラーハンドリング

### 🤖 AI開発支援
- **MCP (Model Context Protocol) 利用推奨**
  - ファイル操作・Git管理・データベース操作の効率化
  - エージェント間でのコンテキスト共有
  - リアルタイム情報取得とプロジェクト状態把握
  - 複雑なワークフローの自動化サポート
- MCPサーバーが利用可能な場合は積極的に活用
- 従来ツールとMCPのハイブリッド利用で生産性最大化

---

## 📞 エスカレーション

### 🚨 緊急時連絡先
1. **システムダウン**: 右腕エージェント → PL
2. **セキュリティ**: 即座にPLに報告
3. **重大バグ**: 発見者 → 右腕 → PL
4. **技術判断**: 専門エージェント → 右腕 → PL

### ⏰ 対応時間
- **緊急**: 即座
- **高優先**: 24時間以内
- **中優先**: 48時間以内
- **低優先**: 1週間以内

---

*このメモリーバンクは全エージェントの共通リファレンスです。最新情報は常にこのファイルで確認してください。*