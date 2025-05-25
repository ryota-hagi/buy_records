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

    const appId = process.env.EBAY_APP_ID;
    const userToken = process.env.EBAY_USER_TOKEN;
    
    if (!appId || !userToken) {
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

    // eBay Browse API呼び出し
    const ebayResponse = await axios.get('https://api.ebay.com/buy/browse/v1/item_summary/search', {
      params: {
        q: query,
        limit: 20,
        sort: 'price',
        filter: 'conditionIds:{1000|1500|2000|2500|3000|4000|5000|6000}', // 全ての状態
        fieldgroups: 'MATCHING_ITEMS,EXTENDED'
      },
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
        'X-EBAY-C-ENDUSERCTX': `affiliateCampaignId=${appId}`
      },
      timeout: 15000
    });

    const items = ebayResponse.data?.itemSummaries || [];
    
    // レスポンス形式を統一
    const formattedResults = items.map((item: any) => {
      const basePrice = parseFloat(item.price?.value) || 0;
      const shippingCost = parseFloat(item.shippingOptions?.[0]?.shippingCost?.value) || 0;
      
      return {
        platform: 'ebay',
        item_title: item.title || '',
        item_url: item.itemWebUrl || '',
        item_image_url: item.image?.imageUrl || '',
        base_price: Math.round(basePrice * 150), // USD to JPY概算
        shipping_fee: Math.round(shippingCost * 150),
        total_price: Math.round((basePrice + shippingCost) * 150),
        item_condition: item.condition || 'unknown',
        seller_name: item.seller?.username || '',
        location: item.itemLocation?.country || '',
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
