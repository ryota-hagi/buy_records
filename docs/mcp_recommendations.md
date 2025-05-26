# buy_recordsプロジェクトでのMCP活用推奨事項

## 現在利用可能なMCPサーバー

現在、`context7` MCPサーバー（mcprouter）が設定されています。

## buy_recordsプロジェクトに推奨されるMCPサーバー

### 1. **Filesystem MCP Server**
- **用途**: スクリーンショット管理、ログファイル操作
- **利点**: ファイル操作が安全かつ効率的に
- **設定例**:
  ```json
  {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./screenshots"]
    }
  }
  ```

### 2. **Fetch MCP Server**
- **用途**: Webスクレイピング、API呼び出し
- **利点**: CORS制限を回避、高度なリクエスト制御
- **活用例**:
  - メルカリの商品ページ取得
  - eBay APIへのアクセス
  - Yahoo Shopping APIの呼び出し

### 3. **Puppeteer MCP Server**
- **用途**: 視覚的スクレイピング、動的コンテンツ処理
- **利点**: JavaScriptレンダリング対応、スクリーンショット撮影
- **活用例**:
  - メルカリの動的コンテンツ取得
  - 商品画像の自動ダウンロード
  - ページネーション処理

### 4. **Supabase MCP Server**
- **用途**: データベース操作
- **利点**: 直接的なDB操作、リアルタイム更新
- **活用例**:
  - 検索結果の保存
  - 価格履歴の記録
  - ユーザー設定の管理

## 実装提案

### 1. 統合検索システムの改善
```javascript
// MCPを使った統合検索
async function unifiedSearchWithMCP(query) {
  // Fetch MCPでYahoo Shopping API
  const yahooResults = await fetchMCP.call('fetch', {
    url: `https://shopping.yahooapis.jp/search?query=${query}`,
    headers: { 'Authorization': 'Bearer ...' }
  });

  // Puppeteer MCPでメルカリスクレイピング
  const mercariResults = await puppeteerMCP.call('scrape', {
    url: `https://jp.mercari.com/search?keyword=${query}`,
    waitFor: 'mer-item-thumbnail',
    extract: 'products'
  });

  // Supabase MCPで結果を保存
  await supabaseMCP.call('insert', {
    table: 'search_results',
    data: { query, results: [...yahooResults, ...mercariResults] }
  });
}
```

### 2. 視覚スクレイピングの強化
- Puppeteer MCPでブラウザ制御
- スクリーンショットの自動保存
- AI Vision APIとの連携

### 3. データ管理の効率化
- Supabase MCPでリアルタイムデータ同期
- 検索履歴の自動記録
- 価格変動の追跡

## セットアップ手順

1. **Claude Desktopの設定更新**
   ```bash
   # 設定ファイルを編集
   ~/.config/claude/claude_desktop_config.json
   ```

2. **必要なnpmパッケージのインストール**
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-fetch
   npm install -g @modelcontextprotocol/server-puppeteer
   ```

3. **環境変数の設定**
   - Supabase認証情報
   - API キー
   - その他のクレデンシャル

## 注意事項

- MCPサーバーは指定されたスコープ内でのみ動作
- セキュリティを考慮した権限設定が重要
- 本番環境では別途設定が必要

## 次のステップ

1. MCPサーバーの設定をClaude Desktopに追加
2. 各プラットフォーム用のMCPツール実装
3. 既存のPythonスクリプトをMCP対応に移行