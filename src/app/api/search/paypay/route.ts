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

    console.log(`PayPayフリマ検索開始: ${searchQuery}`);

    // Pythonスクリプトを使用してPayPayフリマ検索を実行
    const pythonScript = path.join(process.cwd(), 'scripts', 'search', 'search_paypay_selenium.py');
    
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python3', [pythonScript, searchQuery, limit.toString()], {
        env: { ...process.env },
        timeout: 120000 // 120秒のタイムアウト
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
        if (code !== 0) {
          console.error(`PayPayフリマ検索エラー: ${errorOutput}`);
          resolve(NextResponse.json({
            success: false,
            error: 'PayPayフリマ検索中にエラーが発生しました',
            details: errorOutput,
            results: []
          }, { status: 500 }));
          return;
        }
        
        try {
          // Clean output by extracting only JSON part
          const jsonMatch = output.match(/\[[\s\S]*\]/);
          if (!jsonMatch) {
            console.log('PayPayフリマ: No JSON found in output');
            resolve(NextResponse.json({
              success: true,
              platform: 'paypay',
              query: searchQuery,
              results: [],
              total_results: 0,
              data_source: 'paypay_selenium',
              scraping_method: 'selenium',
              timestamp: new Date().toISOString()
            }));
            return;
          }
          
          const results = JSON.parse(jsonMatch[0]);
          console.log(`PayPayフリマ検索完了: ${results.length}件`);
          
          // Transform results to standard format
          const standardResults = results.map((item: any) => ({
            platform: 'paypay',
            title: item.item_title || item.title || '',
            price: item.price || 0,
            url: item.item_url || item.url || '',
            image_url: item.item_image_url || item.image_url || '',
            shipping_fee: item.shipping_cost || 0,
            total_price: item.total_price || item.price || 0,
            condition: item.condition || '中古',
            store_name: item.seller || 'PayPayフリマ出品者',
            location: 'Japan',
            currency: 'JPY'
          }));
          
          resolve(NextResponse.json({
            success: true,
            platform: 'paypay',
            query: searchQuery,
            results: standardResults.slice(0, limit),
            total_results: standardResults.length,
            data_source: 'paypay_selenium',
            scraping_method: 'selenium',
            timestamp: new Date().toISOString()
          }));
        } catch (parseError) {
          console.error('PayPayフリマ結果パースエラー:', parseError);
          console.error('Output was:', output);
          resolve(NextResponse.json({
            success: false,
            error: 'PayPayフリマ検索結果の解析に失敗しました',
            details: parseError.message,
            results: []
          }, { status: 500 }));
        }
      });
      
      pythonProcess.on('error', (error) => {
        console.error('PayPayフリマPythonプロセスエラー:', error);
        resolve(NextResponse.json({
          success: false,
          error: 'PayPayフリマ検索プロセスの起動に失敗しました',
          details: error.message,
          results: []
        }, { status: 500 }));
      });
    });

  } catch (error) {
    console.error('PayPayフリマ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'PayPayフリマ検索中にエラーが発生しました',
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
    console.error('PayPayフリマ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'PayPayフリマ検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        results: []
      },
      { status: 500 }
    );
  }
}