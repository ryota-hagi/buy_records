import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import axios from 'axios';

// 検索結果の型定義
interface SearchResult {
  platform: string;
  item_title: string;
  item_url: string;
  item_image_url: string;
  price: number;
  total_price: number;
  shipping_cost: number;
  condition: string;
  seller: string;
}

interface SearchResponse {
  finalResults: SearchResult[];
  platformResults: {
    ebay: SearchResult[];
    yahoo_shopping: SearchResult[];
    mercari: SearchResult[];
  };
  summary: {
    totalFound: number;
    afterDuplicateRemoval: number;
    finalCount: number;
    cheapest: SearchResult | null;
    mostExpensive: SearchResult | null;
    platformCounts: {
      ebay: number;
      yahoo_shopping: number;
      mercari: number;
    };
  };
}

// 環境変数の確認
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase環境変数が設定されていません。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// 直接API呼び出しによる検索実装（フォールバック版）
async function executeFallbackJanSearch(janCode: string): Promise<SearchResponse> {
  try {
    console.log(`[FALLBACK] Starting fallback JAN search for: ${janCode}`);
    console.log(
      `[FALLBACK] Environment check - EBAY_APP_ID: ${
        !!(
          process.env.EBAY_APP_ID ||
          process.env.EBAY_CLIENT_ID ||
          (process.env as any).EBAY_APPID
        )
      }, YAHOO_SHOPPING_APP_ID: ${!!process.env.YAHOO_SHOPPING_APP_ID}`
    );
    
    // 並行して各プラットフォームを検索
    const [yahooResults, ebayResults] = await Promise.all([
      searchYahooShoppingDirect(janCode, 20),
      searchEbayDirect(janCode, 20)
    ]);

    console.log(`[FALLBACK] Platform results - Yahoo: ${yahooResults.length}, eBay: ${ebayResults.length}`);

    // 結果統合
    const allResults = [...yahooResults, ...ebayResults];
    const deduplicatedResults = removeDuplicates(allResults);
    const sortedResults = deduplicatedResults.sort((a, b) => a.total_price - b.total_price);
    const finalResults = sortedResults.slice(0, 20);

    const response: SearchResponse = {
      finalResults,
      platformResults: {
        ebay: ebayResults,
        yahoo_shopping: yahooResults,
        mercari: [] // メルカリは後で実装
      },
      summary: {
        totalFound: allResults.length,
        afterDuplicateRemoval: deduplicatedResults.length,
        finalCount: finalResults.length,
        cheapest: finalResults.length > 0 ? finalResults[0] : null,
        mostExpensive: finalResults.length > 0 ? finalResults[finalResults.length - 1] : null,
        platformCounts: {
          ebay: ebayResults.length,
          yahoo_shopping: yahooResults.length,
          mercari: 0
        }
      }
    };

    console.log(`[FALLBACK] Search completed: ${finalResults.length} final results`);
    return response;

  } catch (error) {
    console.error('[FALLBACK] Error executing fallback search:', error);
    throw new Error(`フォールバック検索の実行に失敗しました: ${(error as Error).message}`);
  }
}

// Yahoo Shopping API直接呼び出し
async function searchYahooShoppingDirect(janCode: string, limit: number): Promise<SearchResult[]> {
  try {
    console.log(`[YAHOO_DIRECT] Starting Yahoo Shopping search for JAN: ${janCode}`);
    
    const yahooAppId = process.env.YAHOO_SHOPPING_APP_ID;
    if (!yahooAppId) {
      console.warn('[YAHOO_DIRECT] API key not configured');
      return [];
    }

    const response = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
      params: {
        appid: yahooAppId,
        jan_code: janCode,
        results: limit,
        sort: 'price',
        output: 'json'
      },
      timeout: 8000
    });

    console.log(`[YAHOO_DIRECT] API response status: ${response.status}`);
    console.log(`[YAHOO_DIRECT] API response data:`, JSON.stringify(response.data, null, 2));

    const items = response.data?.hits || [];
    console.log(`[YAHOO_DIRECT] Found ${items.length} items`);
    
    return items.map((item: any) => ({
      platform: 'yahoo_shopping',
      item_title: item.name || '',
      item_url: item.url || '',
      item_image_url: item.image?.medium || '',
      price: parseInt(item.price || '0'),
      total_price: parseInt(item.price || '0'),
      shipping_cost: 0,
      condition: '新品',
      seller: item.store?.name || '',
    }));

  } catch (error) {
    console.error('[YAHOO_DIRECT] Search failed:', error);
    if (axios.isAxiosError(error)) {
      console.error('[YAHOO_DIRECT] Axios error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      });
    }
    return [];
  }
}

// eBay API直接呼び出し
async function searchEbayDirect(janCode: string, limit: number): Promise<SearchResult[]> {
  try {
    console.log(`[EBAY_DIRECT] Starting eBay search for JAN: ${janCode}`);
    
    const ebayAppId =
      process.env.EBAY_APP_ID ||
      process.env.EBAY_CLIENT_ID ||
      (process.env as any).EBAY_APPID;
    if (!ebayAppId) {
      console.warn('[EBAY_DIRECT] API key not configured');
      return [];
    }

    const response = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
      params: {
        'OPERATION-NAME': 'findItemsByKeywords',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': ebayAppId,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': janCode,
        'paginationInput.entriesPerPage': limit,
        'itemFilter(0).name': 'ListingType',
        'itemFilter(0).value': 'FixedPrice'
      },
      timeout: 8000
    });

    console.log(`[EBAY_DIRECT] API response status: ${response.status}`);
    console.log(`[EBAY_DIRECT] API response data:`, JSON.stringify(response.data, null, 2));

    const items = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
    console.log(`[EBAY_DIRECT] Found ${items.length} items`);
    
    return items.map((item: any) => ({
      platform: 'ebay',
      item_title: item.title?.[0] || '',
      item_url: item.viewItemURL?.[0] || '',
      item_image_url: item.galleryURL?.[0] || '',
      price: parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0'),
      total_price: parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0'),
      shipping_cost: parseFloat(item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__ || '0'),
      condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'Used',
      seller: item.sellerInfo?.[0]?.sellerUserName?.[0] || ''
    }));

  } catch (error) {
    console.error('[EBAY_DIRECT] Search failed:', error);
    if (axios.isAxiosError(error)) {
      console.error('[EBAY_DIRECT] Axios error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      });
    }
    return [];
  }
}

// 重複除去
function removeDuplicates(results: SearchResult[]): SearchResult[] {
  const seen = new Set<string>();
  return results.filter((item) => {
    const key = `${item.platform}-${item.item_title.toLowerCase()}-${item.price}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

// POST: フォールバック検索タスクを作成
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { jan_code } = body;

    // JANコードのバリデーション
    if (!jan_code || typeof jan_code !== 'string') {
      return NextResponse.json(
        { error: 'JANコードが必要です' },
        { status: 400 }
      );
    }

    const cleanJanCode = jan_code.replace(/\D/g, '');
    if (!/^\d{8}$|^\d{13}$/.test(cleanJanCode)) {
      return NextResponse.json(
        { error: 'JANコードは8桁または13桁の数字である必要があります' },
        { status: 400 }
      );
    }

    console.log(`Creating fallback search task for JAN code: ${cleanJanCode}`);

    // タスクをデータベースに作成（pending状態）
    const taskData = {
      name: `フォールバック検索 (JANコード: ${cleanJanCode})`,
      status: 'pending',
      search_params: {
        jan_code: cleanJanCode,
        platforms: ['yahoo_shopping', 'ebay'],
        search_type: 'fallback'
      },
      processing_logs: [
        {
          timestamp: new Date().toISOString(),
          step: 'task_created',
          status: 'info',
          message: 'フォールバック検索タスクが作成されました'
        }
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { data: task, error: insertError } = await supabase
      .from('search_tasks')
      .insert(taskData)
      .select()
      .single();

    if (insertError) {
      console.error('Database insert error:', insertError);
      return NextResponse.json(
        { error: 'タスクの作成に失敗しました' },
        { status: 500 }
      );
    }

    console.log(`Fallback search task created: ${task.id}`);

    // バックグラウンドでフォールバック検索を実行開始
    executeFallbackTaskInBackground(task.id, cleanJanCode).catch(error => {
      console.error(`Background fallback task execution failed for task ${task.id}:`, error);
    });

    // タスク作成の成功レスポンスを即座に返す
    return NextResponse.json({
      success: true,
      task: {
        id: task.id,
        name: task.name,
        status: task.status,
        search_params: task.search_params,
        created_at: task.created_at
      }
    });

  } catch (error) {
    console.error('Error creating fallback search task:', error);
    return NextResponse.json(
      { error: 'フォールバックタスクの作成中にエラーが発生しました: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

// バックグラウンドでフォールバック検索タスクを実行する関数
async function executeFallbackTaskInBackground(taskId: string, janCode: string) {
  try {
    // タスクを実行中に更新
    await supabase
      .from('search_tasks')
      .update({
        status: 'running',
        updated_at: new Date().toISOString(),
        processing_logs: [
          {
            timestamp: new Date().toISOString(),
            step: 'fallback_search_started',
            status: 'info',
            message: 'フォールバック検索を開始しました（Yahoo Shopping + eBay直接API呼び出し）'
          }
        ]
      })
      .eq('id', taskId);

    console.log(`Starting fallback search for task ${taskId}, JAN: ${janCode}`);

    // フォールバック検索を実行
    const searchResult = await executeFallbackJanSearch(janCode);
    
    console.log(`Fallback search completed for task ${taskId}. Found ${searchResult.finalResults.length} results`);

    // タスクを完了状態に更新
    await supabase
      .from('search_tasks')
      .update({
        status: 'completed',
        result: {
          integrated_results: {
            count: searchResult.finalResults.length,
            items: searchResult.finalResults
          },
          platform_results: searchResult.platformResults,
          summary: searchResult.summary
        },
        completed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        processing_logs: [
          {
            timestamp: new Date().toISOString(),
            step: 'fallback_search_completed',
            status: 'success',
            message: `フォールバック検索が完了しました（${searchResult.finalResults.length}件の結果）- Yahoo: ${searchResult.summary.platformCounts.yahoo_shopping}件, eBay: ${searchResult.summary.platformCounts.ebay}件`
          }
        ]
      })
      .eq('id', taskId);

    // 検索結果をsearch_resultsテーブルにも保存
    if (searchResult.finalResults.length > 0) {
      const resultsData = searchResult.finalResults.map((result: SearchResult) => ({
        task_id: taskId,
        platform: result.platform || 'unknown',
        item_title: result.item_title || '',
        item_url: result.item_url || '',
        item_image_url: result.item_image_url || '',
        base_price: result.price || 0,
        shipping_fee: result.shipping_cost || 0,
        total_price: result.total_price || 0,
        item_condition: result.condition || '',
        seller_name: result.seller || ''
      }));

      console.log(`Inserting ${resultsData.length} fallback search results into search_results table for task ${taskId}`);
      
      const { error: insertError } = await supabase
        .from('search_results')
        .insert(resultsData);
        
      if (insertError) {
        console.error(`Error inserting fallback search results for task ${taskId}:`, insertError);
      } else {
        console.log(`Successfully inserted ${resultsData.length} fallback search results for task ${taskId}`);
      }
    }

    console.log(`Fallback search task ${taskId} completed successfully`);

  } catch (error) {
    console.error(`Error executing fallback task ${taskId}:`, error);
    
    // タスクを失敗状態に更新
    await supabase
      .from('search_tasks')
      .update({
        status: 'failed',
        error: (error as Error).message,
        updated_at: new Date().toISOString(),
        processing_logs: [
          {
            timestamp: new Date().toISOString(),
            step: 'fallback_search_failed',
            status: 'error',
            message: `フォールバック検索に失敗しました: ${(error as Error).message}`
          }
        ]
      })
      .eq('id', taskId);
  }
}
