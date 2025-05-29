# デプロイメントチェックリスト

**実行日時**: 2025/05/29  
**デプロイバージョン**: RM-2025-05-29-002  

## 事前準備チェックリスト

### 1. バックアップ
- [ ] 現在の本番コードのバックアップ作成
- [ ] 環境変数のバックアップ
- [ ] データベース接続情報の確認
- [ ] 前回のデプロイメントIDを記録

### 2. 環境確認
- [ ] Vercel CLIがインストール済み
- [ ] 適切な権限でログイン済み
- [ ] 本番環境のステータス確認

### 3. コード確認
- [ ] すべての修正がコミット済み
- [ ] ビルドが成功することを確認
- [ ] TypeScriptエラーがないことを確認

## デプロイ手順

### ステップ1: 事前テスト
```bash
# ローカルでのビルド確認
npm run build

# 型チェック
npm run type-check || npx tsc --noEmit

# リント
npm run lint || npx next lint
```

### ステップ2: Git操作
```bash
# 現在のブランチを確認
git status

# すべての変更をコミット
git add .
git commit -m "fix: 統合検索エンジンの複数プラットフォームエラー修正

- 楽天API: itemNameエラー修正、nullチェック追加
- ヨドバシAPI: slice エラー修正、配列チェック追加
- PayPay: JSON解析エラー修正、0件問題解決
- ラクマ: タイムアウト30秒に短縮、処理高速化
- UI: プラットフォーム別結果表示ボタン実装

Issue: RM-2025-05-29-001"

# リモートにプッシュ
git push origin main
```

### ステップ3: Vercelデプロイ
```bash
# Vercel CLIでのデプロイ（プレビュー）
vercel

# 本番デプロイ
vercel --prod
```

## デプロイ後の確認事項

### 1. 基本動作確認
- [ ] トップページが正常に表示される
- [ ] 検索フォームが動作する
- [ ] APIエンドポイントが応答する

### 2. 各プラットフォーム確認
- [ ] 楽天API: /api/search/rakuten
- [ ] ヨドバシAPI: /api/search/yodobashi
- [ ] PayPay: /api/search/paypay
- [ ] ラクマ: /api/search/rakuma
- [ ] eBay: /api/search/ebay
- [ ] メルカリ: /api/search/mercari
- [ ] Yahoo: /api/search/yahoo

### 3. 統合テスト実行
```bash
# 本番環境での統合テスト
python3 scripts/testing/test_all_platforms_integration.py production
```

## ロールバック手順

### 即時ロールバック（Vercel Dashboard）
1. Vercelダッシュボードにアクセス
2. Deploymentsタブを開く
3. 前回の安定版デプロイメントを探す
4. "..."メニューから"Promote to Production"を選択

### CLIでのロールバック
```bash
# デプロイメント一覧を確認
vercel ls

# 特定のデプロイメントにロールバック
vercel rollback [deployment-url]
```

## エラー発生時の対応

### 1. 軽微なエラー（エラー率 < 10%）
- ログを収集して原因調査
- ホットフィックスの準備
- 次回デプロイで修正

### 2. 重大なエラー（エラー率 >= 10%）
- 即座にロールバック実施
- エラーログの保存
- 原因調査と修正

### 3. 完全障害
- 緊急ロールバック
- ステータスページ更新
- 利害関係者への通知

## 監視項目

- エラー率: 5%以下を維持
- レスポンスタイム: 各API 30秒以内
- 成功率: 95%以上
- メモリ使用率: 閾値以下

## 連絡先

- 技術責任者: [連絡先]
- 緊急連絡先: [連絡先]
- エスカレーション: [連絡先]