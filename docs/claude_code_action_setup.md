# Claude Code Action セットアップガイド

## 概要
Claude Code ActionはGitHub上でイシューやコメントに対してClaude AIが自動的に応答・作業を行うGitHub Actionです。

## セットアップ手順

### 1. ワークフローファイルの作成
`.github/workflows/claude.yml` ファイルを作成済み

### 2. ANTHROPIC_API_KEY の設定
GitHubリポジトリでシークレットを設定する必要があります：

1. GitHubリポジトリページへアクセス: https://github.com/ryota-hagi/buy_records
2. Settings → Secrets and variables → Actions
3. "New repository secret" をクリック
4. 以下を入力：
   - Name: `ANTHROPIC_API_KEY`
   - Secret: Anthropic APIキー
5. "Add secret" をクリック

### 3. 使い方
- イシューを作成すると、Claude Code Actionが自動的に反応
- イシューにコメントすると、Claudeが応答
- コードの修正やドキュメントの更新などを自動実行

### トリガーイベント
- `issue_comment.created`: イシューにコメントが追加されたとき
- `issues.opened`: 新しいイシューが作成されたとき
- `issues.edited`: イシューが編集されたとき

### 注意事項
- APIキーは必ずGitHub Secretsに保存（直接コードに含めない）
- アクションの実行にはGitHub Actionsの使用時間が消費される
- Anthropic APIの使用料金が発生する可能性がある