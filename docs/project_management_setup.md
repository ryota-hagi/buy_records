# プロジェクト管理セットアップガイド

## 1. GitHub Project Board設定

### 1.1 プロジェクトボードの作成
```bash
# GitHub CLIを使用してプロジェクトを作成
gh project create --title "Buy Records Development" --owner @me
```

### 1.2 ボード構成
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│   Backlog   │    Todo     │ In Progress │   Review    │    Done     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 未着手タスク │ 今週の作業  │  開発中     │ レビュー中   │  完了済み   │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### 1.3 ラベル体系
```yaml
# 種別ラベル
- feature: 新機能
- enhancement: 機能改善
- bug: バグ修正
- documentation: ドキュメント
- infrastructure: インフラ/CI/CD

# 優先度ラベル
- priority-high: 高優先度
- priority-medium: 中優先度
- priority-low: 低優先度

# コンポーネントラベル
- search-engine: 検索エンジン関連
- platform-adapter: プラットフォーム統合
- api: API関連
- frontend: フロントエンド
- database: データベース

# 状態ラベル
- blocked: ブロック中
- needs-discussion: 議論必要
- ready-for-review: レビュー準備完了
```

## 2. マイルストーン設定

### 2.1 マイルストーンの作成
```bash
# Phase 0: 基盤整備
gh milestone create --title "Phase 0: Foundation" --due-date 2025-02-03

# Phase 1: 検索機能拡張
gh milestone create --title "Phase 1: Search Enhancement" --due-date 2025-03-03

# Phase 2: 国内プラットフォーム
gh milestone create --title "Phase 2: Domestic Platforms" --due-date 2025-03-24

# Phase 3: 高度な検索
gh milestone create --title "Phase 3: Advanced Search" --due-date 2025-04-14

# Phase 4: 国際プラットフォーム
gh milestone create --title "Phase 4: International Platforms" --due-date 2025-05-12
```

## 3. イシューテンプレート

### 3.1 機能追加テンプレート
`.github/ISSUE_TEMPLATE/feature_request.md`
```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: 'feature'
assignees: ''
---

## 概要
機能の簡潔な説明

## 背景・目的
なぜこの機能が必要か

## 提案する解決策
実装方法の提案

## 代替案
検討した他の方法

## 追加情報
スクリーンショット、参考リンクなど
```

### 3.2 バグ報告テンプレート
`.github/ISSUE_TEMPLATE/bug_report.md`
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## バグの説明
何が起きているか

## 再現手順
1. '...'に移動
2. '...'をクリック
3. エラーが発生

## 期待される動作
本来どうあるべきか

## スクリーンショット
可能であれば添付

## 環境
- OS: [e.g. macOS 14.0]
- ブラウザ: [e.g. Chrome 120]
- Node.js: [e.g. 20.11.0]
```

## 4. スプリント管理

### 4.1 スプリント構成
- **期間**: 1週間
- **開始日**: 月曜日
- **終了日**: 金曜日
- **振り返り**: 金曜日午後

### 4.2 スプリント計画
```markdown
# Sprint [番号] - [開始日]～[終了日]

## スプリントゴール
今週達成すべき主要目標

## タスク一覧
- [ ] #123 商品名検索APIの実装
- [ ] #124 検索結果のキャッシング
- [ ] #125 単体テストの追加

## 成功指標
- API応答時間2秒以内
- テストカバレッジ80%以上
```

## 5. 自動化設定

### 5.1 GitHub Actions
`.github/workflows/project-automation.yml`
```yaml
name: Project Automation

on:
  issues:
    types: [opened, closed]
  pull_request:
    types: [opened, closed, ready_for_review]

jobs:
  project-board:
    runs-on: ubuntu-latest
    steps:
      - name: Add to project
        uses: actions/add-to-project@v0.5.0
        with:
          project-url: https://github.com/users/USERNAME/projects/1
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 5.2 自動ラベリング
`.github/labeler.yml`
```yaml
search-engine:
  - src/search/**/*
  - src/jan/**/*

platform-adapter:
  - src/platforms/**/*
  - src/collectors/**/*

frontend:
  - src/app/**/*
  - src/components/**/*

documentation:
  - docs/**/*
  - '**/*.md'
```

## 6. 進捗追跡

### 6.1 週次レポート
```markdown
# 週次進捗レポート - Week [番号]

## 完了タスク
- ✅ 商品名検索の基本実装
- ✅ eBay APIの最適化

## 進行中タスク
- 🔄 画像アップロード機能
- 🔄 メルカリスクレイピング改善

## 次週の計画
- 📋 自然言語検索の設計
- 📋 ヤフオク統合の開始

## 課題・リスク
- ⚠️ API制限への対策が必要
- ⚠️ テストカバレッジが目標未達

## メトリクス
- 完了タスク: 8/10
- コードカバレッジ: 75%
- API応答時間: 平均1.8秒
```

## 7. コミュニケーション

### 7.1 定例会議
- **デイリースタンドアップ**: 毎日10:00（15分）
- **スプリント計画**: 月曜日14:00（1時間）
- **スプリント振り返り**: 金曜日16:00（30分）

### 7.2 Slack/Discord設定
```
#general - 一般的な連絡
#dev-search - 検索機能開発
#dev-platform - プラットフォーム統合
#ci-cd - ビルド・デプロイ通知
#random - 雑談
```

## 8. 次のステップ

1. **即座に実行**
   ```bash
   # GitHubプロジェクトボードの作成
   gh project create --title "Buy Records Development" --owner @me
   
   # イシューテンプレートの追加
   mkdir -p .github/ISSUE_TEMPLATE
   # 上記テンプレートをコピー
   ```

2. **今週中に完了**
   - マイルストーンの設定
   - 最初のスプリント計画
   - チームメンバーへの説明会

3. **継続的な改善**
   - 週次でプロセスの見直し
   - メトリクスに基づく調整
   - チームフィードバックの反映