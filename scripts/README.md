# Scripts Directory Structure

## 📁 ディレクトリ構成

### 🧪 testing/
テスト関連スクリプト
- test_*.py - 各種テストスクリプト

### 🔍 search/
検索機能関連
- search_*.py - プラットフォーム別検索スクリプト
- fetch_*.py - データ取得スクリプト

### 🛠️ debug/
デバッグ・診断用
- debug_*.py - デバッグスクリプト
- diagnose_*.py - 診断スクリプト
- analyze_*.py - 分析スクリプト

### 📊 database/
データベース関連
- create_*_table.sql - テーブル作成SQL
- create_*_table*.py - テーブル作成スクリプト

### 🔧 utilities/
ユーティリティ
- check_*.py - チェック・検証スクリプト
- fix_*.py - 修正スクリプト
- generate_*.py - 生成スクリプト

### 🚀 deployment/
デプロイ・運用関連
- deploy_*.py - デプロイスクリプト
- setup_*.sh - セットアップスクリプト

### 📦 api/
API関連
- *_api*.py - API関連スクリプト
- apify_*.py - Apify関連

### 🏃 runners/
実行・処理系
- *_runner.py - ランナースクリプト
- run_*.py - 実行スクリプト
- start_*.py - 起動スクリプト

### 🗑️ deprecated/
非推奨・削除予定
- 古いスクリプトや使用されていないファイル

## 📝 命名規則

- `test_` - テストスクリプト
- `search_` - 検索機能
- `debug_` - デバッグ用
- `create_` - 作成・生成
- `check_` - チェック・検証
- `fix_` - 修正・改善
- `analyze_` - 分析
- `fetch_` - データ取得