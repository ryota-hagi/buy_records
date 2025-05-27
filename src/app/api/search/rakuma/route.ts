import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { RakumaAdapter } from '@/platforms/adapters/rakuma-adapter';

async function searchRakuma(searchQuery: string, limit: number = 20): Promise<any> {
  return new Promise((resolve, reject) => {
    console.log(`ラクマ検索開始: ${searchQuery}`);
    
    const rakumaScript = path.join(process.cwd(), 'src', 'collectors', 'rakuma.py');
    
    // Python3でスクリプトを実行
    const pythonProcess = spawn('python3', [rakumaScript, searchQuery, limit.toString()], {
      env: { ...process.env },
      timeout: 30000 // 30秒のタイムアウト
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
          const jsonStartIndex = output.indexOf('JSON_START');
          const jsonEndIndex = output.indexOf('JSON_END');
          
          if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
            const jsonStr = output.substring(jsonStartIndex + 'JSON_START'.length, jsonEndIndex).trim();
            const parsed = JSON.parse(jsonStr);
            console.log(`ラクマ検索成功: ${parsed.results?.length || 0}件取得`);
            
            resolve({
              results: parsed.results || [],
              metadata: parsed.metadata || null,
              method: parsed.method || 'dom_parsing'
            });
          } else {
            console.error('ラクマ検索: JSONマーカーが見つかりません');
            console.error('出力:', output);
            console.error('エラー出力:', errorOutput);
            resolve({ results: [], metadata: null, method: 'error' });
          }
        } catch (parseError) {
          console.error('ラクマ検索結果解析エラー:', parseError);
          console.error('出力:', output);
          console.error('エラー出力:', errorOutput);
          resolve({ results: [], metadata: null, method: 'error' });
        }
      } else {
        console.error(`ラクマ検索エラー (code ${code}):`, errorOutput);
        resolve({ results: [], metadata: null, method: 'error' });
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('ラクマ検索プロセスエラー:', error);
      resolve({ results: [], metadata: null, method: 'error' });
    });
  });
}

async function handleRakumaSearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20): Promise<any> {
  // アダプターインスタンスを作成
  const adapter = new RakumaAdapter();
  
  // 検索クエリを構築
  let searchQuery = '';
  try {
    searchQuery = adapter.buildSearchQuery({ product_name: productName, jan_code: janCode, query });
  } catch (error) {
    throw new Error('検索パラメータが不足しています');
  }

  console.log(`ラクマ検索開始: ${searchQuery}`);

  try {
    // スクレイピングで検索実行
    const scrapingResponse = await searchRakuma(searchQuery, limit);
    const scrapingResults = scrapingResponse.results || [];
    const metadata = scrapingResponse.metadata || null;
    const method = scrapingResponse.method || 'unknown';
    
    if (scrapingResults && scrapingResults.length > 0) {
      // アダプターを使用してレスポンス形式を統一
      const formattedResults = scrapingResults.map((item: any) => {
        const transformed = adapter.transformResult(item);
        // 旧形式との互換性も追加
        return {
          ...transformed,
          item_title: transformed.title,
          item_url: transformed.url,
          item_image_url: transformed.image_url,
          base_price: transformed.price,
          item_condition: transformed.condition,
          seller_name: transformed.store_name
        };
      });

      console.log(`ラクマ検索完了: ${formattedResults.length}件`);
      
      return {
        success: true,
        platform: 'rakuma',
        query: searchQuery,
        total_results: formattedResults.length,
        results: formattedResults,
        timestamp: new Date().toISOString(),
        data_source: 'web_scraping',
        metadata: metadata,
        scraping_method: method
      };
    } else {
      console.log('ラクマ検索結果が空です');
      return {
        success: true,
        platform: 'rakuma',
        query: searchQuery,
        total_results: 0,
        results: [],
        timestamp: new Date().toISOString(),
        data_source: 'web_scraping_empty',
        warning: 'ラクマから検索結果を取得できませんでした',
        metadata: metadata,
        scraping_method: method
      };
    }

  } catch (error) {
    console.error('ラクマ検索エラー:', error);
    
    // エラーの場合も空の結果を返す（システム全体の安定性を保つ）
    return {
      success: true,
      platform: 'rakuma',
      query: searchQuery,
      total_results: 0,
      results: [],
      timestamp: new Date().toISOString(),
      data_source: 'scraping_error',
      warning: 'ラクマ検索中にエラーが発生しました',
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

    const response = await handleRakumaSearch(productName, janCode, query, limit);
    return NextResponse.json(response);

  } catch (error) {
    console.error('ラクマ検索エラー:', error);
    
    // エラーの場合も空の結果を返す
    return NextResponse.json({
      success: true,
      platform: 'rakuma',
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

    const response = await handleRakumaSearch(product_name, jan_code, query, limit);
    return NextResponse.json(response);

  } catch (error) {
    console.error('ラクマ検索エラー:', error);
    
    // エラーの場合も空の結果を返す
    return NextResponse.json({
      success: true,
      platform: 'rakuma',
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