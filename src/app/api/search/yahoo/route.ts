import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

async function handleYahooSearch(janCode: string | null, productName: string | null, query: string | null, limit: number = 20) {
  // 環境変数が読み込まれない場合の直接設定
  const appId = process.env.YAHOO_SHOPPING_APP_ID || 'dj00aiZpPVBkdm9nV2F0WTZDVyZzPWNvbnN1bWVyc2VjcmV0Jng9OTk-';
  if (!appId) {
    throw new Error('Yahoo Shopping API設定が不完全です');
  }

  console.log(`Yahoo Shopping検索開始 - JAN: ${janCode}, Product: ${productName}, Query: ${query}`);

  // Yahoo Shopping API呼び出し - 優先順位: JANコード > 商品名 > クエリ
  let yahooResponse;
  if (janCode) {
    // JANコード検索 - Yahoo Shopping APIではqueryパラメータでJANコードを検索
    yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
      params: {
        appid: appId,
        query: janCode,
        results: limit
      },
      timeout: 10000
    });
  } else if (productName) {
    // 商品名検索
    yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
      params: {
        appid: appId,
        query: productName,
        results: limit
      },
      timeout: 10000
    });
  } else if (query) {
    // 一般クエリ検索
    yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
      params: {
        appid: appId,
        query: query,
        results: limit
      },
      timeout: 10000
    });
  } else {
    throw new Error('検索パラメータが不足しています');
  }

  const items = yahooResponse.data?.hits || [];
  
  // レスポンス形式を統一
  const formattedResults = items.map((item: any) => ({
    platform: 'yahoo_shopping',
    title: item.name || '',
    url: item.url || '',
    image_url: item.image?.medium || item.image?.small || '',
    price: parseInt(item.price) || 0,
    shipping_fee: 0, // Yahoo Shoppingでは送料情報が限定的
    total_price: parseInt(item.price) || 0,
    condition: 'new', // Yahoo Shoppingは主に新品
    store_name: item.seller?.name || '',
    location: '',
    currency: 'JPY',
    // 旧形式との互換性
    item_title: item.name || '',
    item_url: item.url || '',
    item_image_url: item.image?.medium || item.image?.small || '',
    base_price: parseInt(item.price) || 0,
    item_condition: 'new',
    seller_name: item.seller?.name || ''
  }));

  return {
    success: true,
    platform: 'yahoo_shopping',
    query: janCode || productName || query || '',
    total_results: formattedResults.length,
    results: formattedResults,
    timestamp: new Date().toISOString()
  };
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const janCode = searchParams.get('jan_code');
    const productName = searchParams.get('product_name');
    const query = searchParams.get('query');
    const limit = parseInt(searchParams.get('limit') || '20');
    
    if (!janCode && !productName && !query) {
      return NextResponse.json(
        { error: 'jan_code、product_name、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await handleYahooSearch(janCode, productName, query, limit);
    console.log(`Yahoo Shopping検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Yahoo Shopping検索エラー:', error);
    
    let errorMessage = 'Yahoo Shopping検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'Yahoo Shopping APIキーが無効です';
      } else if (error.response?.status === 429) {
        errorMessage = 'Yahoo Shopping APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Yahoo Shopping APIタイムアウトしました';
      } else if (error.response?.status === 400) {
        errorMessage = 'Yahoo Shopping API リクエストパラメータエラー';
        details = `Request failed with status code 400: ${error.response?.data || 'Bad Request'}`;
      }
    }

    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'yahoo_shopping',
        details: details
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { jan_code, product_name, query, limit = 20 } = body;
    
    if (!jan_code && !product_name && !query) {
      return NextResponse.json(
        { error: 'jan_code、product_name、またはqueryが必要です' },
        { status: 400 }
      );
    }

    const response = await handleYahooSearch(jan_code, product_name, query, limit);
    console.log(`Yahoo Shopping検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Yahoo Shopping検索エラー:', error);
    
    let errorMessage = 'Yahoo Shopping検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'Yahoo Shopping APIキーが無効です';
      } else if (error.response?.status === 429) {
        errorMessage = 'Yahoo Shopping APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Yahoo Shopping APIタイムアウトしました';
      } else if (error.response?.status === 400) {
        errorMessage = 'Yahoo Shopping API リクエストパラメータエラー';
        details = `Request failed with status code 400: ${error.response?.data || 'Bad Request'}`;
      }
    }

    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'yahoo_shopping',
        details: details
      },
      { status: 500 }
    );
  }
}
