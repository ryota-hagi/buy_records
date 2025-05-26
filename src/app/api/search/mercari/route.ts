import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

async function searchMercariReliable(searchQuery: string, limit: number = 20): Promise<any> {
  return new Promise((resolve, reject) => {
    console.log(`メルカリSelenium検索開始: ${searchQuery}`);
    
    // DOM解析を優先的に使用（確実性重視）
    const domScript = path.join(process.cwd(), 'scripts', 'search_mercari_dom.py');
    const optimizedScript = path.join(process.cwd(), 'scripts', 'search_mercari_visual_optimized.py');
    const visualScript = path.join(process.cwd(), 'scripts', 'search_mercari_visual_integrated.py');
    const fallbackScript = path.join(process.cwd(), 'scripts', 'search_mercari_final.py');
    
    // 優先順位: DOM解析 > 最適化版 > 通常版 > フォールバック
    let pythonScript = domScript;
    
    const fs = require('fs');
    if (!fs.existsSync(domScript)) {
      console.log('DOM解析が見つかりません。視覚スクレイピングを使用します。');
      pythonScript = optimizedScript;
      
      if (!fs.existsSync(optimizedScript)) {
        console.log('最適化版が見つかりません。通常の視覚スクレイピングを使用します。');
        pythonScript = visualScript;
        
        if (!fs.existsSync(visualScript)) {
          console.log('視覚スクレイピングスクリプトが見つかりません。フォールバックを使用します。');
          pythonScript = fallbackScript;
        }
      }
    } else {
      console.log('DOM解析（確実性重視）を使用します。');
    }
    // タイムアウトを延長し、環境変数を設定
    const pythonProcess = spawn('python3', [pythonScript, searchQuery, limit.toString()], {
      env: { ...process.env },
      timeout: 60000 // 60秒のタイムアウト
    });
    
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
          // JSON_STARTとJSON_ENDマーカーを探してJSONを抽出
          // stdoutとstderrの両方をチェック
          let jsonStartIndex = output.indexOf('JSON_START');
          let jsonEndIndex = output.indexOf('JSON_END');
          let jsonSource = output;
          
          if (jsonStartIndex === -1 || jsonEndIndex === -1) {
            // stdoutに見つからない場合はstderrもチェック
            jsonStartIndex = errorOutput.indexOf('JSON_START');
            jsonEndIndex = errorOutput.indexOf('JSON_END');
            jsonSource = errorOutput;
          }
          
          if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
            const jsonStr = jsonSource.substring(jsonStartIndex + 'JSON_START'.length, jsonEndIndex).trim();
            const parsed = JSON.parse(jsonStr);
            console.log(`メルカリ確実検索成功: ${parsed.results?.length || 0}件取得`);
            
            // メタデータを含めて返す
            resolve({
              results: parsed.results || [],
              metadata: parsed.metadata || null,
              method: parsed.method || 'unknown'
            });
          } else {
            console.error('メルカリ確実検索: JSONマーカーが見つかりません');
            console.error('出力:', output);
            console.error('エラー出力:', errorOutput);
            resolve({ results: [], metadata: null, method: 'error' });
          }
        } catch (parseError) {
          console.error('メルカリ確実検索結果解析エラー:', parseError);
          console.error('出力:', output);
          console.error('エラー出力:', errorOutput);
          resolve({ results: [], metadata: null, method: 'error' });
        }
      } else {
        console.error(`メルカリ確実検索エラー (code ${code}):`, errorOutput);
        resolve({ results: [], metadata: null, method: 'error' });
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('メルカリ確実検索プロセスエラー:', error);
      resolve({ results: [], metadata: null, method: 'error' });
    });
  });
}

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

  console.log(`メルカリ検索開始: ${searchQuery}`);

  try {
    // 確実検索で検索実行
    const scrapingResponse = await searchMercariReliable(searchQuery, limit);
    const scrapingResults = scrapingResponse.results || [];
    const metadata = scrapingResponse.metadata || null;
    const method = scrapingResponse.method || 'unknown';
    
    if (scrapingResults && scrapingResults.length > 0) {
      // レスポンス形式を統一
      const formattedResults = scrapingResults.map((item: any) => ({
        platform: 'mercari',
        title: item.title || '',
        url: item.url || '',
        image_url: item.image_url || '',
        price: item.price || 0,
        shipping_fee: 0, // メルカリは送料込みが多い
        total_price: item.price || 0,
        condition: item.condition || '中古',
        store_name: 'メルカリ',
        location: '日本',
        currency: 'JPY',
        // 旧形式との互換性
        item_title: item.title || '',
        item_url: item.url || '',
        item_image_url: item.image_url || '',
        base_price: item.price || 0,
        item_condition: item.condition || '中古',
        seller_name: 'メルカリ'
      }));

      console.log(`メルカリ検索完了: ${formattedResults.length}件`);
      
      return {
        success: true,
        platform: 'mercari',
        query: searchQuery,
        total_results: formattedResults.length,
        results: formattedResults,
        timestamp: new Date().toISOString(),
        data_source: method === 'visual_ai_optimized' ? 'visual_ai_gpt4o_mini' : 'web_scraping',
        metadata: metadata,
        scraping_method: method
      };
    } else {
      console.log('メルカリ検索結果が空です');
      return {
        success: true,
        platform: 'mercari',
        query: searchQuery,
        total_results: 0,
        results: [],
        timestamp: new Date().toISOString(),
        data_source: 'web_scraping_empty',
        warning: 'メルカリから検索結果を取得できませんでした',
        metadata: metadata,
        scraping_method: method
      };
    }

  } catch (error) {
    console.error('メルカリ検索エラー:', error);
    
    // エラーの場合も空の結果を返す（システム全体の安定性を保つ）
    return {
      success: true,
      platform: 'mercari',
      query: searchQuery,
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'scraping_error',
      warning: 'メルカリ検索中にエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー',
      metadata: null,
      scraping_method: 'error'
    };
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
    return NextResponse.json(response);

  } catch (error) {
    console.error('メルカリ検索エラー:', error);
    
    // エラーの場合も空の結果を返す（システム全体の安定性を保つ）
    return NextResponse.json({
      success: true,
      platform: 'mercari',
      query: 'unknown',
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'error_fallback',
      warning: 'システムエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー'
    });
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
    return NextResponse.json(response);

  } catch (error) {
    console.error('メルカリ検索エラー:', error);
    
    // エラーの場合も空の結果を返す
    return NextResponse.json({
      success: true,
      platform: 'mercari',
      query: 'unknown',
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'error_fallback',
      warning: 'システムエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー'
    });
  }
}
