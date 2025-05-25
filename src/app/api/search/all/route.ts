import { NextRequest, NextResponse } from 'next/server';

interface SearchResult {
  platform: string;
  title: string;
  url: string;
  image_url: string;
  price: number;
  shipping_fee?: number;
  total_price: number;
  condition: string;
  store_name: string;
  location: string;
  currency: string;
  [key: string]: any;
}

async function searchAllPlatforms(productName: string | null, janCode: string | null, query: string | null, limit: number = 20) {
  const baseUrl = process.env.NODE_ENV === 'production' 
    ? 'https://buy-records.vercel.app' 
    : 'http://localhost:3000';
  
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

  console.log(`統合検索開始: ${searchQuery}`);

  const platforms = [
    { name: 'yahoo_shopping', endpoint: '/api/search/yahoo' },
    { name: 'ebay', endpoint: '/api/search/ebay' },
    { name: 'mercari', endpoint: '/api/search/mercari' }
  ];

  const results: SearchResult[] = [];
  const errors: string[] = [];

  // 並行検索実行
  const searchPromises = platforms.map(async (platform) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      // 正しいパラメータ名を使用
      const params = new URLSearchParams();
      if (janCode) {
        params.append('jan_code', janCode);
      } else if (productName) {
        params.append('product_name', productName);
      } else if (query) {
        params.append('query', query);
      }
      params.append('limit', limit.toString());
      
      const response = await fetch(`${baseUrl}${platform.endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.results) {
          results.push(...data.results);
          console.log(`${platform.name}: ${data.results.length}件取得`);
        } else {
          errors.push(`${platform.name}: ${data.error || 'Unknown error'}`);
          console.error(`${platform.name} APIエラー:`, data.error);
        }
      } else {
        errors.push(`${platform.name}: HTTP ${response.status}`);
        console.error(`${platform.name} HTTPエラー:`, response.status);
      }
    } catch (error) {
      errors.push(`${platform.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error(`${platform.name} 検索エラー:`, error);
    }
  });

  await Promise.allSettled(searchPromises);

  // 結果を価格順でソート
  results.sort((a, b) => (a.total_price || a.price || 0) - (b.total_price || b.price || 0));

  // プラットフォーム別の結果を集計
  const platformResults: { [key: string]: SearchResult[] } = {};
  for (const result of results) {
    if (!platformResults[result.platform]) {
      platformResults[result.platform] = [];
    }
    platformResults[result.platform].push(result);
  }

  return {
    success: true,
    query: searchQuery,
    total_results: results.length,
    results: results.slice(0, limit), // 制限数まで
    platforms: platformResults, // プラットフォーム別結果
    platforms_searched: platforms.length,
    errors: errors.length > 0 ? errors : undefined,
    timestamp: new Date().toISOString()
  };
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const productName = searchParams.get('product_name');
    const janCode = searchParams.get('jan_code');
    const query = searchParams.get('query');
    const limit = parseInt(searchParams.get('limit') || '50');
    
    if (!productName && !janCode && !query) {
      return NextResponse.json(
        { error: 'product_name、jan_code、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await searchAllPlatforms(productName, janCode, query, limit);
    console.log(`統合検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('統合検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '統合検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_name, jan_code, query, limit = 50 } = body;
    
    if (!product_name && !jan_code && !query) {
      return NextResponse.json(
        { error: 'product_name、jan_code、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await searchAllPlatforms(product_name, jan_code, query, limit);
    console.log(`統合検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('統合検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '統合検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}
