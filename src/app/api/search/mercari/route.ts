import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

async function searchMercariReliable(searchQuery: string, limit: number = 20): Promise<any> {
  return new Promise((resolve, reject) => {
    console.log(`メルカリSelenium検索開始: ${searchQuery}`);
    
    const pythonScript = path.join(process.cwd(), 'scripts', 'search_mercari_selenium_standalone.py');
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
          // JSON_STARTとJSON_ENDマーカーを探してJSONを抽出
          const jsonStartIndex = output.indexOf('JSON_START');
          const jsonEndIndex = output.indexOf('JSON_END');
          
          if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
            const jsonStr = output.substring(jsonStartIndex + 'JSON_START'.length, jsonEndIndex).trim();
            const results = JSON.parse(jsonStr);
            console.log(`メルカリ確実検索成功: ${results.length}件取得`);
            resolve(results);
          } else {
            console.error('メルカリ確実検索: JSONマーカーが見つかりません');
            console.error('出力:', output);
            console.error('エラー出力:', errorOutput);
            resolve([]);
          }
        } catch (parseError) {
          console.error('メルカリ確実検索結果解析エラー:', parseError);
          console.error('出力:', output);
          console.error('エラー出力:', errorOutput);
          resolve([]);
        }
      } else {
        console.error(`メルカリ確実検索エラー (code ${code}):`, errorOutput);
        resolve([]);
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('メルカリ確実検索プロセスエラー:', error);
      resolve([]);
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
    const scrapingResults = await searchMercariReliable(searchQuery, limit);
    
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
        data_source: 'web_scraping'
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
        warning: 'メルカリから検索結果を取得できませんでした'
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
      error: error instanceof Error ? error.message : '不明なエラー'
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
