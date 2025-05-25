import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
const { JANSearchEngine } = require('../../../../lib/search-engine.js');

// 環境変数の確認
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase環境変数が設定されていません。NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// JANコードから商品名を取得する関数（Node.js版）
async function getProductNameFromJan(janCode: string): Promise<string> {
  try {
    const searchEngine = new JANSearchEngine();
    return searchEngine.getProductNameFromJan(janCode);
  } catch (error) {
    console.error('Error getting product name:', error);
    return `商品 (JANコード: ${janCode})`;
  }
}

// JANコード検索を実行する関数（Node.js版）
async function executeJanSearch(janCode: string): Promise<any> {
  try {
    console.log(`Starting Node.js search for JAN code: ${janCode}`);
    console.log(`Target: 20 items each from eBay, Yahoo Shopping, Mercari (60 total) → top 20 items`);
    
    const searchEngine = new JANSearchEngine();
    const searchResult = await searchEngine.searchByJan(janCode, 20);
    
    console.log(`Node.js search completed:`);
    console.log(`- Final results: ${searchResult.finalResults.length} items`);
    console.log(`- Platform counts: eBay ${searchResult.summary.platformCounts.ebay}, Yahoo ${searchResult.summary.platformCounts.yahoo_shopping}, Mercari ${searchResult.summary.platformCounts.mercari}`);
    console.log(`- Total found: ${searchResult.summary.totalFound} items`);
    
    return searchResult;
    
  } catch (error) {
    console.error('Error executing JAN search:', error);
    throw new Error(`検索の実行に失敗しました: ${(error as Error).message}`);
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

    console.log(`Creating search task for JAN code: ${cleanJanCode}`);

    // JANコードから商品名を取得（Node.js版）
    const productName = await getProductNameFromJan(cleanJanCode);

    // タスクをデータベースに作成（pending状態）
    const taskData = {
      name: productName,
      status: 'pending',
      search_params: {
        jan_code: cleanJanCode,
        platforms: ['mercari', 'yahoo_shopping', 'yahoo_auction', 'ebay']
      },
      processing_logs: [
        {
          timestamp: new Date().toISOString(),
          step: 'task_created',
          status: 'info',
          message: 'タスクが作成されました（Node.js版）'
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

    console.log(`Search task created: ${task.id}`);

    // バックグラウンドでタスクを実行開始
    // 非同期でタスクを実行（レスポンスを待たない）
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

// バックグラウンドでタスクを実行する関数（Node.js版）
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
            message: 'Node.js検索エンジンで検索を開始しました'
          }
        ]
      })
      .eq('id', taskId);

    console.log(`Starting background search for task ${taskId}, JAN: ${janCode}`);

    // JANコード検索を実行（Node.js版）
    const searchResult = await executeJanSearch(janCode);
    
    console.log(`Background search completed for task ${taskId}. Found ${searchResult.finalResults.length} final results from ${searchResult.summary.totalFound} total`);

    // タスクを完了状態に更新（プラットフォーム別結果とサマリーを含む）
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
            message: `Node.js検索エンジンで検索が完了しました（${searchResult.finalResults.length}件の最終結果、${searchResult.summary.totalFound}件の総取得数）`
          }
        ]
      })
      .eq('id', taskId);

    // 検索結果をsearch_resultsテーブルにも保存（最終結果のみ）
    if (searchResult.finalResults.length > 0) {
      const resultsData = searchResult.finalResults.map((result: any) => ({
        task_id: taskId,
        platform: result.platform || 'unknown',
        item_title: result.item_title || result.title || '',
        item_url: result.item_url || result.url || '',
        item_image_url: result.item_image_url || result.image_url || '',
        base_price: result.price || 0,
        total_price: result.total_price || result.price || 0,
        shipping_fee: result.shipping_cost || 0,
        item_condition: result.condition || '',
        seller_name: result.seller || ''
      }));

      console.log(`Inserting ${resultsData.length} final results into search_results table for task ${taskId}`);
      
      const { error: insertError } = await supabase
        .from('search_results')
        .insert(resultsData);
        
      if (insertError) {
        console.error(`Error inserting search results for task ${taskId}:`, insertError);
      } else {
        console.log(`Successfully inserted ${resultsData.length} search results for task ${taskId}`);
      }
    }

    console.log(`Task ${taskId} completed successfully`);

  } catch (error) {
    console.error(`Error executing background task ${taskId}:`, error);
    
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
            message: `Node.js検索エンジンで検索に失敗しました: ${(error as Error).message}`
          }
        ]
      })
      .eq('id', taskId);
  }
}
