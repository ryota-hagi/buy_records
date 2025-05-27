# Claude Assistant 設定

## 重要な指示

### 言語設定
- **必ず日本語で回答すること**
- ユーザーへの説明、エラーメッセージ、進捗報告などすべて日本語で行う
- コード内のコメントも可能な限り日本語で記述する

## プロジェクト概要

buy_recordsプロジェクトは、複数のオンラインマーケットプレイス（eBay、Yahoo Shopping、メルカリ、ラクマ）から商品を検索するシステムです。

### 主要コンポーネント
- Next.js フロントエンド
- Python スクレイピングスクリプト
- Apify Actor統合
- Docker環境サポート

### 現在の課題と対応状況
1. Apify Actorのデプロイメント問題
   - Actor ID: yVpUua8jmqTA0iwvO（Mercari Rakuma Scraper）
   - Actor ID: m6uuQHFAXYK3cwKL3（Mercari Scraper V2）
   - PlaywrightCrawler/PuppeteerCrawlerのモジュール読み込みエラーが発生中
   - Apifyのビルドシステムが古いコードをキャッシュしている問題
   - APIアクセス時に404エラーが発生する場合がある

2. タイムアウト設定
   - すべてのAPI呼び出しで300秒（5分）のタイムアウトを設定済み

### 環境変数
必要な環境変数：
- APIFY_API_TOKEN
- EBAY_CLIENT_ID
- EBAY_CLIENT_SECRET
- その他各プラットフォームのAPI認証情報

### テストとリントコマンド
プロジェクトで使用可能なコマンドを確認する場合は、package.jsonのscriptsセクションを参照してください。