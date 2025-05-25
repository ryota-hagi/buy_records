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


// 重複除去関数
function removeDuplicates(results: SearchResult[]): SearchResult[] {
  const seen = new Set<string>();
  return results.filter((item: SearchResult) => {
    const key = `${item.platform}-${item.item_title}-${item.price}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

// 環境変数の確認
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase環境変数が設定されていません。NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// JANコードから商品名を取得する関数（API検索結果から取得）
async function getProductNameFromJan(janCode: string): Promise<string> {
  try {
    console.log(`[PRODUCT_NAME] Fetching product name for JAN: ${janCode}`);
    
    // まずeBay APIで商品名を取得を試行
    const ebayAppId = process.env.EBAY_APP_ID;
    if (ebayAppId) {
      try {
        const response = await axios.get('https://svcs.ebay.com/services/search/FindingService/v1', {
          params: {
            'OPERATION-NAME': 'findItemsByKeywords',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': ebayAppId,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',
            'keywords': janCode,
            'paginationInput.entriesPerPage': 1
          },
          timeout: 3000
        });

        const items = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
        if (items.length > 0 && items[0].title?.[0]) {
          const productName = items[0].title[0];
          console.log(`[PRODUCT_NAME] Found product name from eBay: ${productName}`);
          return productName;
        }
      } catch (error) {
        console.warn(`[PRODUCT_NAME] eBay API failed for product name lookup:`, error);
      }
    }

    // eBayで見つからない場合、Yahoo Shopping APIで試行
    const yahooAppId = process.env.YAHOO_SHOPPING_APP_ID;
    if (yahooAppId) {
      try {
        const response = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
          params: {
            appid: yahooAppId,
            jan_code: janCode,
            results: 1,
            output: 'json'
          },
          timeout: 3000
        });

        const items = response.data?.hits || [];
        if (items.length > 0 && items[0].name) {
          const productName = items[0].name;
          console.log(`[PRODUCT_NAME] Found product name from Yahoo: ${productName}`);
          return productName;
        }
      } catch (error) {
        console.warn(`[PRODUCT_NAME] Yahoo API failed for product name lookup:`, error);
      }
    }

    // どちらのAPIでも見つからない場合はデフォルト名を返す
    console.warn(`[PRODUCT_NAME] No product name found for JAN: ${janCode}`);
    return `商品 (JANコード: ${janCode})`;
    
  } catch (error) {
    console.error(`[PRODUCT_NAME] Error fetching product name:`, error);
    return `商品 (JANコード: ${janCode})`;
  }
}

// JANコード検索を実行する関数（Node.js版 - Vercel対応）
async function executeJanSearch(janCode: string): Promise<SearchResponse> {
  try {
    console.log(`[MAIN] Starting Node.js JAN search for: ${janCode}`);
    console.log(`[MAIN] Target: 10 items each from eBay API, Yahoo API → 20 total`);
    
    // 環境変数の詳細チェック
    const ebayAppId = process.env.EBAY_APP_ID;
    const yahooAppId = process.env.YAHOO_SHOPPING_APP_ID;
    
    console.log(`[MAIN] Environment variables check:`);
    console.log(`[MAIN] - EBAY_APP_ID: ${ebayAppId ? `SET (${ebayAppId.substring(0, 10)}...)` : 'NOT SET'}`);
    console.log(`[MAIN] - YAHOO_SHOPPING_APP_ID: ${yahooAppId ? `SET (${yahooAppId.substring(0, 10)}...)` : 'NOT SET'}`);
    console.log(`[MAIN] - NODE_ENV: ${process.env.NODE_ENV}`);
    console.log(`[MAIN] - All env keys:`, Object.keys(process.env).filter(key => key.includes('EBAY') || key.includes('YAHOO')));
    console.log(`[MAIN] - All env keys (full):`, Object.keys(process.env).sort());
    
    // 環境変数が設定されていない場合は即座にエラーを返す
    if (!ebayAppId && !yahooAppId) {
      const errorMsg = `API検索に失敗しました。eBay、Yahoo Shopping、メルカリのAPIが利用できません。環境変数が設定されていません。
      利用可能な環境変数: ${Object.keys(process.env).filter(key => key.includes('EBAY') || key.includes('YAHOO')).join(', ')}
      NODE_ENV: ${process.env.NODE_ENV}`;
      throw new Error(errorMsg);
    }
    
    // 各プラットフォームから並行して検索
    console.log(`[MAIN] Starting parallel search execution...`);
    const [ebayResults, yahooResults] = await Promise.all([
      searchEbayNodeJS(janCode, 10),
      searchYahooShoppingNodeJS(janCode, 10)
    ]);

    console.log(`[MAIN] Platform results: eBay ${ebayResults.length}, Yahoo ${yahooResults.length}`);

    // 全結果を統合
    const allResults = [...ebayResults, ...yahooResults];
    console.log(`[MAIN] Combined results: ${allResults.length} total items`);
    
    // 重複除去
    const uniqueResults = removeDuplicates(allResults);
    console.log(`[MAIN] After duplicate removal: ${uniqueResults.length} unique items`);
    
    // 価格順でソート
    const sortedResults = uniqueResults.sort((a, b) => a.total_price - b.total_price);
    console.log(`[MAIN] Results sorted by price`);
    
    // 最終的に20件に制限
    const finalResults = sortedResults.slice(0, 20);
    console.log(`[MAIN] Final results: ${finalResults.length} items (limited to 20)`);
    
    // 結果が0件の場合の詳細ログ
    if (finalResults.length === 0) {
      console.warn(`[MAIN] WARNING: No results found for JAN ${janCode}`);
      console.warn(`[MAIN] eBay results: ${ebayResults.length}, Yahoo results: ${yahooResults.length}`);
      console.warn(`[MAIN] This may indicate API configuration issues or no matching products`);
    }
    
    const response = {
      finalResults,
      platformResults: {
        ebay: ebayResults,
        yahoo_shopping: yahooResults,
        mercari: [] // メルカリは本番環境では無効
      },
      summary: {
        totalFound: allResults.length,
        afterDuplicateRemoval: uniqueResults.length,
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
    
    console.log(`[MAIN] Search completed successfully. Response summary:`, JSON.stringify(response.summary, null, 2));
    return response;
    
  } catch (error) {
    console.error('[MAIN] Error executing Node.js JAN search:', error);
    throw new Error(`Node.js検索の実行に失敗しました: ${(error as Error).message}`);
  }
}

// eBay API検索（Node.js版）
async function searchEbayNodeJS(janCode: string, limit: number): Promise<SearchResult[]> {
  try {
    console.log(`[eBay] Starting search for JAN: ${janCode}`);
    
    const ebayAppId = process.env.EBAY_APP_ID;
    console.log(`[eBay] API Key configured: ${ebayAppId ? 'YES' : 'NO'}`);
    
    if (!ebayAppId) {
      console.warn('[eBay] API key not configured, skipping eBay search');
      return [];
    }

    console.log(`[eBay] Making API request to eBay Finding Service...`);
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
        'itemFilter(0).value': 'FixedPrice',
        'itemFilter(1).name': 'Condition',
        'itemFilter(1).value': 'New'
      },
      timeout: 5000
    });

    console.log(`[eBay] API response status: ${response.status}`);
    console.log(`[eBay] API response data structure:`, JSON.stringify(response.data, null, 2).substring(0, 500));

    const items = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
    console.log(`[eBay] Found ${items.length} raw items`);
    
    const results: SearchResult[] = items.map((item: any) => ({
      platform: 'ebay',
      item_title: item.title?.[0] || '',
      item_url: item.viewItemURL?.[0] || '',
      item_image_url: item.galleryURL?.[0] || '',
      price: parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0'),
      total_price: parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0'),
      shipping_cost: parseFloat(item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__ || '0'),
      condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'New',
      seller: item.sellerInfo?.[0]?.sellerUserName?.[0] || ''
    }));

    console.log(`[eBay] Search completed successfully: ${results.length} items processed`);
    return results;
    
  } catch (error) {
    console.error('[eBay] Search error details:', {
      message: (error as Error).message,
      status: (error as any).response?.status,
      statusText: (error as any).response?.statusText,
      data: (error as any).response?.data
    });
    return [];
  }
}

// Yahoo Shopping API検索（Node.js版）
async function searchYahooShoppingNodeJS(janCode: string, limit: number): Promise<SearchResult[]> {
  try {
    console.log(`[Yahoo] Starting search for JAN: ${janCode}`);
    
    const yahooAppId = process.env.YAHOO_SHOPPING_APP_ID;
    console.log(`[Yahoo] API Key configured: ${yahooAppId ? 'YES' : 'NO'}`);
    
    if (!yahooAppId) {
      console.warn('[Yahoo] API key not configured, skipping Yahoo search');
      return [];
    }

    console.log(`[Yahoo] Making API request to Yahoo Shopping Service...`);
    const response = await axios.get('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch', {
      params: {
        appid: yahooAppId,
        jan_code: janCode,
        results: limit,
        sort: 'price',
        output: 'json'
      },
      timeout: 5000
    });

    console.log(`[Yahoo] API response status: ${response.status}`);
    console.log(`[Yahoo] API response data structure:`, JSON.stringify(response.data, null, 2).substring(0, 500));

    const items = response.data?.hits || [];
    console.log(`[Yahoo] Found ${items.length} raw items`);
    
    const results: SearchResult[] = items.map((item: any) => ({
      platform: 'yahoo_shopping',
      item_title: item.name || '',
      item_url: item.url || '',
      item_image_url: item.image?.medium || '',
      price: parseInt(item.price || '0'),
      total_price: parseInt(item.price || '0'),
      shipping_cost: 0,
      condition: '新品',
      seller: item.store?.name || ''
    }));

    console.log(`[Yahoo] Search completed successfully: ${results.length} items processed`);
    return results;
    
  } catch (error) {
    console.error('[Yahoo] Search error details:', {
      message: (error as Error).message,
      status: (error as any).response?.status,
      statusText: (error as any).response?.statusText,
      data: (error as any).response?.data
    });
    return [];
  }
}

// GET: タスク一覧を取得
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const status = searchParams.get('status');

    const offset = (page - 1) * limit;

    // クエリを構築
    let query = supabase
      .from('search_tasks')
      .select('*', { count: 'exact' });

    if (status) {
      query = query.eq('status', status);
    }

    query = query
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    const { data: tasks, error, count } = await query;

    if (error) {
      console.error('Database query error:', error);
      return NextResponse.json(
        { error: 'タスクの取得に失敗しました' },
        { status: 500 }
      );
    }

    // 各タスクに検索結果を追加
    const tasksWithResults = await Promise.all((tasks || []).map(async (task) => {
      try {
        // search_resultsテーブルから結果を取得
        const { data: results, error: resultsError } = await supabase
          .from('search_results')
          .select('*')
          .eq('task_id', task.id)
          .order('total_price', { ascending: true });

        if (resultsError) {
          console.error('Error fetching results for task', task.id, ':', resultsError);
        }

        return {
          ...task,
          results: results || [],
          results_count: results?.length || 0
        };
      } catch (err) {
        console.error('Error processing task', task.id, ':', err);
        return {
          ...task,
          results: [],
          results_count: 0
        };
      }
    }));

    const totalPages = Math.ceil((count || 0) / limit);

    return NextResponse.json({
      success: true,
      tasks: tasksWithResults,
      pagination: {
        page,
        limit,
        total: count || 0,
        totalPages
      }
    });

  } catch (error) {
    console.error('Error fetching tasks:', error);
    return NextResponse.json(
      { error: '内部サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}

// POST: 新しい検索タスクを作成（バックグラウンド実行）
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

    console.log(`Creating real search task for JAN code: ${cleanJanCode}`);

    // JANコードから商品名を取得（API検索）
    const productName = await getProductNameFromJan(cleanJanCode);

    // タスクをデータベースに作成（pending状態）
    const taskData = {
      name: productName,
      status: 'pending',
      search_params: {
        jan_code: cleanJanCode,
        platforms: ['ebay', 'yahoo_shopping', 'mercari']
      },
      processing_logs: [
        {
          timestamp: new Date().toISOString(),
          step: 'task_created',
          status: 'info',
          message: 'タスクが作成されました（実際のAPI検索版）'
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

    console.log(`Real search task created: ${task.id}`);

    // バックグラウンドでタスクを実行開始
    executeTaskInBackground(task.id, cleanJanCode).catch(error => {
      console.error(`Background task execution failed for task ${task.id}:`, error);
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
    console.error('Error creating search task:', error);
    return NextResponse.json(
      { error: 'タスクの作成中にエラーが発生しました: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

// バックグラウンドでタスクを実行する関数（Vercel対応版）
async function executeTaskInBackground(taskId: string, janCode: string) {
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
            step: 'search_started',
            status: 'info',
            message: 'Vercel環境での高速検索を開始しました（タイムアウト対策版）'
          }
        ]
      })
      .eq('id', taskId);

    console.log(`Starting Vercel-optimized search for task ${taskId}, JAN: ${janCode}`);

    // Vercelの制限に対応した高速検索（5秒以内で完了）
    const searchResult = await executeJanSearch(janCode);
    
    console.log(`Vercel search completed for task ${taskId}. Found ${searchResult.finalResults.length} results`);

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
            step: 'search_completed',
            status: 'success',
            message: `Vercel環境での検索が完了しました（${searchResult.finalResults.length}件の結果）`
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
        item_condition: result.condition || '',
        seller_name: result.seller || ''
      }));

      console.log(`Inserting ${resultsData.length} search results into search_results table for task ${taskId}`);
      
      const { error: insertError } = await supabase
        .from('search_results')
        .insert(resultsData);
        
      if (insertError) {
        console.error(`Error inserting search results for task ${taskId}:`, insertError);
      } else {
        console.log(`Successfully inserted ${resultsData.length} search results for task ${taskId}`);
      }
    }

    console.log(`Vercel search task ${taskId} completed successfully`);

  } catch (error) {
    console.error(`Error executing Vercel task ${taskId}:`, error);
    
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
            step: 'search_failed',
            status: 'error',
            message: `Vercel環境での検索に失敗しました: ${(error as Error).message}`
          }
        ]
      })
      .eq('id', taskId);
  }
}
