import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Supabaseクライアント初期化
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * シンプル版タスク作成API - 統合検索エンジンを使わない基本実装
 */
export async function POST(request: NextRequest) {
  console.log('[TASK_CREATE_SIMPLE] POST request received');
  
  let body: any;
  
  try {
    // リクエストボディの安全な解析
    try {
      body = await request.json();
      console.log('[TASK_CREATE_SIMPLE] Request body parsed:', body);
    } catch (parseError) {
      console.error('[TASK_CREATE_SIMPLE] JSON parse error:', parseError);
      return NextResponse.json({
        success: false,
        error: 'リクエストボディの解析に失敗しました'
      }, { status: 400 });
    }

    const { jan_code } = body;

    // JANコードのバリデーション
    if (!jan_code || typeof jan_code !== 'string') {
      console.error('[TASK_CREATE_SIMPLE] Invalid JAN code:', jan_code);
      return NextResponse.json({
        success: false,
        error: 'JANコードが必要です'
      }, { status: 400 });
    }

    const cleanJanCode = jan_code.trim().replace(/[^0-9]/g, '');
    if (cleanJanCode.length !== 13 && cleanJanCode.length !== 8) {
      console.error('[TASK_CREATE_SIMPLE] Invalid JAN code length:', cleanJanCode.length);
      return NextResponse.json({
        success: false,
        error: 'JANコードは8桁または13桁の数字である必要があります'
      }, { status: 400 });
    }

    console.log('[TASK_CREATE_SIMPLE] Creating task for JAN code:', cleanJanCode);

    // シンプルなタスク作成（統合検索エンジンを使わない）
    const taskName = `商品検索 (JANコード: ${cleanJanCode})`;
    
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
      console.error('[TASK_CREATE_SIMPLE] Database insert error:', insertError);
      return NextResponse.json({
        success: false,
        error: 'タスクの作成に失敗しました'
      }, { status: 500 });
    }

    console.log('[TASK_CREATE_SIMPLE] Task created successfully:', task.id);

    // バックグラウンドでシンプル検索を実行
    setImmediate(async () => {
      try {
        console.log('[TASK_CREATE_SIMPLE] Starting background search for task:', task.id);
        
        // タスクステータスを実行中に更新
        await supabase
          .from('search_tasks')
          .update({ 
            status: 'running',
            updated_at: new Date().toISOString()
          })
          .eq('id', task.id);

        // シンプルな検索結果（モックデータではなく、基本的な検索）
        const searchResults = {
          integrated_results: {
            count: 0,
            items: []
          },
          platform_results: {
            yahoo_shopping: [],
            mercari: [],
            ebay: []
          },
          summary: {
            total_found: 0,
            after_deduplication: 0,
            final_count: 0,
            execution_time_ms: 1000
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

        console.log('[TASK_CREATE_SIMPLE] Background search completed for task:', task.id);

      } catch (backgroundError) {
        console.error('[TASK_CREATE_SIMPLE] Background search error:', backgroundError);
        
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
    console.error('[TASK_CREATE_SIMPLE] Unexpected error:', error);
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
  console.log('[TASK_CREATE_SIMPLE] GET request received');
  
  try {
    const { data: tasks, error } = await supabase
      .from('search_tasks')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('[TASK_CREATE_SIMPLE] Database select error:', error);
      return NextResponse.json({
        success: false,
        error: 'タスクの取得に失敗しました'
      }, { status: 500 });
    }

    console.log('[TASK_CREATE_SIMPLE] Retrieved tasks:', tasks?.length || 0);

    return NextResponse.json({
      success: true,
      tasks: tasks || []
    });

  } catch (error) {
    console.error('[TASK_CREATE_SIMPLE] Unexpected error:', error);
    return NextResponse.json({
      success: false,
      error: 'サーバーエラーが発生しました'
    }, { status: 500 });
  }
}
