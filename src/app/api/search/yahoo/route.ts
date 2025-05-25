import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const janCode = searchParams.get('jan_code');
    const productName = searchParams.get('product_name');
    
    if (!janCode && !productName) {
      return NextResponse.json(
        { error: 'jan_codeまたはproduct_nameが必要です' },
        { status: 400 }
      );
    }

    const appId = process.env.YAHOO_SHOPPING_APP_ID;
    if (!appId) {
      return NextResponse.json(
        { error: 'Yahoo Shopping API設定が不完全です' },
        { status: 500 }
      );
    }

    console.log(`Yahoo Shopping検索開始 - JAN: ${janCode}, Product: ${productName}`);

    // Yahoo Shopping API呼び出し - JANコード優先
    let yahooResponse;
    if (janCode) {
      // JANコード検索
      yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
        params: {
          appid: appId,
          jan_code: janCode,
          results: 20,
          sort: 'price'
        },
        timeout: 10000
      });
    } else {
      // 商品名検索
      yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
        params: {
          appid: appId,
          query: productName,
          results: 20,
          sort: 'price'
        },
        timeout: 10000
      });
    }

    const items = yahooResponse.data?.hits || [];
    
    // レスポンス形式を統一
    const formattedResults = items.map((item: any) => ({
      platform: 'yahoo_shopping',
      item_title: item.name || '',
      item_url: item.url || '',
      item_image_url: item.image?.medium || item.image?.small || '',
      base_price: parseInt(item.price) || 0,
      shipping_fee: 0, // Yahoo Shoppingでは送料情報が限定的
      total_price: parseInt(item.price) || 0,
      item_condition: 'new', // Yahoo Shoppingは主に新品
      seller_name: item.seller?.name || '',
      location: '',
      currency: 'JPY'
    }));

    const response = {
      success: true,
      platform: 'yahoo_shopping',
      query: janCode || productName || '',
      total_results: formattedResults.length,
      results: formattedResults,
      timestamp: new Date().toISOString()
    };

    console.log(`Yahoo Shopping検索完了: ${formattedResults.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Yahoo Shopping検索エラー:', error);
    
    let errorMessage = 'Yahoo Shopping検索中にエラーが発生しました';
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'Yahoo Shopping APIキーが無効です';
      } else if (error.response?.status === 429) {
        errorMessage = 'Yahoo Shopping APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Yahoo Shopping APIタイムアウトしました';
      }
    }

    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'yahoo_shopping',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}
