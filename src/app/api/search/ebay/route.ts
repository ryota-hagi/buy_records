import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

async function handleEbaySearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20) {
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

  console.log(`eBay検索開始: ${searchQuery}`);

  // eBay Finding API設定
  const appId = process.env.EBAY_APP_ID || 'ariGaT-records-PRD-1a6ee1171-104bfaa4';
  
  try {
    // eBay Finding API呼び出し
    const response = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
      params: {
        'OPERATION-NAME': 'findItemsByKeywords',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': appId,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': searchQuery,
        'paginationInput.entriesPerPage': Math.min(limit, 100),
        'sortOrder': 'PricePlusShipping',
        'itemFilter(0).name': 'Condition',
        'itemFilter(0).value': 'Used',
        'itemFilter(1).name': 'ListingType',
        'itemFilter(1).value': 'FixedPrice'
      },
      timeout: 15000
    });

    const searchResult = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0];
    const items = searchResult?.item || [];
    
    // レスポンス形式を統一
    const formattedResults = items.map((item: any) => {
      const currentPrice = parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0');
      const shippingCost = parseFloat(item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__ || '0');
      
      // USD to JPY conversion (approximate rate: 1 USD = 150 JPY)
      const exchangeRate = 150;
      const priceJPY = Math.round(currentPrice * exchangeRate);
      const shippingJPY = Math.round(shippingCost * exchangeRate);
      
      return {
        platform: 'ebay',
        title: item.title?.[0] || '',
        url: item.viewItemURL?.[0] || '',
        image_url: item.galleryURL?.[0] || '',
        price: priceJPY,
        shipping_fee: shippingJPY,
        total_price: priceJPY + shippingJPY,
        condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'Used',
        store_name: item.sellerInfo?.[0]?.sellerUserName?.[0] || '',
        location: item.location?.[0] || '',
        currency: 'JPY',
        // 旧形式との互換性
        item_title: item.title?.[0] || '',
        item_url: item.viewItemURL?.[0] || '',
        item_image_url: item.galleryURL?.[0] || '',
        base_price: priceJPY,
        item_condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'Used',
        seller_name: item.sellerInfo?.[0]?.sellerUserName?.[0] || ''
      };
    });

    return {
      success: true,
      platform: 'ebay',
      query: searchQuery,
      total_results: formattedResults.length,
      results: formattedResults,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('eBay API呼び出しエラー:', error);
    
    // エラーの詳細をログに記録
    if (axios.isAxiosError(error)) {
      console.error('eBay API Axiosエラー:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      });
    }
    
    // APIエラーの場合は実際のエラーを返す（モックデータは生成しない）
    throw error;
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

    const response = await handleEbaySearch(productName, janCode, query, limit);
    console.log(`eBay検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    let errorMessage = 'eBay検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'eBay APIキーが無効です';
      } else if (error.response?.status === 429) {
        errorMessage = 'eBay APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'eBay APIタイムアウトしました';
      } else if (error.response?.status === 500) {
        errorMessage = 'eBay APIサーバーエラー';
        details = `Request failed with status code 500: ${error.response?.data || 'Internal Server Error'}`;
      }
    }
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'ebay',
        details: details
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

    const response = await handleEbaySearch(product_name, jan_code, query, limit);
    console.log(`eBay検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    let errorMessage = 'eBay検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'eBay APIキーが無効です';
      } else if (error.response?.status === 429) {
        errorMessage = 'eBay APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'eBay APIタイムアウトしました';
      } else if (error.response?.status === 500) {
        errorMessage = 'eBay APIサーバーエラー';
        details = `Request failed with status code 500: ${error.response?.data || 'Internal Server Error'}`;
      }
    }
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'ebay',
        details: details
      },
      { status: 500 }
    );
  }
}
