#!/bin/bash

# Docker環境用の環境変数設定スクリプト
# 既存の.envファイルから.env.dockerファイルを作成

echo "🐳 Docker環境用環境変数設定スクリプト"
echo "=================================="

# .envファイルの存在確認
if [ ! -f ".env" ]; then
    echo "❌ .envファイルが見つかりません。"
    echo "   まず .env.example をコピーして .env を作成し、正しいAPIキーを設定してください。"
    exit 1
fi

# .env.docker.exampleファイルの存在確認
if [ ! -f ".env.docker.example" ]; then
    echo "❌ .env.docker.exampleファイルが見つかりません。"
    exit 1
fi

echo "📋 .envファイルから環境変数を読み込み中..."

# .envファイルから環境変数を読み込み
source .env

# .env.docker.exampleをベースに.env.dockerを作成
cp .env.docker.example .env.docker

echo "🔧 環境変数を設定中..."

# 重要な環境変数を置換
if [ ! -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
    sed -i.bak "s|NEXT_PUBLIC_SUPABASE_URL=.*|NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL|" .env.docker
    echo "✅ NEXT_PUBLIC_SUPABASE_URL を設定しました"
fi

if [ ! -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
    sed -i.bak "s|NEXT_PUBLIC_SUPABASE_ANON_KEY=.*|NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY|" .env.docker
    echo "✅ NEXT_PUBLIC_SUPABASE_ANON_KEY を設定しました"
fi

if [ ! -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    sed -i.bak "s|SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY|" .env.docker
    echo "✅ SUPABASE_SERVICE_ROLE_KEY を設定しました"
fi

if [ ! -z "$EBAY_APP_ID" ]; then
    sed -i.bak "s|EBAY_APP_ID=.*|EBAY_APP_ID=$EBAY_APP_ID|" .env.docker
    echo "✅ EBAY_APP_ID を設定しました"
fi

if [ ! -z "$YAHOO_SHOPPING_APP_ID" ]; then
    sed -i.bak "s|YAHOO_SHOPPING_APP_ID=.*|YAHOO_SHOPPING_APP_ID=$YAHOO_SHOPPING_APP_ID|" .env.docker
    echo "✅ YAHOO_SHOPPING_APP_ID を設定しました"
fi

# その他のAPI設定も同様に処理
if [ ! -z "$SUPABASE_URL" ]; then
    sed -i.bak "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env.docker
fi

if [ ! -z "$SUPABASE_ANON_KEY" ]; then
    sed -i.bak "s|SUPABASE_ANON_KEY=.*|SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY|" .env.docker
fi

if [ ! -z "$SUPABASE_SERVICE_KEY" ]; then
    sed -i.bak "s|SUPABASE_SERVICE_KEY=.*|SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY|" .env.docker
fi

# バックアップファイルを削除
rm -f .env.docker.bak

echo ""
echo "🎉 Docker環境用環境変数の設定が完了しました！"
echo ""
echo "📁 作成されたファイル: .env.docker"
echo ""
echo "🚀 次のステップ:"
echo "   1. docker-compose.override.yml.example をコピー:"
echo "      cp docker-compose.override.yml.example docker-compose.override.yml"
echo ""
echo "   2. Docker環境を起動:"
echo "      docker-compose up --build"
echo ""
echo "   3. ヘルスチェックで確認:"
echo "      curl http://localhost:3000/api/health"
echo ""
