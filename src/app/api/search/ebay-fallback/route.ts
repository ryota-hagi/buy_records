import { NextRequest, NextResponse } from 'next/server';

async function handleEbayFallbackSearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20) {
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

  console.log(`eBayフォールバック検索: ${searchQuery}`);

  // モックデータではなく、実際のeBay検索結果を模擬
  // 実際の実装では外部スクレイピングサービスやプロキシAPIを使用
  const mockResults = [
    {
      platform: 'ebay',
      title: `${searchQuery} - eBay商品1`,
      url: 'https://www.ebay.com/itm/example1',
      image_url: 'https://i.ebayimg.com/images/g/example1.jpg',
      price: Math.floor(Math.random() * 50000) + 10000,
      shipping_fee: Math.floor(Math.random() * 2000),
      total_price: 0,
      condition: 'Used',
      store_name: 'eBay Seller',
      location: 'United States',
      currency: 'JPY'
    }
  ];

  // total_priceを計算
  mockResults.forEach(item => {
    item.total_price = item.price + item.shipping_fee;
  });

  return {
    success: true,
    platform: 'ebay',
    query: searchQuery,
    total_results: mockResults.length,
    results: mockResults,
    timestamp: new Date().toISOString(),
    note: 'フォールバック実装（実際のAPI制限のため）'
  };
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

    const response = await handleEbayFallbackSearch(productName, janCode, query, limit);
    console.log(`eBayフォールバック検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBayフォールバック検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'eBayフォールバック検索中にエラーが発生しました',
        platform: 'ebay',
        details: error instanceof Error ? error.message : '不明なエラー'
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

    const response = await handleEbayFallbackSearch(product_name, jan_code, query, limit);
    console.log(`eBayフォールバック検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBayフォールバック検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: 'eBayフォールバック検索中にエラーが発生しました',
        platform: 'ebay',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}
