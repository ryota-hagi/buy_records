# 開発環境セットアップガイド

## 前提条件

### 必須ソフトウェア
- Node.js 20.x以上
- Python 3.11以上
- Docker Desktop
- Git
- Chrome/Chromium（Seleniumテスト用）

### 推奨ツール
- Visual Studio Code
- GitHub CLI
- Postman/Insomnia（API開発）

## 1. リポジトリのクローンと初期設定

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/buy_records.git
cd buy_records

# 依存関係のインストール
npm install

# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python依存関係のインストール
pip install -r requirements.txt
```

## 2. 環境変数の設定

### 2.1 環境変数ファイルの作成
```bash
# .env.localファイルを作成
cp .env.example .env.local
```

### 2.2 必須環境変数
```env
# Supabase設定
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# OpenAI設定（AI機能用）
OPENAI_API_KEY=your_openai_api_key

# eBay API設定
EBAY_APP_ID=your_ebay_app_id
EBAY_CERT_ID=your_ebay_cert_id
EBAY_DEV_ID=your_ebay_dev_id
EBAY_REDIRECT_URI=http://localhost:3000/api/ebay/callback

# Yahoo API設定
YAHOO_CLIENT_ID=your_yahoo_client_id
YAHOO_CLIENT_SECRET=your_yahoo_client_secret

# Apify設定（スクレイピング用）
APIFY_API_TOKEN=your_apify_token

# 開発環境設定
NODE_ENV=development
PYTHON_ENV=development
```

## 3. Docker環境のセットアップ

### 3.1 Dockerコンテナの起動
```bash
# 開発用Docker環境の起動
docker-compose up -d

# ログの確認
docker-compose logs -f
```

### 3.2 docker-compose.override.yml
```yaml
version: '3.8'

services:
  app:
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    ports:
      - "3000:3000"
      - "9229:9229"  # Node.js debugger

  postgres:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=localpassword

  redis:
    ports:
      - "6379:6379"
```

## 4. データベースのセットアップ

### 4.1 Supabaseローカル環境
```bash
# Supabase CLIのインストール
npm install -g supabase

# ローカルSupabaseの起動
supabase start

# マイグレーションの実行
supabase db push
```

### 4.2 初期データの投入
```bash
# テーブルの作成
psql -h localhost -U postgres -d postgres -f scripts/create_search_tasks_table.sql
psql -h localhost -U postgres -d postgres -f scripts/create_search_results_table.sql
psql -h localhost -U postgres -d postgres -f scripts/create_ebay_table.sql
psql -h localhost -U postgres -d postgres -f scripts/create_mercari_table.sql
psql -h localhost -U postgres -d postgres -f scripts/create_yahoo_auction_table.sql
```

## 5. 開発サーバーの起動

### 5.1 Next.js開発サーバー
```bash
# 開発サーバーの起動
npm run dev

# 別ターミナルでPythonスクリプトの監視
python scripts/start_task_processor.py
```

### 5.2 確認URL
- フロントエンド: http://localhost:3000
- API Health Check: http://localhost:3000/api/health
- Supabase Studio: http://localhost:54323

## 6. VS Code設定

### 6.1 推奨拡張機能
`.vscode/extensions.json`
```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma",
    "ms-azuretools.vscode-docker",
    "github.copilot"
  ]
}
```

### 6.2 デバッグ設定
`.vscode/launch.json`
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 9229,
      "env": {
        "NODE_OPTIONS": "--inspect"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

## 7. テスト環境

### 7.1 単体テストの実行
```bash
# TypeScript/JavaScriptテスト
npm test

# Pythonテスト
pytest

# カバレッジレポート
npm run test:coverage
pytest --cov=src --cov-report=html
```

### 7.2 E2Eテスト
```bash
# Playwrightのインストール
npx playwright install

# E2Eテストの実行
npm run test:e2e
```

## 8. トラブルシューティング

### 8.1 よくある問題

#### Python実行エラー
```bash
# Python 3を明示的に指定
alias python=python3
alias pip=pip3
```

#### ポート競合
```bash
# 使用中のポートを確認
lsof -i :3000
lsof -i :5432

# プロセスの停止
kill -9 <PID>
```

#### 依存関係エラー
```bash
# node_modulesの再インストール
rm -rf node_modules package-lock.json
npm install

# Pythonパッケージの再インストール
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 8.2 ログの確認
```bash
# Next.jsログ
tail -f .next/server/logs/*.log

# Dockerログ
docker-compose logs -f app

# Pythonログ
tail -f logs/python-app.log
```

## 9. 開発フロー

### 9.1 ブランチ作成
```bash
# 最新のdevelopブランチから作成
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 9.2 コミット規約
```bash
# コミットメッセージの形式
# type(scope): subject
# 
# 例:
git commit -m "feat(search): add product name search API"
git commit -m "fix(mercari): resolve scraping timeout issue"
git commit -m "docs(readme): update setup instructions"
```

### 9.3 プルリクエスト
```bash
# 変更をプッシュ
git push origin feature/your-feature-name

# GitHub CLIでPR作成
gh pr create --title "feat: add product name search" --body "Description of changes"
```

## 10. 便利なスクリプト

### 10.1 開発用エイリアス
```bash
# ~/.bashrc or ~/.zshrcに追加
alias br-dev="cd ~/buy_records && npm run dev"
alias br-test="cd ~/buy_records && npm test"
alias br-build="cd ~/buy_records && npm run build"
alias br-logs="cd ~/buy_records && tail -f logs/*.log"
```

### 10.2 データリセット
```bash
# create_reset_dev_data.sh
#!/bin/bash
echo "Resetting development data..."
docker-compose down -v
docker-compose up -d postgres
sleep 5
psql -h localhost -U postgres -d postgres < scripts/reset_database.sql
echo "Development data reset complete!"
```

## 次のステップ

1. 環境変数ファイルの設定を完了する
2. `npm run dev`で開発サーバーを起動
3. http://localhost:3000 にアクセスして動作確認
4. テストを実行して環境が正しく設定されているか確認

問題が発生した場合は、[トラブルシューティング](#8-トラブルシューティング)セクションを参照してください。