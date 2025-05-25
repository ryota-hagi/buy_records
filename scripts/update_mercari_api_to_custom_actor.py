#!/usr/bin/env python3
"""
Mercari APIルートをカスタムActorを使用するように更新
"""

import os
import re

def update_mercari_route():
    """Mercari APIルートファイルを更新"""
    route_file = "src/app/api/search/mercari/route.ts"
    
    if not os.path.exists(route_file):
        print(f"❌ ファイルが見つかりません: {route_file}")
        return False
    
    # 現在のファイル内容を読み取り
    with open(route_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新しいコンテンツを作成（カスタムActorを使用）
    new_content = '''import { NextRequest, NextResponse } from 'next/server';
import { ApifyApi } from 'apify-client';

async function handleMercariSearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20): Promise<any> {
  // 検索クエリを構築
  let searchQuery = '';
  if (productName) {
    searchQuery = productName;
  } else if (janCode) {
    searchQuery = janCode;
  } else if (query) {
    searchQuery = query;
  } else {
    throw new Error('検索パラメータが不足しています');
  }

  console.log(`Mercari カスタムActor検索開始: ${searchQuery}`);

  // カスタムApify Actorを呼び出し
  const client = new ApifyApi({
    token: process.env.APIFY_API_TOKEN,
  });

  const input = {
    searchKeyword: searchQuery,
    maxItems: Math.min(limit, 50),
    includeImages: true,
    includeDescription: false
  };

  try {
    // カスタムActorを実行（YOUR_USERNAMEは実際のユーザー名に置き換える必要があります）
    const run = await client.actor('YOUR_USERNAME/mercari-scraper').call(input, {
      timeout: 120000, // 2分のタイムアウト
    });

    // 結果を取得
    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    
    console.log(`Mercari カスタムActor検索完了: ${items.length}件`);
    
    return {
      success: true,
      platform: 'mercari',
      query: searchQuery,
      total_results: items.length,
      results: items,
      timestamp: new Date().toISOString(),
      data_source: 'custom_apify_actor'
    };

  } catch (error) {
    console.error('Mercari カスタムActor エラー:', error);
    
    // フォールバック: 既存のSeleniumスクレイピングを使用
    console.log('フォールバック: Seleniumスクレイピングを実行');
    
    const { spawn } = require('child_process');
    const path = require('path');
    
    return new Promise((resolve, reject) => {
      const pythonScript = path.join(process.cwd(), 'scripts', 'search_mercari_scraping.py');
      const pythonProcess = spawn('python', [pythonScript, searchQuery, limit.toString()]);
      
      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const results = JSON.parse(output);
            resolve({
              success: true,
              platform: 'mercari',
              query: searchQuery,
              total_results: results.length,
              results: results,
              timestamp: new Date().toISOString(),
              data_source: 'selenium_fallback'
            });
          } catch (e) {
            reject(new Error('Mercari検索結果の解析に失敗しました'));
          }
        } else {
          reject(new Error(`Mercari検索に失敗しました: ${errorOutput}`));
        }
      });
    });
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const productName = searchParams.get('product_name');
    const janCode = searchParams.get('jan_code');
    const query = searchParams.get('query');
    const limit = parseInt(searchParams.get('limit') || '20');
    
    if (!productName && !janCode && !query) {
      return NextResponse.json(
        { error: 'product_name、jan_code、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await handleMercariSearch(productName, janCode, query, limit);
    console.log(`Mercari検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Mercari検索エラー:', error);
    
    let errorMessage = 'Mercari検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'mercari',
        details: details,
        suggestion: 'しばらく時間をおいて再試行してください'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_name, jan_code, query, limit = 20 } = body;
    
    if (!product_name && !jan_code && !query) {
      return NextResponse.json(
        { error: 'product_name、jan_code、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await handleMercariSearch(product_name, jan_code, query, limit);
    console.log(`Mercari検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Mercari検索エラー:', error);
    
    let errorMessage = 'Mercari検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'mercari',
        details: details,
        suggestion: 'しばらく時間をおいて再試行してください'
      },
      { status: 500 }
    );
  }
}
'''
    
    # ファイルを更新
    with open(route_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {route_file} を更新しました")
    print("⚠️  注意: 'YOUR_USERNAME/mercari-scraper' を実際のActor名に置き換えてください")
    return True

def main():
    print("=== Mercari APIルート更新スクリプト ===")
    
    if update_mercari_route():
        print("\n🎉 更新完了！")
        print("\n次のステップ:")
        print("1. Apify Consoleでアクター名を確認")
        print("2. src/app/api/search/mercari/route.ts の 'YOUR_USERNAME/mercari-scraper' を実際の名前に置き換え")
        print("3. apify-client パッケージをインストール: npm install apify-client")
        print("4. テスト実行")
    else:
        print("❌ 更新に失敗しました")

if __name__ == "__main__":
    main()
