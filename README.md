# レコード販売データ分析ダッシュボード

複数のプラットフォーム（Discogs、eBay、Mercari、Yahooオークション）からのレコード販売データを分析し、利益計算結果を表示するダッシュボードWebアプリケーションです。

## 機能

- Supabaseに保存された利益計算結果の一覧表示
- 利益額の大きい順にソート
- プラットフォームでのフィルタリング
- 利益額範囲でのフィルタリング
- ページネーション
- レスポンシブデザイン
- 設定したキーワードを使って複数プラットフォームから並列に検索を行うコレクターAPI（`/api/collect`）
  - 利用するキーワードやプラットフォームは`src/lib/collectConfig.ts`で定義します

## 技術スタック

- **フロントエンド**: Next.js (React)
- **スタイリング**: Tailwind CSS
- **データベース**: Supabase (PostgreSQL)
- **デプロイ**: Vercel

## 開発環境のセットアップ

### 前提条件

- Node.js 18.x以上
- npm 9.x以上
- Supabaseアカウント

### インストール

1. リポジトリをクローン

```bash
git clone https://github.com/ryota-hagi/buy_records.git
cd buy_records
```

2. 依存関係をインストール

```bash
npm install
```

3. 環境変数を設定

`.env.example`ファイルを`.env.local`にコピーし、Supabaseの接続情報を設定します。

```bash
cp .env.example .env.local
```

`.env.local`ファイルを編集し、以下の値を設定します：

```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

4. 開発サーバーを起動

```bash
npm run dev
```

ブラウザで[http://localhost:3000](http://localhost:3000)を開いてアプリケーションを確認できます。

## デプロイ

このプロジェクトはVercelにデプロイするように設定されています。GitHubリポジトリをVercelに接続するだけで、自動的にデプロイされます。

1. [Vercel](https://vercel.com)にサインアップ/ログイン
2. 「New Project」をクリック
3. このリポジトリをインポート
4. 環境変数を設定
5. 「Deploy」をクリック

## データベース構造

このアプリケーションは、Supabaseの`price_comparison_results`テーブルからデータを取得します。テーブルの構造は以下の通りです：

```sql
CREATE TABLE price_comparison_results (
  id UUID PRIMARY KEY,
  release_id INTEGER,
  title TEXT NOT NULL,
  artist TEXT,
  best_source_platform TEXT,
  best_source_item_id TEXT,
  best_source_url TEXT,
  best_source_price DECIMAL,
  best_source_currency TEXT,
  best_target_platform TEXT,
  best_target_item_id TEXT,
  best_target_url TEXT,
  best_target_price DECIMAL,
  best_target_currency TEXT,
  profit_amount DECIMAL,
  profit_percentage DECIMAL,
  score DECIMAL,
  score_factors JSONB,
  thumbnail TEXT,
  genre TEXT[],
  style TEXT[],
  year INTEGER,
  country TEXT,
  format TEXT[],
  source_condition TEXT,
  target_condition TEXT,
  source_sold_count INTEGER,
  target_sold_count INTEGER,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
);
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
