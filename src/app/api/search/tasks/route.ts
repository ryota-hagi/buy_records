import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import axios from 'axios';
import UnifiedJanSearchEngine from '../../../../jan/unified_search_engine';

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
  throw new Error('Supabase環境変数が設定されていません。NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// 統合JANコード検索を実行する関数（統合検索エンジン使用）
async function executeUnifiedJanSearch(janCode: string): Promise<SearchResponse> {
  try {
    console.log(`[UNIFIED] Starting unified JAN search for: ${janCode}`);
    
    // 統合検索エンジンのインスタンスを作成
    const searchEngine = new UnifiedJanSearchEngine();
    
    // 統合検索を実行
    const unifiedResult = await searchEngine.executeUnifiedJanSearch(janCode);
    
    if (!unifiedResult.success) {
      throw new Error('統合検索エンジンの実行に失敗しました');
    }
    
    console.log(`[UNIFIED] Search completed: ${unifiedResult.final_results.length} final results`);
    
    // レスポンス形式を既存の形式に合わせて変換
    const response: SearchResponse = {
      finalResults: unifiedResult.final_results,
      platformResults: {
        ebay: unifiedResult.platform_results.ebay,
        yahoo_shopping: unifiedResult.platform_results.yahoo_shopping,
        mercari: unifiedResult.platform_results.mercari
      },
      summary: {
        totalFound: unifiedResult.summary.total_found,
        afterDuplicateRemoval: unifiedResult.summary.after_deduplication,
        finalCount: unifiedResult.summary.final_count,
        cheapest: unifiedResult.final_results.length > 0 ? unifiedResult.final_results[0] : null,
        mostExpensive: unifiedResult.final_results.length > 0 ? 
          unifiedResult.final_results[unifiedResult.final_results.length - 1] : null,
        platformCounts: {
          ebay: unifiedResult.platform_results.ebay.length,
          yahoo_shopping: unifiedResult.platform_results.yahoo_shopping.length,
          mercari: unifiedResult.platform_results.mercari.length
        }
      }
    };
    
    console.log(`[UNIFIED] Response prepared: ${response.finalResults.length} items`);
    return response;
    
  } catch (error) {
    console.error('[UNIFIED] Error executing unified JAN search:', error);
    throw new Error(`統合検索の実行に失敗しました: ${(error as Error).message}`);
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

// POST: 新しい検索タスクを作成（統合検索エンジン使用）
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

    console.log(`Creating unified search task for JAN code: ${cleanJanCode}`);

    // まず商品名のみを取得（軽量な処理）
    const searchEngine = new UnifiedJanSearchEngine();
    let productName = `商品 (JANコード: ${cleanJanCode})`;
    
    try {
      // 商品名取得のみの軽量処理
      const tempResult = await searchEngine.executeUnifiedJanSearch(cleanJanCode);
      if (tempResult.success && tempResult.product_name) {
        productName = tempResult.product_name;
      }
    } catch (error) {
      console.warn('Product name fetch failed, using default name:', error);
    }

    // タスクをデータベースに作成（pending状態）
    const taskData = {
      name: productName,
      status: 'pending',
      search_params: {
        jan_code: cleanJanCode,
        platforms: ['yahoo_shopping', 'mercari', 'ebay']
      },
      processing_logs: [
        {
          timestamp: new Date().toISOString(),
          step: 'task_created',
          status: 'info',
          message: 'タスクが作成されました（統合検索エンジン版）'
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

    console.log(`Unified search task created: ${task.id}`);

    // バックグラウンドで統合検索を実行開始（実際の検索処理）
    executeUnifiedTaskInBackground(task.id, cleanJanCode).catch(error => {
      console.error(`Background unified task execution failed for task ${task.id}:`, error);
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
    console.error('Error creating unified search task:', error);
    return NextResponse.json(
      { error: 'タスクの作成中にエラーが発生しました: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

// バックグラウンドで統合検索タスクを実行する関数
async function executeUnifiedTaskInBackground(taskId: string, janCode: string) {
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
            step: 'unified_search_started',
            status: 'info',
            message: '統合検索エンジンによる検索を開始しました（Yahoo Shopping + メルカリ + eBay）'
          }
        ]
      })
      .eq('id', taskId);

    console.log(`Starting unified search for task ${taskId}, JAN: ${janCode}`);

    // 統合検索を実行
    const searchResult = await executeUnifiedJanSearch(janCode);
    
    console.log(`Unified search completed for task ${taskId}. Found ${searchResult.finalResults.length} results`);

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
            step: 'unified_search_completed',
            status: 'success',
            message: `統合検索が完了しました（${searchResult.finalResults.length}件の結果）- Yahoo: ${searchResult.summary.platformCounts.yahoo_shopping}件, メルカリ: ${searchResult.summary.platformCounts.mercari}件, eBay: ${searchResult.summary.platformCounts.ebay}件`
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

      console.log(`Inserting ${resultsData.length} unified search results into search_results table for task ${taskId}`);
      
      const { error: insertError } = await supabase
        .from('search_results')
        .insert(resultsData);
        
      if (insertError) {
        console.error(`Error inserting unified search results for task ${taskId}:`, insertError);
      } else {
        console.log(`Successfully inserted ${resultsData.length} unified search results for task ${taskId}`);
      }
    }

    console.log(`Unified search task ${taskId} completed successfully`);

  } catch (error) {
    console.error(`Error executing unified task ${taskId}:`, error);
    
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
            step: 'unified_search_failed',
            status: 'error',
            message: `統合検索に失敗しました: ${(error as Error).message}`
          }
        ]
      })
      .eq('id', taskId);
  }
}
