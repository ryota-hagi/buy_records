import { NextRequest, NextResponse } from 'next/server';
import { YodobashiScraper } from '@/collectors/yodobashi';

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

    console.log(`ヨドバシ検索開始: ${searchQuery}`);

    const scraper = new YodobashiScraper();

    try {
      // ヨドバシで検索実行（リトライロジック付き）
      let searchResult = null;
      let lastError = null;
      const maxRetries = 3;

      for (let i = 0; i < maxRetries; i++) {
        try {
          searchResult = await scraper.search(searchQuery, limit);
          if (searchResult.success && searchResult.results.length > 0) {
            break; // 成功したらループを抜ける
          }
        } catch (error) {
          lastError = error;
          console.log(`ヨドバシ検索リトライ ${i + 1}/${maxRetries}`);
          if (i < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, 2000)); // 2秒待機
          }
        }
      }

      if (!searchResult || (!searchResult.success && lastError)) {
        throw lastError || new Error('検索に失敗しました');
      }

      // 結果を取得
      const results = searchResult.results || [];

      console.log(`ヨドバシ検索完了: ${results.length}件`);

      return NextResponse.json({
        success: true,
        query: searchQuery,
        results: results,
        total_results: searchResult.metadata?.total_results || results.length,
        data_source: 'yodobashi_scraper',
        scraping_method: 'api',
        timestamp: new Date().toISOString()
      });

    } catch (scraperError) {
      console.error('ヨドバシスクレイピングエラー:', scraperError);
      
      // エラーでも空の結果を返す（他のプラットフォームの検索を止めない）
      return NextResponse.json({
        success: false,
        query: searchQuery,
        results: [],
        total_results: 0,
        error: scraperError instanceof Error ? scraperError.message : 'スクレイピングエラー',
        data_source: 'yodobashi_scraper',
        scraping_method: 'beautifulsoup',
        timestamp: new Date().toISOString()
      });
    }

  } catch (error) {
    console.error('ヨドバシ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'ヨドバシ検索中にエラーが発生しました',
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
    console.error('ヨドバシ検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'ヨドバシ検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        results: []
      },
      { status: 500 }
    );
  }
}