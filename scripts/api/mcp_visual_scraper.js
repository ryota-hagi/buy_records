#!/usr/bin/env node
/**
 * MCPサーバーを使用した視覚スクレイピング実装例
 * Puppeteer MCPサーバーを利用してブラウザ自動化を行う
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

async function createMCPClient(serverCommand, serverArgs) {
  const transport = new StdioClientTransport({
    command: serverCommand,
    args: serverArgs,
  });

  const client = new Client({
    name: 'buy-records-client',
    version: '1.0.0',
  }, {
    capabilities: {}
  });

  await client.connect(transport);
  return client;
}

async function searchMercariWithMCP(query, limit = 20) {
  try {
    // Puppeteer MCPサーバーに接続
    const client = await createMCPClient('npx', [
      '-y',
      '@modelcontextprotocol/server-puppeteer'
    ]);

    // 利用可能なツールを確認
    const tools = await client.listTools();
    console.log('利用可能なツール:', tools);

    // ブラウザを起動してページに移動
    const navigateResult = await client.callTool('puppeteer_navigate', {
      url: `https://jp.mercari.com/search?keyword=${encodeURIComponent(query)}&status=on_sale&sort=price&order=asc`
    });

    // スクリーンショットを撮影
    const screenshotResult = await client.callTool('puppeteer_screenshot', {
      fullPage: false
    });

    // ページ内容を取得
    const contentResult = await client.callTool('puppeteer_evaluate', {
      script: `
        // 商品要素を探す
        const items = [];
        const thumbnails = document.querySelectorAll('mer-item-thumbnail');
        
        thumbnails.forEach((thumb, index) => {
          if (index >= ${limit}) return;
          
          const ariaLabel = thumb.getAttribute('aria-label') || '';
          const id = thumb.getAttribute('id') || '';
          
          // aria-labelから情報を抽出
          const titleMatch = ariaLabel.match(/^(.*?)の画像/);
          const priceMatch = ariaLabel.match(/(\\d+(?:,\\d+)*)円/);
          
          if (titleMatch && priceMatch) {
            items.push({
              id: id,
              title: titleMatch[1],
              price: parseInt(priceMatch[1].replace(/,/g, '')),
              url: 'https://jp.mercari.com/item/' + id
            });
          }
        });
        
        return items;
      `
    });

    await client.disconnect();

    return {
      success: true,
      results: contentResult.result || [],
      screenshot: screenshotResult.screenshot,
      method: 'mcp_puppeteer'
    };

  } catch (error) {
    console.error('MCPエラー:', error);
    return {
      success: false,
      results: [],
      error: error.message
    };
  }
}

// メイン処理
async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node mcp_visual_scraper.js <query> [limit]');
    process.exit(1);
  }

  const query = args[0];
  const limit = parseInt(args[1]) || 20;

  console.log(`Searching Mercari for: ${query}`);
  const result = await searchMercariWithMCP(query, limit);
  
  console.log(JSON.stringify(result, null, 2));
}

// エラーハンドリング
process.on('unhandledRejection', (error) => {
  console.error('Unhandled rejection:', error);
  process.exit(1);
});

main();