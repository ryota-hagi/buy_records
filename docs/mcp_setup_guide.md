# MCP (Model Context Protocol) サーバー設定ガイド

## MCPとは
MCP（Model Context Protocol）は、AIアシスタントが外部ツールやサービスと安全に連携するためのプロトコルです。

## 利用可能なMCPサーバー

### 1. データベース関連
- **SQLite MCP**: SQLiteデータベースへの直接アクセス
- **PostgreSQL MCP**: PostgreSQLデータベースの操作
- **Supabase MCP**: Supabaseデータベースとの連携

### 2. ファイルシステム
- **Filesystem MCP**: ローカルファイルの読み書き（セキュアな範囲で）

### 3. Web関連
- **Fetch MCP**: Webページの取得と解析
- **Puppeteer MCP**: ブラウザ自動化（スクレイピング向け）

### 4. 開発ツール
- **Git MCP**: Gitリポジトリの操作
- **GitHub MCP**: GitHub APIとの連携

## 設定方法

### 1. Claude Desktop アプリでの設定

```bash
# Claude設定ディレクトリを作成
mkdir -p ~/.config/claude

# MCP設定ファイルを作成
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/hagiryouta/my-claude-project/buy_records"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-supabase"],
      "env": {
        "SUPABASE_URL": "https://ggvuuixcswldxfeygxvy.supabase.co",
        "SUPABASE_SERVICE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdndnV1aXhjc3dsZHhmZXlneHZ5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzMxNzEzMCwiZXhwIjoyMDYyODkzMTMwfQ.fkFZinlf1e8YTM8QDlzFap0dOmh_lIH3ma8n1cLANrQ"
      }
    }
  }
}
EOF
```

### 2. カスタムMCPサーバーの作成

buy_recordsプロジェクト専用のMCPサーバーを作成できます：

```javascript
// mcp-server-buy-records/index.js
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: 'buy-records-mcp',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {},
  },
});

// ツールの定義
server.setRequestHandler('tools/list', async () => ({
  tools: [
    {
      name: 'search_all_platforms',
      description: 'Search products across eBay, Mercari, and Yahoo Shopping',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
          janCode: { type: 'string', description: 'JAN code' },
          limit: { type: 'number', description: 'Maximum results' }
        }
      }
    },
    {
      name: 'visual_scrape_mercari',
      description: 'Perform visual scraping on Mercari',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
          useAI: { type: 'boolean', description: 'Use AI vision' }
        }
      }
    }
  ]
}));

// サーバー起動
const transport = new StdioServerTransport();
await server.connect(transport);
```

## 推奨MCPサーバー構成

buy_recordsプロジェクトには以下のMCPサーバーが推奨されます：

1. **Supabase MCP**: 商品データベースへのアクセス
2. **Fetch MCP**: Webスクレイピング用
3. **Filesystem MCP**: スクリーンショット管理
4. **カスタムMCP**: プロジェクト固有の機能

## セキュリティ考慮事項

- MCPサーバーは指定されたディレクトリ/リソースのみアクセス可能
- 環境変数は設定ファイルで管理
- 本番環境のクレデンシャルは別途管理

## トラブルシューティング

### MCPサーバーが認識されない場合
1. Claude Desktopアプリを再起動
2. 設定ファイルのJSON構文を確認
3. npmパッケージがインストール可能か確認

### 接続エラーの場合
1. ネットワーク接続を確認
2. ファイアウォール設定を確認
3. MCPサーバーのログを確認