import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

async function searchEbayBrowseApi(searchQuery: string, limit: number = 20): Promise<any> {
  return new Promise((resolve, reject) => {
    console.log(`eBay Browse API検索開始: ${searchQuery}`);
    
    const pythonScript = path.join(process.cwd(), 'scripts', 'search_ebay_browse_api.py');
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
            console.log(`eBay Browse API検索成功: ${results.length}件取得`);
            resolve(results);
          } else {
            console.error('eBay Browse API検索: JSONマーカーが見つかりません');
            console.error('出力:', output);
            console.error('エラー出力:', errorOutput);
            resolve([]);
          }
        } catch (parseError) {
          console.error('eBay Browse API検索結果解析エラー:', parseError);
          console.error('出力:', output);
          console.error('エラー出力:', errorOutput);
          resolve([]);
        }
      } else {
        console.error(`eBay Browse API検索エラー (code ${code}):`, errorOutput);
        resolve([]);
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('eBay Browse API検索プロセスエラー:', error);
      resolve([]);
    });
  });
}

async function handleEbaySearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20): Promise<any> {
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

  console.log(`eBay検索開始: ${searchQuery}`);

  try {
    // Browse APIで検索実行
    const searchResults = await searchEbayBrowseApi(searchQuery, limit);
    
    if (searchResults && searchResults.length > 0) {
      // レスポンス形式を統一
      const formattedResults = searchResults.map((item: any) => ({
        platform: 'ebay',
        title: item.title || '',
        url: item.url || '',
        image_url: item.image_url || '',
        price: item.price || 0,
        shipping_fee: item.shipping_fee || 0,
        total_price: item.total_price || item.price || 0,
        condition: item.condition || 'Used',
        store_name: item.seller || 'eBay Seller',
        location: 'United States',
        currency: 'JPY',
        exchange_rate: item.exchange_rate || 150,
        // 旧形式との互換性
        item_title: item.title || '',
        item_url: item.url || '',
        item_image_url: item.image_url || '',
        base_price: item.price || 0,
        item_condition: item.condition || 'Used',
        seller_name: item.seller || 'eBay Seller'
      }));

      console.log(`eBay検索完了: ${formattedResults.length}件`);
      
      return {
        success: true,
        platform: 'ebay',
        query: searchQuery,
        total_results: formattedResults.length,
        results: formattedResults,
        timestamp: new Date().toISOString(),
        data_source: 'browse_api',
        exchange_rate: searchResults[0]?.exchange_rate || 150
      };
    } else {
      console.log('eBay検索結果が空です');
      return {
        success: true,
        platform: 'ebay',
        query: searchQuery,
        total_results: 0,
        results: [],
        timestamp: new Date().toISOString(),
        data_source: 'browse_api_empty',
        warning: 'eBayから検索結果を取得できませんでした',
        exchange_rate: 150
      };
    }

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    // エラーの場合も空の結果を返す（システム全体の安定性を保つ）
    return {
      success: true,
      platform: 'ebay',
      query: searchQuery,
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'search_error',
      warning: 'eBay検索中にエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー',
      exchange_rate: 150
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

    const response = await handleEbaySearch(productName, janCode, query, limit);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    // エラーの場合も空の結果を返す（システム全体の安定性を保つ）
    return NextResponse.json({
      success: true,
      platform: 'ebay',
      query: 'unknown',
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'error_fallback',
      warning: 'システムエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー',
      exchange_rate: 150
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

    const response = await handleEbaySearch(product_name, jan_code, query, limit);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    // エラーの場合も空の結果を返す
    return NextResponse.json({
      success: true,
      platform: 'ebay',
      query: 'unknown',
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'error_fallback',
      warning: 'システムエラーが発生しました',
      error: error instanceof Error ? error.message : '不明なエラー',
      exchange_rate: 150
    });
  }
}
