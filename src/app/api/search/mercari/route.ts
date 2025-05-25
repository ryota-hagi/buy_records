import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

async function handleMercariSearch(productName: string | null, janCode: string | null, query: string | null, limit: number = 20) {
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

  console.log(`Mercari検索開始: ${searchQuery}`);

  try {
    // Mercari検索API（非公式）を試行
    const response = await axios.get('https://api.mercari.com/v2/entities:search', {
      params: {
        keyword: searchQuery,
        limit: Math.min(limit, 120),
        offset: 0,
        order: 'created_time',
        sort: 'desc',
        status: 'sold_out'
      },
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8'
      },
      timeout: 15000
    });

    const items = response.data?.data || [];
    
    // レスポンス形式を統一
    const formattedResults = items.slice(0, limit).map((item: any) => ({
      platform: 'mercari',
      title: item.name || '',
      url: `https://jp.mercari.com/item/${item.id}` || '',
      image_url: item.thumbnails?.[0] || '',
      price: parseInt(item.price) || 0,
      shipping_fee: item.shipping_payer === 'seller' ? 0 : 500, // 推定送料
      total_price: (parseInt(item.price) || 0) + (item.shipping_payer === 'seller' ? 0 : 500),
      condition: item.item_condition?.name || 'Used',
      store_name: item.seller?.name || '',
      location: item.seller?.profile?.region_name || '',
      currency: 'JPY',
      // 旧形式との互換性
      item_title: item.name || '',
      item_url: `https://jp.mercari.com/item/${item.id}` || '',
      item_image_url: item.thumbnails?.[0] || '',
      base_price: parseInt(item.price) || 0,
      item_condition: item.item_condition?.name || 'Used',
      seller_name: item.seller?.name || ''
    }));

    return {
      success: true,
      platform: 'mercari',
      query: searchQuery,
      total_results: formattedResults.length,
      results: formattedResults,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Mercari API呼び出しエラー:', error);
    
    // エラーの詳細をログに記録
    if (axios.isAxiosError(error)) {
      console.error('Mercari API Axiosエラー:', {
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

    const response = await handleMercariSearch(productName, janCode, query, limit);
    console.log(`Mercari検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Mercari検索エラー:', error);
    
    let errorMessage = 'Mercari検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'Mercari APIアクセスが拒否されました';
      } else if (error.response?.status === 429) {
        errorMessage = 'Mercari APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Mercari APIタイムアウトしました';
      } else if (error.response?.status === 404) {
        errorMessage = 'Mercari APIエンドポイントが見つかりません';
        details = `Request failed with status code 404: ${error.response?.data || 'Not Found'}`;
      }
    }
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'mercari',
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

    const response = await handleMercariSearch(product_name, jan_code, query, limit);
    console.log(`Mercari検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('Mercari検索エラー:', error);
    
    let errorMessage = 'Mercari検索中にエラーが発生しました';
    let details = error instanceof Error ? error.message : '不明なエラー';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        errorMessage = 'Mercari APIアクセスが拒否されました';
      } else if (error.response?.status === 429) {
        errorMessage = 'Mercari APIレート制限に達しました';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Mercari APIタイムアウトしました';
      } else if (error.response?.status === 404) {
        errorMessage = 'Mercari APIエンドポイントが見つかりません';
        details = `Request failed with status code 404: ${error.response?.data || 'Not Found'}`;
      }
    }
    
    return NextResponse.json(
      { 
        success: false,
        error: errorMessage,
        platform: 'mercari',
        details: details
      },
      { status: 500 }
    );
  }
}
