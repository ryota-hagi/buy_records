import { NextRequest, NextResponse } from 'next/server';
import { PayPaySeleniumScraper } from '@/collectors/paypay_selenium';

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

    // Seleniumサーバーの設定
    const seleniumUrl = process.env.SELENIUM_HUB_URL || 'http://localhost:5001';
    const scraper = new PayPaySeleniumScraper(seleniumUrl);

    try {
      // PayPayフリマで検索実行
      const results = await scraper.search(searchQuery);

      // 結果を制限数まで取得
      const limitedResults = results.slice(0, limit);

      console.log(`PayPayフリマ検索完了: ${limitedResults.length}件`);

      return NextResponse.json({
        success: true,
        query: searchQuery,
        results: limitedResults,
        total_results: results.length,
        data_source: 'paypay_selenium',
        scraping_method: 'selenium',
        timestamp: new Date().toISOString()
      });

    } catch (scraperError) {
      console.error('PayPayフリマスクレイピングエラー:', scraperError);
      
      // エラーでも空の結果を返す（他のプラットフォームの検索を止めない）
      return NextResponse.json({
        success: false,
        query: searchQuery,
        results: [],
        total_results: 0,
        error: scraperError instanceof Error ? scraperError.message : 'スクレイピングエラー',
        data_source: 'paypay_selenium',
        scraping_method: 'selenium',
        timestamp: new Date().toISOString()
      });
    }

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