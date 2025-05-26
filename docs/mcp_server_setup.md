# MCP (Model Context Protocol) サーバー設定ガイド

## GitHub MCP サーバー

GitHub MCP サーバーを使用すると、Claude DesktopからGitHubリポジトリに直接アクセスできます。

### インストール

```bash
npm install -g @modelcontextprotocol/server-github
```

### 設定

1. **GitHub Personal Access Tokenの作成**
   - https://github.com/settings/tokens/new にアクセス
   - 以下の権限を選択：
     - `repo` - プライベートリポジトリへのフルアクセス
     - `read:org` - 組織情報の読み取り
     - `read:user` - ユーザープロファイルの読み取り
   - トークンをコピー

2. **Claude Desktop設定ファイルの編集**
   
   ファイル: `~/Library/Application Support/Claude/claude_desktop_config.json`
   
   ```json
   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "your-github-token-here"
         }
       }
     }
   }
   ```

3. **Claude Desktopを再起動**

### 使用方法

Claude Desktop内で以下のようなコマンドが使用できます：

- リポジトリの作成
- イシューの作成・管理
- プルリクエストの作成
- コードの検索
- ファイルの読み取り

### トラブルシューティング

- トークンが正しく設定されているか確認
- Claude Desktopのログを確認: `~/Library/Logs/Claude/`
- NPMパッケージが正しくインストールされているか確認: `npm list -g @modelcontextprotocol/server-github`

## Context7 MCP サーバー

Context7は、OpenAI Vision APIを使用した視覚的な操作を可能にするMCPサーバーです。

### 設定

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

### 使用例

- Webページのスクリーンショット取得
- 画像の解析
- 視覚的なスクレイピング