import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

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

    const { jan_code, product_name } = body;

    // パラメータのバリデーション
    if (!jan_code && !product_name) {
      console.error('[TASK_CREATE] No search parameters provided');
      return NextResponse.json({
        success: false,
        error: 'JANコードまたは商品名が必要です'
      }, { status: 400 });
    }

    let cleanJanCode = '';
    let cleanProductName = '';
    let taskName = '';

    if (jan_code) {
      // JANコードのバリデーション
      if (typeof jan_code !== 'string') {
        console.error('[TASK_CREATE] Invalid JAN code type:', typeof jan_code);
        return NextResponse.json({
          success: false,
          error: 'JANコードは文字列である必要があります'
        }, { status: 400 });
      }

      cleanJanCode = jan_code.trim().replace(/[^0-9]/g, '');
      if (cleanJanCode.length !== 13 && cleanJanCode.length !== 8) {
        console.error('[TASK_CREATE] Invalid JAN code length:', cleanJanCode.length);
        return NextResponse.json({
          success: false,
          error: 'JANコードは8桁または13桁の数字である必要があります'
        }, { status: 400 });
      }
      
      console.log('[TASK_CREATE] Creating task for JAN code:', cleanJanCode);
      taskName = `商品検索 (JANコード: ${cleanJanCode})`;
    } else if (product_name) {
      // 商品名のバリデーション
      if (typeof product_name !== 'string' || !product_name.trim()) {
        console.error('[TASK_CREATE] Invalid product name:', product_name);
        return NextResponse.json({
          success: false,
          error: '有効な商品名を入力してください'
        }, { status: 400 });
      }
      
      cleanProductName = product_name.trim();
      console.log('[TASK_CREATE] Creating task for product name:', cleanProductName);
      taskName = `商品検索 (商品名: ${cleanProductName})`;
    }
    
    // Supabaseにタスクを作成
    const searchParams = cleanJanCode 
      ? { jan_code: cleanJanCode, platforms: ['yahoo_shopping', 'mercari', 'ebay'] }
      : { product_name: cleanProductName, platforms: ['yahoo_shopping', 'mercari', 'ebay'] };
      
    const { data: task, error: insertError } = await supabase
      .from('search_tasks')
      .insert({
        name: taskName,
        status: 'pending',
        search_params: searchParams,
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

        // 統合検索APIを使用（4プラットフォーム対応）
        console.log('[TASK_CREATE] Executing unified search via /api/search/all');
        
        const baseUrl = process.env.NODE_ENV === 'production' 
          ? 'https://buy-records.vercel.app' 
          : `http://localhost:${process.env.PORT || 3000}`;
        
        const searchParams = new URLSearchParams();
        if (cleanJanCode) {
          searchParams.append('jan_code', cleanJanCode);
        } else {
          searchParams.append('product_name', cleanProductName);
        }
        searchParams.append('limit', '80'); // 各プラットフォーム20件ずつ
        
        const searchResponse = await fetch(`${baseUrl}/api/search/all?${searchParams.toString()}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (!searchResponse.ok) {
          throw new Error(`Search API failed: ${searchResponse.status}`);
        }
        
        const searchData = await searchResponse.json();
        
        console.log('[TASK_CREATE] Unified search completed:', {
          success: searchData.success,
          totalResults: searchData.total_results,
          platformCounts: Object.entries(searchData.platforms || {}).reduce((acc, [platform, items]) => {
            acc[platform] = (items as any[]).length;
            return acc;
          }, {} as Record<string, number>)
        });

        // 結果データを構築（要件通りの形式）
        const resultData = {
          integrated_results: {
            success: searchData.success,
            product_name: searchData.query || taskName,
            total_results: searchData.total_results,
            items: searchData.results || [], // 統合された結果（価格順）
            platform_results: searchData.platforms || {}, // 各プラットフォーム別結果
            summary: {
              total_found: searchData.total_results,
              after_deduplication: searchData.total_results,
              final_count: searchData.results ? searchData.results.length : 0,
              execution_time_ms: 0
            }
          }
        };

        // 商品名を更新（検索結果から取得）
        if (searchData.success && searchData.query && 
            searchData.query !== taskName && 
            !searchData.query.includes('JANコード:')) {
          await supabase
            .from('search_tasks')
            .update({ 
              name: searchData.query,
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
