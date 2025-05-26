import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { UnifiedJanSearchEngineFinal } from '../../../../jan/unified_search_engine_final';

// Supabaseクライアント初期化
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * 統合検索エンジン使用版タスク作成API
 * 要件: eBay、メルカリ、Yahoo!ショッピングから各20件取得 → 60件を安い順ソート → 最終20件
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

    // デフォルトのタスク名
    let taskName = `商品検索 (JANコード: ${cleanJanCode})`;
    
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

    // バックグラウンドで統合検索を実行
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

        // 新しい統合検索エンジンを直接使用
        console.log('[TASK_CREATE] Executing unified search engine');
        
        const searchEngine = new UnifiedJanSearchEngineFinal();
        const searchResults = await searchEngine.executeUnifiedJanSearch(cleanJanCode);
        
        console.log('[TASK_CREATE] Unified search completed:', {
          success: searchResults.success,
          totalResults: searchResults.total_results,
          finalCount: searchResults.final_results.length,
          platformCounts: {
            yahoo: searchResults.platform_results.yahoo_shopping.length,
            mercari: searchResults.platform_results.mercari.length,
            ebay: searchResults.platform_results.ebay.length
          }
        });

        // 結果データを構築（要件通りの形式）
        const resultData = {
          integrated_results: {
            success: searchResults.success,
            product_name: searchResults.product_name,
            total_results: searchResults.total_results,
            items: searchResults.final_results, // 最終20件（安い順ソート済み）
            platform_results: searchResults.platform_results, // 各プラットフォーム別結果
            summary: searchResults.summary
          }
        };

        // 商品名を更新（検索結果から取得）
        if (searchResults.success && searchResults.product_name && 
            searchResults.product_name !== taskName && 
            !searchResults.product_name.includes('JANコード:')) {
          await supabase
            .from('search_tasks')
            .update({ 
              name: searchResults.product_name,
              updated_at: new Date().toISOString()
            })
            .eq('id', task.id);
        }

        // タスク完了
        await supabase
          .from('search_tasks')
          .update({
            status: 'completed',
            result: resultData,
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
            error_message: backgroundError instanceof Error ? backgroundError.message : 'Unknown error',
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
