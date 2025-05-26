import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Supabaseクライアント初期化
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// GET: 特定のタスクの詳細と検索結果を取得
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: taskId } = await params;

    if (!taskId) {
      return NextResponse.json(
        { error: 'タスクIDが必要です' },
        { status: 400 }
      );
    }

    // タスク情報を取得
    const { data: task, error: taskError } = await supabase
      .from('search_tasks')
      .select('*')
      .eq('id', taskId)
      .single();

    if (taskError) {
      if (taskError.code === 'PGRST116') {
        return NextResponse.json(
          { error: 'タスクが見つかりません' },
          { status: 404 }
        );
      }
      console.error('Database query error:', taskError);
      return NextResponse.json(
        { error: 'タスクの取得に失敗しました' },
        { status: 500 }
      );
    }

    // タスクのresultフィールドから結果を取得（新しい形式）
    let mappedResults: any[] = [];
    
    if (task.result && task.result.integrated_results && task.result.integrated_results.items) {
      mappedResults = task.result.integrated_results.items;
    }

    // レスポンスデータを構築
    const response = {
      ...task,
      results: mappedResults,
      results_count: mappedResults.length,
      // 統計情報を追加
      stats: mappedResults.length > 0 ? {
        min_price: Math.min(...mappedResults.filter(r => r.total_price).map(r => r.total_price)),
        max_price: Math.max(...mappedResults.filter(r => r.total_price).map(r => r.total_price)),
        avg_price: mappedResults.filter(r => r.total_price).reduce((sum, r) => sum + r.total_price, 0) / mappedResults.filter(r => r.total_price).length,
        platforms: [...new Set(mappedResults.map(r => r.platform))],
        platform_counts: mappedResults.reduce((acc, r) => {
          acc[r.platform] = (acc[r.platform] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      } : null
    };

    return NextResponse.json({
      success: true,
      task: response
    });

  } catch (error) {
    console.error('Error fetching task details:', error);
    return NextResponse.json(
      { error: '内部サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}

// DELETE: タスクをキャンセルまたは削除
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: taskId } = await params;
    const url = new URL(request.url);
    const action = url.searchParams.get('action') || 'cancel';

    if (!taskId) {
      return NextResponse.json(
        { error: 'タスクIDが必要です' },
        { status: 400 }
      );
    }

    // タスクの現在のステータスを確認
    const { data: task, error: fetchError } = await supabase
      .from('search_tasks')
      .select('status')
      .eq('id', taskId)
      .single();

    if (fetchError) {
      if (fetchError.code === 'PGRST116') {
        return NextResponse.json(
          { error: 'タスクが見つかりません' },
          { status: 404 }
        );
      }
      console.error('Database query error:', fetchError);
      return NextResponse.json(
        { error: 'タスクの取得に失敗しました' },
        { status: 500 }
      );
    }

    if (action === 'delete') {
      // 完全削除の場合
      const { error: taskDeleteError } = await supabase
        .from('search_tasks')
        .delete()
        .eq('id', taskId);

      if (taskDeleteError) {
        console.error('Error deleting task:', taskDeleteError);
        return NextResponse.json(
          { error: 'タスクの削除に失敗しました' },
          { status: 500 }
        );
      }

      return NextResponse.json({
        success: true,
        message: 'タスクが削除されました'
      });
    } else {
      // キャンセルの場合
      if (!task || ['completed', 'failed', 'cancelled'].includes(task.status)) {
        return NextResponse.json(
          { error: 'このタスクはキャンセルできません' },
          { status: 400 }
        );
      }

      // ステータスをキャンセルに更新
      const { data: updatedTask, error: updateError } = await supabase
        .from('search_tasks')
        .update({ 
          status: 'cancelled',
          updated_at: new Date().toISOString()
        })
        .eq('id', taskId)
        .select()
        .single();

      if (updateError) {
        console.error('Database update error:', updateError);
        return NextResponse.json(
          { error: 'タスクのキャンセルに失敗しました' },
          { status: 500 }
        );
      }

      return NextResponse.json({
        success: true,
        message: 'タスクがキャンセルされました',
        task: updatedTask
      });
    }

  } catch (error) {
    console.error('Error processing task:', error);
    return NextResponse.json(
      { error: '内部サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}

// PUT: タスクステータスを更新（システム内部用）
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: taskId } = await params;
    const body = await request.json();
    const { status, error_message } = body;

    if (!taskId) {
      return NextResponse.json(
        { error: 'タスクIDが必要です' },
        { status: 400 }
      );
    }

    if (!status) {
      return NextResponse.json(
        { error: 'ステータスが必要です' },
        { status: 400 }
      );
    }

    // 有効なステータスかチェック
    const validStatuses = ['pending', 'running', 'completed', 'failed', 'cancelled'];
    if (!validStatuses.includes(status)) {
      return NextResponse.json(
        { error: '無効なステータスです' },
        { status: 400 }
      );
    }

    // 更新データを準備
    const updateData: any = {
      status,
      updated_at: new Date().toISOString()
    };

    if (status === 'completed') {
      updateData.completed_at = new Date().toISOString();
    }

    if (status === 'failed' && error_message) {
      updateData.error_message = error_message;
    }

    // タスクを更新
    const { data: updatedTask, error: updateError } = await supabase
      .from('search_tasks')
      .update(updateData)
      .eq('id', taskId)
      .select()
      .single();

    if (updateError) {
      console.error('Database update error:', updateError);
      return NextResponse.json(
        { error: 'タスクの更新に失敗しました' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      task: updatedTask
    });

  } catch (error) {
    console.error('Error updating task:', error);
    return NextResponse.json(
      { error: '内部サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
