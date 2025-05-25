import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Supabaseクライアント初期化
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// 統合検索エンジンの機能を直接実装
async function executeUnifiedJanSearch(janCode: string) {
  console.log(`[UNIFIED_SEARCH] Starting search for JAN: ${janCode}`);
  
  const startTime = Date.now();
  const results = {
    success: false,
    product_name: '',
    total_results: 0,
    platform_results: {
      yahoo_shopping: [],
      mercari: [],
      ebay: []
    },
    final_results: [],
    summary: {
      total_found: 0,
      after_deduplication: 0,
      final_count: 0,
      execution_time_ms: 0
    }
  };

  try {
    // 並列でプラットフォーム検索を実行
    const searchPromises = [
      searchYahooShopping(janCode),
      searchMercari(janCode),
      searchEbay(janCode)
    ];

    const platformResults = await Promise.allSettled(searchPromises);
    
    // Yahoo Shopping結果
    if (platformResults[0].status === 'fulfilled') {
      results.platform_results.yahoo_shopping = platformResults[0].value;
    }
    
    // Mercari結果
    if (platformResults[1].status === 'fulfilled') {
      results.platform_results.mercari = platformResults[1].value;
    }
    
    // eBay結果
    if (platformResults[2].status === 'fulfilled') {
      results.platform_results.ebay = platformResults[2].value;
    }

    // 結果を統合
    const allResults = [
      ...results.platform_results.yahoo_shopping,
      ...results.platform_results.mercari,
      ...results.platform_results.ebay
    ];

    results.total_results = allResults.length;
    results.final_results = allResults.slice(0, 50); // 最大50件
    results.summary.total_found = allResults.length;
    results.summary.final_count = results.final_results.length;
    results.summary.execution_time_ms = Date.now() - startTime;

    // 商品名を取得（最初に見つかった商品名を使用）
    if (results.final_results.length > 0) {
      const firstItem = results.final_results[0] as any;
      results.product_name = firstItem?.title || firstItem?.name || `商品検索 (JANコード: ${janCode})`;
    } else {
      results.product_name = `商品検索 (JANコード: ${janCode})`;
    }

    results.success = true;
    console.log(`[UNIFIED_SEARCH] Completed: ${results.final_results.length} results in ${results.summary.execution_time_ms}ms`);

  } catch (error) {
    console.error('[UNIFIED_SEARCH] Error:', error);
    results.product_name = `商品検索 (JANコード: ${janCode})`;
  }

  return results;
}

// Yahoo Shopping検索
async function searchYahooShopping(janCode: string) {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'https://buy-records.vercel.app'}/api/search/yahoo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jan_code: janCode, limit: 20 })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.items || [];
    }
  } catch (error) {
    console.error('[YAHOO_SEARCH] Error:', error);
  }
  return [];
}

// Mercari検索
async function searchMercari(janCode: string) {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'https://buy-records.vercel.app'}/api/search/mercari`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jan_code: janCode, limit: 20 })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.items || [];
    }
  } catch (error) {
    console.error('[MERCARI_SEARCH] Error:', error);
  }
  return [];
}

// eBay検索
async function searchEbay(janCode: string) {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'https://buy-records.vercel.app'}/api/search/ebay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jan_code: janCode, limit: 20 })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.items || [];
    }
  } catch (error) {
    console.error('[EBAY_SEARCH] Error:', error);
  }
  return [];
}

/**
 * 統合検索エンジン使用版タスク作成API
 */
export async function POST(request: NextRequest) {
  console.log('[TASK_CREATE] POST request received');
  
  let body: any;
  
  try {
    // リクエストボディの安全な解析
    try {
      body = await request.json();
      console.log('[TASK_CREATE] Request body parsed:', body);
    } catch (parseError) {
      console.error('[TASK_CREATE] JSON parse error:', parseError);
      return NextResponse.json({
        success: false,
        error: 'リクエストボディの解析に失敗しました'
      }, { status: 400 });
    }

    const { jan_code } = body;

    // JANコードのバリデーション
    if (!jan_code || typeof jan_code !== 'string') {
      console.error('[TASK_CREATE] Invalid JAN code:', jan_code);
      return NextResponse.json({
        success: false,
        error: 'JANコードが必要です'
      }, { status: 400 });
    }

    const cleanJanCode = jan_code.trim().replace(/[^0-9]/g, '');
    if (cleanJanCode.length !== 13 && cleanJanCode.length !== 8) {
      console.error('[TASK_CREATE] Invalid JAN code length:', cleanJanCode.length);
      return NextResponse.json({
        success: false,
        error: 'JANコードは8桁または13桁の数字である必要があります'
      }, { status: 400 });
    }

    console.log('[TASK_CREATE] Creating task for JAN code:', cleanJanCode);

    // 統合検索エンジンを使用してタスク名を取得
    let taskName = `商品検索 (JANコード: ${cleanJanCode})`;
    
    try {
      console.log('[TASK_CREATE] Attempting to get product name from unified search engine');
      
      // 10秒タイムアウトで商品名取得を試行
      const productNamePromise = executeUnifiedJanSearch(cleanJanCode);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Product name fetch timeout')), 10000)
      );
      
      const unifiedResult = await Promise.race([productNamePromise, timeoutPromise]) as any;
      
      if (unifiedResult?.success && unifiedResult?.product_name) {
        taskName = unifiedResult.product_name;
        console.log('[TASK_CREATE] Product name obtained from unified search:', taskName);
      } else {
        console.log('[TASK_CREATE] Using default task name due to unified search failure');
      }
    } catch (error) {
      console.warn('[TASK_CREATE] Failed to get product name from unified search:', error);
      // フォールバック: デフォルト名を使用
    }
    
    // Supabaseにタスクを作成
    const { data: task, error: insertError } = await supabase
      .from('search_tasks')
      .insert({
        name: taskName,
        status: 'pending',
        search_params: {
          jan_code: cleanJanCode,
          platforms: ['yahoo_shopping', 'mercari', 'ebay']
        },
        created_at: new Date().toISOString()
      })
      .select()
      .single();

    if (insertError) {
      console.error('[TASK_CREATE] Database insert error:', insertError);
      return NextResponse.json({
        success: false,
        error: 'タスクの作成に失敗しました'
      }, { status: 500 });
    }

    console.log('[TASK_CREATE] Task created successfully:', task.id);

    // バックグラウンドで統合検索エンジンを使用した検索を実行
    setImmediate(async () => {
      try {
        console.log('[TASK_CREATE] Starting background unified search for task:', task.id);
        
        // タスクステータスを実行中に更新
        await supabase
          .from('search_tasks')
          .update({ 
            status: 'running',
            updated_at: new Date().toISOString()
          })
          .eq('id', task.id);

        // 統合検索エンジンを使用した実際の検索
        console.log('[TASK_CREATE] Executing unified search with engine');
        
        const unifiedResult = await executeUnifiedJanSearch(cleanJanCode);
        console.log('[TASK_CREATE] Unified search completed:', {
          success: unifiedResult.success,
          totalResults: unifiedResult.total_results,
          finalCount: unifiedResult.final_results?.length || 0
        });

        // 統合検索結果をタスク結果形式に変換
        const searchResults = {
          integrated_results: {
            count: unifiedResult.final_results?.length || 0,
            items: unifiedResult.final_results || []
          },
          platform_results: unifiedResult.platform_results || {
            yahoo_shopping: [],
            mercari: [],
            ebay: []
          },
          summary: unifiedResult.summary || {
            total_found: 0,
            after_deduplication: 0,
            final_count: 0,
            execution_time_ms: 0
          }
        };

        // タスク完了
        await supabase
          .from('search_tasks')
          .update({
            status: 'completed',
            result: searchResults,
            completed_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          })
          .eq('id', task.id);

        console.log('[TASK_CREATE] Background unified search completed for task:', task.id);

      } catch (backgroundError) {
        console.error('[TASK_CREATE] Background unified search error:', backgroundError);
        
        // エラー時のタスク更新
        await supabase
          .from('search_tasks')
          .update({
            status: 'failed',
            error: backgroundError instanceof Error ? backgroundError.message : 'Unknown error',
            updated_at: new Date().toISOString()
          })
          .eq('id', task.id);
      }
    });

    // 即座にレスポンスを返す
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
    console.error('[TASK_CREATE] Unexpected error:', error);
    return NextResponse.json({
      success: false,
      error: 'サーバーエラーが発生しました'
    }, { status: 500 });
  }
}

/**
 * タスク一覧取得
 */
export async function GET() {
  console.log('[TASK_CREATE] GET request received');
  
  try {
    const { data: tasks, error } = await supabase
      .from('search_tasks')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('[TASK_CREATE] Database select error:', error);
      return NextResponse.json({
        success: false,
        error: 'タスクの取得に失敗しました'
      }, { status: 500 });
    }

    console.log('[TASK_CREATE] Retrieved tasks:', tasks?.length || 0);

    return NextResponse.json({
      success: true,
      tasks: tasks || []
    });

  } catch (error) {
    console.error('[TASK_CREATE] Unexpected error:', error);
    return NextResponse.json({
      success: false,
      error: 'サーバーエラーが発生しました'
    }, { status: 500 });
  }
}
