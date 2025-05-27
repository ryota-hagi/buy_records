# 開発ワークフロー

## プロジェクト構造の概要

```
検索機能拡張 + プラットフォーム拡張
├── 検索タイプ拡張（垂直展開）
│   ├── JANコード検索（実装済み）
│   ├── 商品名検索
│   ├── 画像検索
│   └── 自然言語検索
└── プラットフォーム拡張（水平展開）
    ├── 既存: eBay, メルカリ, Yahoo!ショッピング
    ├── Phase A: ヤフオク!, ラクマ, Amazon
    ├── Phase B: Discogs, Reverb, StockX
    └── Phase C: BOOTH, BASE
```

## 開発の進め方

### 1. 新機能開発の基本フロー

```bash
# 1. 最新のdevelopブランチを取得
git checkout develop
git pull origin develop

# 2. 機能ブランチを作成
git checkout -b feature/<機能名>

# 3. 開発作業
# ... コーディング ...

# 4. コミット
git add .
git commit -m "feat: <機能の説明>"

# 5. プッシュ
git push -u origin feature/<機能名>

# 6. Pull Requestを作成
# GitHubでPRを作成し、developへマージ
```

### 2. プラットフォーム追加の手順

```bash
# 1. プラットフォームアダプター作成
./scripts/create-platform-adapter.sh "Platform Name" platform-code

# 2. 実装
# - src/platforms/adapters/platform-code/platform-code.adapter.ts を編集
# - 検索ロジックを実装

# 3. 環境変数追加
# .env.local に追加:
# PLATFORM_CODE_API_KEY=xxx
# PLATFORM_CODE_API_ENDPOINT=xxx

# 4. 登録
# src/platforms/index.ts で登録処理を追加

# 5. テスト
npm test src/platforms/adapters/platform-code
```

### 3. 検索機能追加の手順

```bash
# 1. インターフェース確認
# src/search/interfaces/search-request.ts
# src/search/interfaces/search-response.ts

# 2. 検索エンジン作成
# src/search/engines/<search-type>-search.ts

# 3. APIエンドポイント作成
# src/app/api/search/<search-type>/route.ts

# 4. フロントエンドコンポーネント作成
# src/components/SearchForm/<SearchType>Input.tsx

# 5. 統合
# src/app/api/search/unified/route.ts に追加
```

## 並行開発のガイドライン

### チーム分担例

#### チーム1: 検索機能チーム
```
担当者A: 商品名検索
├── feature/product-name-search
├── キーワード生成AIの実装
└── フロントエンド入力フォーム

担当者B: 画像検索
├── feature/image-search
├── OCR実装
├── Vision API統合
└── 画像アップロードUI

担当者C: 自然言語検索
├── feature/natural-language-search
├── NLP処理
└── 条件抽出ロジック
```

#### チーム2: プラットフォームチーム
```
担当者D: 国内プラットフォーム
├── feature/platform-yahoo-auction
├── feature/platform-rakuma
└── feature/platform-amazon-jp

担当者E: 海外プラットフォーム
├── feature/platform-discogs
├── feature/platform-reverb
└── feature/platform-stockx
```

### コンフリクト回避のルール

1. **インターフェースの凍結**
   - Phase 1完了後、インターフェースは変更禁止
   - 変更が必要な場合は全員で協議

2. **ディレクトリの分離**
   - 各機能は独立したディレクトリで開発
   - 共通コンポーネントは`common/`に配置

3. **定期的な同期**
   ```bash
   # 毎日実行
   git checkout develop
   git pull origin develop
   git checkout feature/<自分のブランチ>
   git merge develop
   ```

## CI/CDパイプライン

### 自動実行されるチェック

1. **Pre-commit**
   - ESLint
   - Prettier
   - TypeScript型チェック

2. **GitHub Actions（PR時）**
   - ユニットテスト
   - 統合テスト
   - ビルドチェック

3. **マージ後**
   - Vercelへの自動デプロイ（develop）
   - パフォーマンステスト

## テスト戦略

### 1. ユニットテスト
```bash
# 個別テスト
npm test src/platforms/adapters/ebay

# 全体テスト
npm test
```

### 2. 統合テスト
```bash
# ローカルで統合テスト
npm run test:integration

# 特定プラットフォームのみ
npm run test:integration -- --platform=ebay
```

### 3. E2Eテスト
```bash
# Cypressで実行
npm run test:e2e
```

## デバッグTips

### 1. プラットフォーム個別テスト
```bash
# 特定プラットフォームのみで検索
curl "http://localhost:3000/api/search/unified?query=test&platforms=ebay"
```

### 2. ログ確認
```typescript
// 開発時のみ詳細ログ
if (process.env.NODE_ENV === 'development') {
  console.log('Platform response:', response);
}
```

### 3. プラットフォーム状態確認
```bash
# ヘルスチェック
curl "http://localhost:3000/api/platforms/health"

# 統計情報
curl "http://localhost:3000/api/platforms/stats"
```

## リリースフロー

### 1. Feature → Develop
- PR作成
- コードレビュー（最低1名）
- テスト合格
- マージ

### 2. Develop → Staging
- 週次でステージング環境へ
- 統合テスト実施
- パフォーマンステスト

### 3. Staging → Main
- ステークホルダー承認
- 本番リリース
- モニタリング開始

## トラブルシューティング

### よくある問題

1. **API制限エラー**
   ```typescript
   // レート制限の実装例
   import { RateLimiter } from '../utils/rate-limiter';
   
   const limiter = new RateLimiter({
     maxRequests: 60,
     windowMs: 60000
   });
   ```

2. **タイムアウト**
   ```typescript
   // タイムアウト設定
   const controller = new AbortController();
   setTimeout(() => controller.abort(), 30000);
   ```

3. **メモリリーク**
   - Seleniumドライバーの適切なクローズ
   - 大きな画像の処理後のメモリ解放

## ドキュメント管理

### 必須ドキュメント

1. **プラットフォーム追加時**
   - `docs/platforms/<platform-code>.md`
   - API仕様
   - 認証方法
   - 制限事項

2. **機能追加時**
   - `docs/features/<feature-name>.md`
   - 使用方法
   - 技術仕様
   - 制限事項

## 連絡・相談

### Slackチャンネル（仮）
- `#buy-records-dev`: 開発全般
- `#buy-records-platforms`: プラットフォーム追加
- `#buy-records-search`: 検索機能拡張

### 定例会議（仮）
- 月曜: 週次計画
- 水曜: 進捗共有
- 金曜: デモ・振り返り