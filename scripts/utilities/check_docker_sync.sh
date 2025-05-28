#!/bin/bash

# Docker環境同期チェックスクリプト
# PROJECT_MANAGER.mdで定義された同期チェックを実行

echo "🐳 Docker環境同期チェック開始..."
echo "実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================="

# エラーカウンター
ERROR_COUNT=0

# 1. package.jsonの更新確認
echo "1️⃣ package.json更新チェック"
if [ -n "$(git status --porcelain package.json 2>/dev/null)" ] || \
   git diff --name-only HEAD~1 2>/dev/null | grep -q "package.json"; then
    echo "⚠️  package.jsonが更新されています。"
    echo "   → docker-compose build --no-cache app app-dev"
    ((ERROR_COUNT++))
else
    echo "✅ package.json: 変更なし"
fi

# 2. Python依存関係の確認
echo -e "\n2️⃣ Python依存関係チェック"
if [ -n "$(git status --porcelain | grep -E 'requirements.*\.txt')" ] || \
   git diff --name-only HEAD~1 2>/dev/null | grep -qE "requirements.*\.txt"; then
    echo "⚠️  Python依存関係が更新されています。"
    echo "   → docker-compose build --no-cache visual"
    ((ERROR_COUNT++))
else
    echo "✅ requirements.txt: 変更なし"
fi

# 3. 環境変数の同期確認
echo -e "\n3️⃣ 環境変数同期チェック"
if [ -f ".env.example" ] && [ -f ".env.docker" ]; then
    # 環境変数名のみを比較（値は無視）
    comm -23 <(grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort) \
             <(grep -E "^[A-Z_]+=" .env.docker | cut -d= -f1 | sort) > /tmp/env_diff_example
    comm -13 <(grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort) \
             <(grep -E "^[A-Z_]+=" .env.docker | cut -d= -f1 | sort) > /tmp/env_diff_docker
    
    if [ -s /tmp/env_diff_example ] || [ -s /tmp/env_diff_docker ]; then
        echo "⚠️  環境変数に差異があります:"
        if [ -s /tmp/env_diff_example ]; then
            echo "   .env.exampleのみ: $(cat /tmp/env_diff_example | tr '\n' ', ' | sed 's/,$//')"
        fi
        if [ -s /tmp/env_diff_docker ]; then
            echo "   .env.dockerのみ: $(cat /tmp/env_diff_docker | tr '\n' ', ' | sed 's/,$//')"
        fi
        ((ERROR_COUNT++))
    else
        echo "✅ 環境変数: 同期済み"
    fi
    rm -f /tmp/env_diff_example /tmp/env_diff_docker
else
    echo "⚠️  環境変数ファイルが見つかりません"
    [ ! -f ".env.example" ] && echo "   - .env.example が存在しません"
    [ ! -f ".env.docker" ] && echo "   - .env.docker が存在しません"
    ((ERROR_COUNT++))
fi

# 4. Dockerfileの整合性チェック
echo -e "\n4️⃣ Dockerfile整合性チェック"
DOCKERFILE_ISSUES=0

# package.jsonの依存関係がDockerfileでインストールされているか
if [ -f "package.json" ] && [ -f "Dockerfile" ]; then
    if ! grep -q "COPY.*package\*.json" Dockerfile; then
        echo "⚠️  Dockerfile: package.jsonがコピーされていません"
        ((DOCKERFILE_ISSUES++))
    fi
    if ! grep -q "npm.*install\|npm.*ci" Dockerfile; then
        echo "⚠️  Dockerfile: npm installが実行されていません"
        ((DOCKERFILE_ISSUES++))
    fi
fi

# srcディレクトリがコピーされているか
if [ -d "src" ] && [ -f "Dockerfile" ]; then
    if ! grep -q "COPY.*src\|COPY \." Dockerfile; then
        echo "⚠️  Dockerfile: srcディレクトリがコピーされていません"
        ((DOCKERFILE_ISSUES++))
    fi
fi

if [ $DOCKERFILE_ISSUES -eq 0 ]; then
    echo "✅ Dockerfile: 整合性OK"
else
    ((ERROR_COUNT++))
fi

# 5. ボリュームマウントの確認
echo -e "\n5️⃣ ボリュームマウント設定"
echo "📁 現在の設定:"
grep -A5 "volumes:" docker-compose*.yml 2>/dev/null | grep -E "^\s+-" | sed 's/^/   /'

# 6. Docker Composeファイルの検証
echo -e "\n6️⃣ Docker Compose検証"
if command -v docker-compose &> /dev/null; then
    if docker-compose config > /dev/null 2>&1; then
        echo "✅ docker-compose.yml: 構文OK"
    else
        echo "⚠️  docker-compose.yml: 構文エラー"
        docker-compose config 2>&1 | grep -E "ERROR|error" | sed 's/^/   /'
        ((ERROR_COUNT++))
    fi
else
    echo "ℹ️  docker-composeコマンドが利用できません（検証スキップ）"
fi

# 7. 未追跡ファイルのチェック
echo -e "\n7️⃣ 未追跡ファイルチェック"
UNTRACKED=$(git ls-files --others --exclude-standard | grep -vE "node_modules|\.next|__pycache__|\.env$" | head -10)
if [ -n "$UNTRACKED" ]; then
    echo "⚠️  Dockerに含まれない可能性のある未追跡ファイル:"
    echo "$UNTRACKED" | sed 's/^/   - /'
    [ $(echo "$UNTRACKED" | wc -l) -eq 10 ] && echo "   ... 他にもあります"
fi

# 結果サマリー
echo -e "\n================================="
echo "🏁 チェック完了"
if [ $ERROR_COUNT -eq 0 ]; then
    echo "✅ すべての項目が同期されています！"
    exit 0
else
    echo "⚠️  $ERROR_COUNT 個の同期問題が見つかりました"
    echo "上記の指示に従って同期を行ってください"
    exit 1
fi