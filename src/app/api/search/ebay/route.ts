import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';
import { spawn } from 'child_process';
import path from 'path';

async function translateProductName(productName: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'scripts', 'translate_for_ebay.py');
    const pythonProcess = spawn('python', [pythonScript, productName]);
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve(output.trim());
      } else {
        console.warn(`翻訳に失敗、元のテキストを使用: ${errorOutput}`);
        resolve(productName); // 翻訳失敗時は元のテキストを使用
      }
    });
  });
}

async function getExchangeRate(): Promise<number> {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'scripts', 'get_exchange_rate.py');
    const pythonProcess = spawn('python', [pythonScript]);
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const rate = parseFloat(output.trim());
          if (!isNaN(rate) && rate > 0) {
            resolve(rate);
          } else {
            console.warn('為替レート取得失敗、フォールバックレートを使用: 150');
            resolve(150);
          }
        } catch (e) {
          console.warn('為替レート解析失敗、フォールバックレートを使用: 150');
          resolve(150);
        }
      } else {
        console.warn(`為替レート取得失敗、フォールバックレートを使用: ${errorOutput}`);
        resolve(150); // フォールバックレート
      }
    });
  });
}

async function handleEbaySearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20) {
  // 検索クエリを構築
  let searchQuery = '';
  if (productName) {
    searchQuery = await translateProductName(productName);
    console.log(`翻訳結果: ${productName} → ${searchQuery}`);
  } else if (janCode) {
    searchQuery = janCode;
  } else if (query) {
    searchQuery = query;
  } else {
    throw new Error('検索パラメータが不足しています');
  }

  console.log(`eBay検索開始: ${searchQuery}`);

  // 為替レートを取得
  const exchangeRate = await getExchangeRate();
  console.log(`為替レート: 1 USD = ${exchangeRate} JPY`);

  // eBay Finding API設定 - 複数のAPIキーでフォールバック
  const appIds = [
    process.env.EBAY_APP_ID,
    process.env.EBAY_USER_TOKEN,
    'ariGaT-records-PRD-1a6ee1171-104bfaa4',
    'YourAppI-d123-4567-8901-234567890123'
  ].filter(Boolean);
  
  let lastError: any = null;
  
  // 複数のAPIキーを順番に試行
  for (const appId of appIds) {
    try {
      console.log(`eBay API試行中: ${appId?.substring(0, 10)}...`);
      
      // eBay Browse API呼び出し（OAuth認証が必要）
      let response;
      let items = [];
      
      try {
        // まずOAuth2トークンを取得
        const tokenResponse = await axios.post('https://api.ebay.com/identity/v1/oauth2/token', 
          'grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope',
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Authorization': `Basic ${Buffer.from(`${appId}:${process.env.EBAY_CLIENT_SECRET}`).toString('base64')}`
            },
            timeout: 10000
          }
        );
        
        const accessToken = tokenResponse.data.access_token;
        
        // Browse APIで検索
        response = await axios.get('https://api.ebay.com/buy/browse/v1/item_summary/search', {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
          },
          params: {
            'q': searchQuery,
            'limit': Math.min(limit, 50),
            'sort': 'price',
            'filter': 'conditionIds:{1000|1500|2000|2500|3000|4000|5000}' // すべてのコンディション
          },
          timeout: 15000
        });
        
        items = response.data?.itemSummaries || [];
        
      } catch (browseError) {
        console.log('Browse API失敗、Finding APIにフォールバック');
        
        // Finding APIにフォールバック
        response = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
          params: {
            'OPERATION-NAME': 'findItemsByKeywords',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': appId,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',
            'keywords': searchQuery,
            'paginationInput.entriesPerPage': Math.min(limit, 100),
            'sortOrder': 'PricePlusShipping'
            // フィルターを削除してより多くの結果を取得
          },
          timeout: 15000
        });

        const searchResult = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0];
        items = searchResult?.item || [];
      }
      
      console.log(`eBay API成功: ${items.length}件取得`);
      
      // レスポンス形式を統一（Browse APIとFinding APIの両方に対応）
      const formattedResults = items.map((item: any) => {
        let currentPrice = 0;
        let shippingCost = 0;
        let title = '';
        let url = '';
        let imageUrl = '';
        let condition = 'Used';
        let sellerName = '';
        let location = '';
        
        // Browse API形式の場合
        if (item.price) {
          currentPrice = parseFloat(item.price.value || '0');
          title = item.title || '';
          url = item.itemWebUrl || '';
          imageUrl = item.image?.imageUrl || '';
          condition = item.condition || 'Used';
          sellerName = item.seller?.username || '';
          location = item.itemLocation?.country || '';
          shippingCost = parseFloat(item.shippingOptions?.[0]?.shippingCost?.value || '0');
        } 
        // Finding API形式の場合
        else {
          currentPrice = parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0');
          shippingCost = parseFloat(item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__ || '0');
          title = item.title?.[0] || '';
          url = item.viewItemURL?.[0] || '';
          imageUrl = item.galleryURL?.[0] || '';
          condition = item.condition?.[0]?.conditionDisplayName?.[0] || 'Used';
          sellerName = item.sellerInfo?.[0]?.sellerUserName?.[0] || '';
          location = item.location?.[0] || '';
        }
        
        // USD to JPY conversion using real-time exchange rate
        const priceJPY = Math.round(currentPrice * exchangeRate);
        const shippingJPY = Math.round(shippingCost * exchangeRate);
        
        return {
          platform: 'ebay',
          title: title,
          url: url,
          image_url: imageUrl,
          price: priceJPY,
          shipping_fee: shippingJPY,
          total_price: priceJPY + shippingJPY,
          condition: condition,
          store_name: sellerName,
          location: location,
          currency: 'JPY',
          exchange_rate: exchangeRate,
          // 旧形式との互換性
          item_title: title,
          item_url: url,
          item_image_url: imageUrl,
          base_price: priceJPY,
          item_condition: condition,
          seller_name: sellerName
        };
      });

      return {
        success: true,
        platform: 'ebay',
        query: searchQuery,
        total_results: formattedResults.length,
        results: formattedResults,
        timestamp: new Date().toISOString(),
        api_key_used: appId?.substring(0, 10) + '...',
        exchange_rate: exchangeRate
      };

    } catch (error) {
      console.error(`eBay API失敗 (${appId?.substring(0, 10)}...):`, error);
      lastError = error;
      
      // エラーの詳細をログに記録
      if (axios.isAxiosError(error)) {
        console.error('eBay API Axiosエラー:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        });
        
        // 403エラー（認証失敗）の場合は次のAPIキーを試行
        if (error.response?.status === 403) {
          continue;
        }
      }
      
      // その他のエラーの場合も次のAPIキーを試行
      continue;
    }
  }
  
  // すべてのAPIキーが失敗した場合、エラーを投げる
  console.log('eBay API全て失敗、エラーを投げます');
  
  throw new Error(`eBay検索に失敗しました。しばらく時間をおいて再試行してください。詳細: ${lastError instanceof Error ? lastError.message : 'Unknown error'}`);
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
        details: details,
        suggestion: 'しばらく時間をおいて再試行してください'
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
        details: details,
        suggestion: 'しばらく時間をおいて再試行してください'
      },
      { status: 500 }
    );
  }
}
