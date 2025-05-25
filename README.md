# JANコード価格比較検索システム

JANコードを入力するだけで、複数のプラットフォーム（Discogs、eBay、メルカリ、Yahoo!オークション）から商品の最安値を検索・比較できるシステムです。

## 主な機能

- **JANコード検索**: 8桁または13桁のJANコードから商品を特定
- **並列検索**: 4つのプラットフォームを同時に検索
- **価格比較**: 送料・手数料込みの総額で比較
- **最安値表示**: 最大20件の最安値商品をリスト表示
- **タスク管理**: 検索タスクの作成・管理・キャンセル
- **結果保存**: 検索結果を7日間保存

## システム構成

### バックエンド (Python)
- **JANコードルックアップ**: JANコードから商品情報を取得
- **価格計算エンジン**: プラットフォーム別の手数料・送料計算
- **検索エンジン**: 並列検索とデータ統合
- **タスクマネージャー**: 検索タスクの管理

### フロントエンド (Next.js)
- **検索フォーム**: JANコード入力とバリデーション
- **タスク一覧**: 検索タスクの状態管理
- **結果表示**: 価格比較結果の表示

### データベース (Supabase)
- **jan_search_tasks**: 検索タスク管理
- **search_results**: 検索結果保存

## セットアップ

### 1. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して以下の値を設定：

```env
# JANコードルックアップAPI
JAN_LOOKUP_APP_ID=4aeb5c05a996d44e02329c8b33411ba2

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# API設定（オプション）
DISCOGS_TOKEN=your_discogs_token
# eBay API は EBAY_APP_ID を推奨しますが、
# 互換性のため EBAY_CLIENT_ID または EBAY_APPID でも利用できます
EBAY_APP_ID=your_ebay_app_id
# Yahoo Shopping API は YAHOO_SHOPPING_APP_ID を推奨しますが、
# 互換性のため YAHOO_APP_ID でも利用可能です
YAHOO_SHOPPING_APP_ID=your_yahoo_shopping_app_id
YAHOO_APP_ID=your_yahoo_app_id
```

### 2. データベースセットアップ

```bash
# テーブル作成
psql -h your_supabase_host -U postgres -d postgres -f scripts/create_jan_search_tables.sql
```

### 3. 依存関係のインストール

```bash
# Python依存関係
pip install -r requirements.txt

# Node.js依存関係
cd buy_records
npm install
```

### 4. システム起動

```bash
# フロントエンド起動
cd buy_records
npm run dev

# バックエンド検索エンジン（別ターミナル）
python scripts/jan_search_main.py
```

## 使用方法

### Webインターフェース

1. ブラウザで `http://localhost:3000/search` にアクセス
2. JANコードを入力（例: `4901234567890`）
3. 「価格比較検索を開始」ボタンをクリック
4. 検索完了まで待機（通常1-3分）
5. 結果を確認

### コマンドライン

```bash
# JANコード検索
python scripts/jan_search_main.py search 4901234567890

# タスク状況確認
python scripts/jan_search_main.py status <task_id>

# タスク一覧表示
python scripts/jan_search_main.py list

# 期限切れデータ削除
python scripts/jan_search_main.py cleanup
```

## API仕様

### 検索タスク作成

```http
POST /api/search/tasks
Content-Type: application/json

{
  "jan_code": "4901234567890"
}
```

### タスク一覧取得

```http
GET /api/search/tasks?page=1&limit=10&status=completed
```

### タスク詳細取得

```http
GET /api/search/tasks/{task_id}
```

### タスクキャンセル

```http
DELETE /api/search/tasks/{task_id}
```

## プラットフォーム別価格計算

### メルカリ
- 販売手数料: 10%
- 送料: 商品サイズに応じて210円〜750円

### eBay
- 落札手数料: 10%
- PayPal手数料: 2.9%
- 送料: 国内500円、国際1500円

### Yahoo!オークション
- システム利用料: 8.8%
- 送料: 商品サイズに応じて185円〜600円

### Discogs
- 手数料: 8.5%
- PayPal手数料: 2.9%
- 送料: 国内300円、国際1200円

## 拡張性

### 新しいプラットフォームの追加

1. `src/collectors/`に新しいコレクタークラスを作成
2. `src/jan/search_engine.py`に検索メソッドを追加
3. `src/pricing/calculator.py`に手数料設定を追加

### 新しい検索方式の追加

1. `src/jan/jan_lookup.py`にルックアップメソッドを追加
2. APIルートでバリデーションを更新
3. フロントエンドフォームを拡張

## トラブルシューティング

### よくある問題

1. **JANコードが見つからない**
   - JANコードが正しいか確認
   - 商品がJANコードルックアップAPIに登録されているか確認

2. **検索が完了しない**
   - ネットワーク接続を確認
   - API制限に達していないか確認
   - ログファイルでエラーを確認

3. **価格が表示されない**
   - プラットフォームでの商品の存在を確認
   - 検索キーワードの精度を確認

### ログ確認

```bash
# 検索ログ
tail -f search_tasks.log

# アプリケーションログ
cd buy_records
npm run dev
```

## ライセンス

MIT License

## 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。
