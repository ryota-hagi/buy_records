import { NextRequest, NextResponse } from 'next/server';

interface RakutenItem {
  itemName: string;
  itemPrice: number;
  itemUrl: string;
  mediumImageUrls: { imageUrl: string }[];
  shopName: string;
  reviewAverage: number;
  reviewCount: number;
  itemCaption?: string;
  availability: number;
  postageFlag: number;
  shopCode: string;
  itemCode: string;
}

interface RakutenSearchResult {
  count: number;
  page: number;
  first: number;
  last: number;
  hits: number;
  carrier: number;
  pageCount: number;
  Items: { Item: RakutenItem }[];
}

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

    console.log(`楽天検索開始: ${searchQuery}`);

    // 楽天APIキーの確認
    const appId = process.env.RAKUTEN_APP_ID;
    if (!appId) {
      console.error('楽天APIキーが設定されていません');
      return NextResponse.json(
        { 
          success: false,
          error: '楽天APIキーが設定されていません',
          results: []
        },
        { status: 500 }
      );
    }

    // 楽天市場検索API
    const baseUrl = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601';
    const params = new URLSearchParams({
      applicationId: appId,
      keyword: searchQuery,
      hits: Math.min(limit, 30).toString(), // 楽天APIの最大は30件
      sort: '+itemPrice', // 価格の安い順
      imageFlag: '1', // 画像ありのみ
      availability: '1', // 在庫ありのみ
      formatVersion: '2'
    });

    const response = await fetch(`${baseUrl}?${params.toString()}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('楽天APIエラー:', response.status, errorText);
      throw new Error(`楽天API error: ${response.status}`);
    }

    const data: RakutenSearchResult = await response.json();

    // 結果を標準フォーマットに変換
    const results = data.Items.map(({ Item }) => ({
      platform: 'rakuten',
      title: Item.itemName,
      price: Item.itemPrice,
      url: Item.itemUrl,
      image_url: Item.mediumImageUrls?.[0]?.imageUrl || '',
      shipping_fee: Item.postageFlag === 0 ? 0 : null, // 送料無料フラグ
      total_price: Item.itemPrice, // 送料が不明な場合は商品価格のみ
      condition: '新品', // 楽天市場は基本的に新品
      store_name: Item.shopName,
      location: 'Japan',
      currency: 'JPY',
      review_average: Item.reviewAverage,
      review_count: Item.reviewCount,
      description: Item.itemCaption,
      item_code: `${Item.shopCode}_${Item.itemCode}`,
      availability: Item.availability === 1
    }));

    console.log(`楽天検索完了: ${results.length}件`);

    return NextResponse.json({
      success: true,
      query: searchQuery,
      results: results,
      total_results: data.hits,
      page: data.page,
      page_count: data.pageCount,
      data_source: 'rakuten_api',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('楽天検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '楽天検索中にエラーが発生しました',
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
    console.error('楽天検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '楽天検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー',
        results: []
      },
      { status: 500 }
    );
  }
}