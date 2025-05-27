# Buy Records クイックスタートガイド

## 🚀 今すぐ始める

### 1. 初期セットアップ（10分）

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/buy_records.git
cd buy_records

# 依存関係をインストール
npm install

# 環境変数を設定
cp .env.example .env.local
# .env.localを編集して必要なAPIキーを設定

# 開発サーバーを起動
npm run dev
```

### 2. 動作確認

ブラウザで http://localhost:3000 を開いて、検索機能をテスト:
- JANコード例: 4988001531654
- 検索結果が表示されることを確認

## 📋 今週のタスク

### Phase 0: 基盤整備（今週中に完了）

#### Day 1-2: プロジェクト管理
```bash
# GitHubプロジェクトボードを作成
gh project create --title "Buy Records Development" --owner @me

# イシューテンプレートを追加
mkdir -p .github/ISSUE_TEMPLATE
# docs/project_management_setup.mdからテンプレートをコピー
```

#### Day 3-4: 開発環境
```bash
# Docker環境を起動
docker-compose up -d

# データベースをセットアップ
npm run db:setup
```

#### Day 5: CI/CD
```bash
# GitHub Actionsを設定
cp .github/workflows/ci.yml.example .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow"
git push origin feature/ci-setup
```

## 🛠️ 開発フロー

### 新機能の追加
1. **ブランチを作成**
   ```bash
   git checkout -b feature/product-name-search
   ```

2. **コードを実装**
   - 既存のパターンに従う
   - テストを書く
   - ドキュメントを更新

3. **プルリクエストを作成**
   ```bash
   gh pr create --title "feat: add product name search"
   ```

### 新プラットフォームの追加
```bash
# 自動化スクリプトを使用
./scripts/create-platform-adapter.sh "Platform Name" platform-code

# 生成されたファイルを編集
code src/platforms/adapters/platform-code-adapter.ts
```

## 📚 重要なドキュメント

1. **[マスター実装ロードマップ](./master_implementation_roadmap.md)**
   - 全体の計画とスケジュール
   - フェーズ別の実装内容

2. **[開発環境セットアップ](./development_environment_setup.md)**
   - 詳細な環境構築手順
   - トラブルシューティング

3. **[プロジェクト管理](./project_management_setup.md)**
   - GitHubプロジェクトボード
   - スプリント管理

## 🔧 便利なコマンド

```bash
# 開発サーバー起動
npm run dev

# テスト実行
npm test

# 型チェック
npm run typecheck

# リント実行
npm run lint

# ビルド
npm run build

# 統合テスト
npm run test:integration
```

## 🏗️ プロジェクト構造

```
buy_records/
├── src/
│   ├── app/           # Next.js App Router
│   ├── search/        # 検索エンジン
│   ├── platforms/     # プラットフォームアダプター
│   └── components/    # UIコンポーネント
├── scripts/           # ユーティリティスクリプト
├── tests/            # テストファイル
└── docs/             # ドキュメント
```

## 🎯 次のマイルストーン

### Week 1（～2/3）
- [ ] 基盤整備の完了
- [ ] 商品名検索の設計開始
- [ ] CI/CDパイプライン稼働

### Week 2（2/4～2/10）
- [ ] 商品名検索API実装
- [ ] 既存プラットフォーム統合
- [ ] 基本的なUIの実装

## 💡 Tips

1. **並行開発を活用**
   - 検索機能とプラットフォーム拡張は独立して進められる
   - 早めにブランチを切って作業開始

2. **テストファースト**
   - 実装前にテストケースを書く
   - 統合テストで品質を保証

3. **ドキュメント更新**
   - 実装と同時にドキュメントも更新
   - 他の開発者のために手順を残す

## 🆘 困ったときは

1. **[トラブルシューティング](./development_environment_setup.md#8-トラブルシューティング)**を確認
2. GitHubでIssueを作成
3. Slackの#dev-helpチャンネルで質問

## 📈 進捗確認

毎週金曜日に進捗を確認:
- 完了したタスク
- 次週の計画
- ブロッカーの有無

---

**Ready to start? 🚀**

```bash
npm run dev
```

http://localhost:3000 を開いて開発開始！