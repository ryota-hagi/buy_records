import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query');
    const productName = searchParams.get('product_name');
    const janCode = searchParams.get('jan_code');
    const limit = parseInt(searchParams.get('limit') || '20');

    // 検索クエリの優先順位
    const searchQuery = query || productName || janCode;
    
    if (!searchQuery) {
      return NextResponse.json(
        { error: 'query, product_name, またはjan_codeが必要です' },
        { status: 400 }
      );
    }

    console.log(`ラクマ検索開始: ${searchQuery}`);

    // Pythonスクリプトを実行
    const pythonScript = path.join(process.cwd(), 'scripts', 'search_rakuma_selenium.py');
    
    return new Promise((resolve) => {
      const pythonProcess = spawn('python3', [pythonScript, searchQuery, limit.toString()], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });
      
      // タイムアウト処理（30秒）
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        console.error('ラクマ検索タイムアウト（30秒）');
        resolve(NextResponse.json({
          success: false,
          query: searchQuery,
          results: [],
          total_results: 0,
          error: 'タイムアウト（30秒）',
          data_source: 'rakuma_selenium',
          scraping_method: 'selenium',
          timestamp: new Date().toISOString()
        }));
      }, 30000);
      
      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        console.log(`ラクマ検索プロセス終了: code=${code}`);
        
        if (code === 0) {
          try {
            // JSON_STARTとJSON_ENDマーカーを探してJSONを抽出
            const jsonStartIndex = output.indexOf('JSON_START');
            const jsonEndIndex = output.indexOf('JSON_END');
            
            if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
              const jsonStr = output.substring(jsonStartIndex + 'JSON_START'.length, jsonEndIndex).trim();
              const parsed = JSON.parse(jsonStr);
              const results = Array.isArray(parsed) ? parsed : (parsed.results || []);
              
              console.log(`ラクマ検索完了: ${results.length}件`);
              
              resolve(NextResponse.json({
                success: true,
                query: searchQuery,
                results: results.slice(0, limit),
                total_results: results.length,
                data_source: 'rakuma_selenium',
                scraping_method: 'selenium',
                timestamp: new Date().toISOString()
              }));
            } else {
              console.error('ラクマ検索: JSONマーカーが見つかりません');
              resolve(NextResponse.json({
                success: false,
                query: searchQuery,
                results: [],
                total_results: 0,
                error: 'データ解析エラー',
                data_source: 'rakuma_selenium',
                scraping_method: 'selenium',
                timestamp: new Date().toISOString()
              }));
            }
          } catch (parseError) {
            console.error('ラクマ検索結果解析エラー:', parseError);
            resolve(NextResponse.json({
              success: false,
              query: searchQuery,
              results: [],
              total_results: 0,
              error: 'JSON解析エラー',
              data_source: 'rakuma_selenium',
              scraping_method: 'selenium',
              timestamp: new Date().toISOString()
            }));
          }
        } else {
          console.error(`ラクマ検索エラー:`, errorOutput);
          resolve(NextResponse.json({
            success: false,
            query: searchQuery,
            results: [],
            total_results: 0,
            error: errorOutput || 'プロセスエラー',
            data_source: 'rakuma_selenium',
            scraping_method: 'selenium',
            timestamp: new Date().toISOString()
          }));
        }
      });
      
      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.error('ラクマ検索プロセスエラー:', error);
        resolve(NextResponse.json({
          success: false,
          query: searchQuery,
          results: [],
          total_results: 0,
          error: 'プロセス起動エラー',
          data_source: 'rakuma_selenium',
          scraping_method: 'selenium',
          timestamp: new Date().toISOString()
        }));
      });
    });

  } catch (error) {
    console.error('ラクマ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'ラクマ検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        results: []
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, product_name, jan_code, limit = 20 } = body;
    
    // URLSearchParamsを作成してGETハンドラーに渡す
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (product_name) params.append('product_name', product_name);
    if (jan_code) params.append('jan_code', jan_code);
    params.append('limit', limit.toString());
    
    // GETハンドラーを再利用
    const url = new URL(request.url);
    url.search = params.toString();
    const getRequest = new NextRequest(url);
    
    return GET(getRequest);
  } catch (error) {
    console.error('ラクマ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'ラクマ検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        results: []
      },
      { status: 500 }
    );
  }
}