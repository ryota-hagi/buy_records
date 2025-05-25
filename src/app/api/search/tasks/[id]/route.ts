import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// 環境変数の確認
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase環境変数が設定されていません。NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

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

    // 検索結果を取得（総額でソート、最大20件）
    const { data: results, error: resultsError } = await supabase
      .from('search_results')
      .select('*')
      .eq('task_id', taskId)
      .order('total_price', { ascending: true })
      .limit(20);

    if (resultsError) {
      console.error('Database query error:', resultsError);
      return NextResponse.json(
        { error: '検索結果の取得に失敗しました' },
        { status: 500 }
      );
    }

    let mappedResults: any[] = [];

    // search_resultsテーブルにデータがある場合
    if (results && results.length > 0) {
      mappedResults = results.map(result => ({
        ...result,
        title: result.item_title,
        url: result.item_url,
        image_url: result.item_image_url,
        condition: result.item_condition,
        item_price: result.base_price,
        shipping_cost: result.shipping_fee,
        // 既存のフィールドも保持
        item_title: result.item_title,
        item_url: result.item_url,
        item_image_url: result.item_image_url,
        item_condition: result.item_condition
      }));
    } 
    // search_resultsテーブルにデータがない場合は空の配列を返す
    // 古いresultフィールドからのデータ取得は無効化（モックデータ防止）
    else {
      console.log('search_resultsテーブルにデータがないため、空の結果を返します');
      mappedResults = [];
    }

    // レスポンスデータを構築
    const response = {
      ...task,
      results: mappedResults,
      results_count: mappedResults.length,
      // 統計情報を追加
      stats: mappedResults.length > 0 ? {
        min_price: Math.min(...mappedResults.map(r => r.total_price)),
        max_price: Math.max(...mappedResults.map(r => r.total_price)),
        avg_price: mappedResults.reduce((sum, r) => sum + r.total_price, 0) / mappedResults.length,
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
      // 関連する検索結果も削除
      const { error: resultsDeleteError } = await supabase
        .from('search_results')
        .delete()
        .eq('task_id', taskId);

      if (resultsDeleteError) {
        console.error('Error deleting search results:', resultsDeleteError);
        return NextResponse.json(
          { error: '検索結果の削除に失敗しました' },
          { status: 500 }
        );
      }

      // タスクを削除
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
      // キャンセルの場合（既存の処理）
      // キャンセル可能なステータスかチェック
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
