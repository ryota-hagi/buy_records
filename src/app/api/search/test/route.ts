import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

// 環境変数からAPIキーを取得
const TEST_YAHOO_SHOPPING_APP_ID = process.env.YAHOO_SHOPPING_APP_ID || '';
const TEST_EBAY_APP_ID = process.env.EBAY_APP_ID || '';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { jan_code } = body;

    if (!jan_code) {
      return NextResponse.json(
        { error: 'JANコードが必要です' },
        { status: 400 }
      );
    }

    console.log(`[TEST_SEARCH] Starting test search for JAN: ${jan_code}`);

    // Yahoo Shopping APIテスト
    let yahooResults = [];
    try {
      console.log(`[TEST_SEARCH] Testing Yahoo Shopping API...`);
      const yahooResponse = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
        params: {
          appid: TEST_YAHOO_SHOPPING_APP_ID,
          jan_code: jan_code,
          results: 5,
          sort: 'price',
          output: 'json'
        },
        timeout: 8000
      });

      console.log(`[TEST_SEARCH] Yahoo API response status: ${yahooResponse.status}`);
      const yahooItems = yahooResponse.data?.hits || [];
      console.log(`[TEST_SEARCH] Yahoo found ${yahooItems.length} items`);
      
      yahooResults = yahooItems.map((item: any) => ({
        platform: 'yahoo_shopping',
        item_title: item.name || '',
        item_url: item.url || '',
        price: parseInt(item.price || '0'),
        seller: item.store?.name || ''
      }));
    } catch (error) {
      console.error('[TEST_SEARCH] Yahoo API failed:', error);
    }

    // eBay APIテスト
    let ebayResults = [];
    try {
      console.log(`[TEST_SEARCH] Testing eBay API...`);
      const ebayResponse = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
        params: {
          'OPERATION-NAME': 'findItemsByKeywords',
          'SERVICE-VERSION': '1.0.0',
          'SECURITY-APPNAME': TEST_EBAY_APP_ID,
          'RESPONSE-DATA-FORMAT': 'JSON',
          'REST-PAYLOAD': '',
          'keywords': jan_code,
          'paginationInput.entriesPerPage': 5,
          'itemFilter(0).name': 'ListingType',
          'itemFilter(0).value': 'FixedPrice'
        },
        timeout: 8000
      });

      console.log(`[TEST_SEARCH] eBay API response status: ${ebayResponse.status}`);
      const ebayItems = ebayResponse.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
      console.log(`[TEST_SEARCH] eBay found ${ebayItems.length} items`);
      
      ebayResults = ebayItems.map((item: any) => ({
        platform: 'ebay',
        item_title: item.title?.[0] || '',
        item_url: item.viewItemURL?.[0] || '',
        price: parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0'),
        seller: item.sellerInfo?.[0]?.sellerUserName?.[0] || ''
      }));
    } catch (error) {
      console.error('[TEST_SEARCH] eBay API failed:', error);
    }

    const totalResults = yahooResults.length + ebayResults.length;
    
    console.log(`[TEST_SEARCH] Test completed: ${totalResults} total results`);

    return NextResponse.json({
      success: true,
      jan_code,
      total_results: totalResults,
      results: {
        yahoo_shopping: yahooResults,
        ebay: ebayResults
      },
      message: totalResults > 0 ? 
        'テスト検索成功！APIキーは正常に動作しています。' : 
        'APIキーは動作していますが、このJANコードでは結果が見つかりませんでした。',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[TEST_SEARCH] Error:', error);
    return NextResponse.json({
      success: false,
      error: (error as Error).message,
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}
