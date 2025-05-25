import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const productName = searchParams.get('product_name');
    const janCode = searchParams.get('jan_code');
    
    if (!productName && !janCode) {
      return NextResponse.json(
        { error: 'product_nameまたはjan_codeが必要です' },
        { status: 400 }
      );
    }

    const appId =
      process.env.EBAY_APP_ID ||
      process.env.EBAY_CLIENT_ID ||
      (process.env as any).EBAY_APPID;
    
    if (!appId) {
      return NextResponse.json(
        { error: 'eBay API設定が不完全です' },
        { status: 500 }
      );
    }

    // 検索クエリを構築
    let query = '';
    if (productName) {
      query = productName;
    } else if (janCode) {
      query = janCode;
    }

    console.log(`eBay検索開始: ${query}`);

    // eBay Finding API呼び出し（認証不要）
    const ebayResponse = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
      params: {
        'OPERATION-NAME': 'findItemsByKeywords',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': appId,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': query,
        'paginationInput.entriesPerPage': 20,
        'itemFilter(0).name': 'ListingType',
        'itemFilter(0).value': 'FixedPrice',
        'sortOrder': 'PricePlusShippingLowest'
      },
      timeout: 15000
    });

    const items = ebayResponse.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
    
    // レスポンス形式を統一
    const formattedResults = items.map((item: any) => {
      const basePrice = parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__) || 0;
      const shippingCost = parseFloat(item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__) || 0;
      
      return {
        platform: 'ebay',
        item_title: item.title?.[0] || '',
        item_url: item.viewItemURL?.[0] || '',
        item_image_url: item.galleryURL?.[0] || '',
        base_price: Math.round(basePrice * 150), // USD to JPY概算
        shipping_fee: Math.round(shippingCost * 150),
        total_price: Math.round((basePrice + shippingCost) * 150),
        item_condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'Used',
        seller_name: item.sellerInfo?.[0]?.sellerUserName?.[0] || '',
        location: item.location?.[0] || '',
        currency: 'JPY' // 変換後
      };
    });

    const response = {
      success: true,
      platform: 'ebay',
      query: query,
      total_results: formattedResults.length,
      results: formattedResults,
      timestamp: new Date().toISOString()
    };

    console.log(`eBay検索完了: ${formattedResults.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('eBay検索エラー:', error);
    
    let errorMessage = 'eBay検索中にエラーが発生しました';
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        errorMessage = 'eBay APIトークンが無効です';
      } else if (error.response?.status === 403) {
        errorMessage = 'eBay APIアクセスが拒否されました';
      } else if (error.response?.status === 429) {
        errorMessage = 'eBay APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'eBay APIタイムアウトしました';
      }
    }

    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'ebay',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}
