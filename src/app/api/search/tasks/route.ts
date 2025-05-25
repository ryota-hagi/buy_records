import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// 環境変数の確認
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Supabase環境変数が設定されていません。NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYを確認してください。');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// JANコードから商品名を取得する関数
async function getProductNameFromJan(janCode: string): Promise<string> {
  try {
    const projectRoot = path.join(process.cwd(), '..');
    
    // Pythonスクリプトを実行して商品名を取得
    const command = `cd "${projectRoot}" && python -c "
import sys
import os
import warnings
warnings.filterwarnings('ignore')

# 標準エラー出力を無効化
sys.stderr = open(os.devnull, 'w')

sys.path.append('.')
from src.jan.jan_lookup import get_product_name_from_jan

try:
    product_name = get_product_name_from_jan('${janCode}')
    if product_name:
        print(product_name)
    else:
        print('商品 (JANコード: ${janCode})')
except Exception as e:
    print('商品 (JANコード: ${janCode})')
" 2>/dev/null`;

    const { stdout } = await execAsync(command);
    const productName = stdout.trim();
    
    return productName || `商品 (JANコード: ${janCode})`;
    
  } catch (error) {
    console.error('Error getting product name:', error);
    return `商品 (JANコード: ${janCode})`;
  }
}

// JANコード検索を実行する関数
async function executeJanSearch(janCode: string): Promise<any[]> {
  try {
    const projectRoot = path.join(process.cwd(), '..');
    
    // Pythonスクリプトを実行（標準エラー出力を無視し、JSONのみを出力）
    const command = `cd "${projectRoot}" && python -c "
import sys
import os
import json
import warnings
warnings.filterwarnings('ignore')

# 標準エラー出力を無効化
sys.stderr = open(os.devnull, 'w')

sys.path.append('.')
from src.jan.search_engine import JANSearchEngine

try:
    engine = JANSearchEngine()
    results = engine.search_by_jan('${janCode}', limit=20)
    print('JSON_START')
    print(json.dumps(results, ensure_ascii=False))
    print('JSON_END')
except Exception as e:
    print('JSON_START')
    print(json.dumps({'error': str(e)}, ensure_ascii=False))
    print('JSON_END')
" 2>/dev/null`;

    const { stdout, stderr } = await execAsync(command);
    
    if (!stdout.trim()) {
      throw new Error('No output from Python script');
    }
    
    // JSON部分のみを抽出
    const lines = stdout.split('\n');
    let jsonStartIndex = -1;
    let jsonEndIndex = -1;
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim() === 'JSON_START') {
        jsonStartIndex = i + 1;
      } else if (lines[i].trim() === 'JSON_END') {
        jsonEndIndex = i;
        break;
      }
    }
    
    if (jsonStartIndex === -1 || jsonEndIndex === -1) {
      // フォールバック: 最後の行がJSONかどうかチェック
      const lastLine = lines[lines.length - 1].trim();
      if (lastLine.startsWith('[') || lastLine.startsWith('{')) {
        try {
          const result = JSON.parse(lastLine);
          if (result.error) {
            throw new Error(result.error);
          }
          return Array.isArray(result) ? result : [];
        } catch (parseError) {
          throw new Error('Failed to parse search results');
        }
      }
      throw new Error('No valid JSON found in output');
    }
    
    const jsonLines = lines.slice(jsonStartIndex, jsonEndIndex);
    const jsonString = jsonLines.join('\n').trim();
    
    if (!jsonString) {
      throw new Error('Empty JSON output');
    }
    
    const result = JSON.parse(jsonString);
    
    if (result.error) {
      throw new Error(result.error);
    }
    
    return Array.isArray(result) ? result : [];
    
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

    // JANコードから商品名を取得
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
          message: 'タスクが作成されました'
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

// バックグラウンドでタスクを実行する関数
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
            message: '検索を開始しました'
          }
        ]
      })
      .eq('id', taskId);

    console.log(`Starting background search for task ${taskId}, JAN: ${janCode}`);

    // JANコード検索を実行
    const searchResults = await executeJanSearch(janCode);
    
    console.log(`Background search completed for task ${taskId}. Found ${searchResults.length} results`);

    // タスクを完了状態に更新
    await supabase
      .from('search_tasks')
      .update({
        status: 'completed',
        result: {
          integrated_results: {
            count: searchResults.length,
            items: searchResults
          }
        },
        completed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        processing_logs: [
          {
            timestamp: new Date().toISOString(),
            step: 'search_completed',
            status: 'success',
            message: `検索が完了しました（${searchResults.length}件の結果）`
          }
        ]
      })
      .eq('id', taskId);

    // 検索結果をsearch_resultsテーブルにも保存
    if (searchResults.length > 0) {
      const resultsData = searchResults.map(result => ({
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

      console.log(`Inserting ${resultsData.length} results into search_results table for task ${taskId}`);
      
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
            message: `検索に失敗しました: ${(error as Error).message}`
          }
        ]
      })
      .eq('id', taskId);
  }
}
