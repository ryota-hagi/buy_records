#!/usr/bin/env node

// Supabase MCPを使用してsearch_tasksテーブルを作成するスクリプト
const dotenv = require('dotenv');
dotenv.config();

async function main() {
  try {
    // 環境変数からSupabase接続情報を取得
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      console.error('Supabase接続情報が設定されていません。.envファイルを確認してください。');
      process.exit(1);
    }

    console.log('Supabase MCPを使用してsearch_tasksテーブルを作成します...');

    // テーブル作成SQL
    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS public.search_tasks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
        search_params JSONB NOT NULL,
        result JSONB,
        error TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        completed_at TIMESTAMP WITH TIME ZONE
      );
    `;
    
    // インデックス作成SQL
    const createIndexSQL = `
      CREATE INDEX IF NOT EXISTS search_tasks_status_idx ON public.search_tasks (status);
      CREATE INDEX IF NOT EXISTS search_tasks_created_at_idx ON public.search_tasks (created_at DESC);
    `;
    
    // RLSポリシー設定SQL
    const createRLSSQL = `
      ALTER TABLE public.search_tasks ENABLE ROW LEVEL SECURITY;
      DROP POLICY IF EXISTS "Allow anonymous select" ON public.search_tasks;
      CREATE POLICY "Allow anonymous select" ON public.search_tasks FOR SELECT USING (true);
      DROP POLICY IF EXISTS "Allow anonymous insert" ON public.search_tasks;
      CREATE POLICY "Allow anonymous insert" ON public.search_tasks FOR INSERT WITH CHECK (true);
      DROP POLICY IF EXISTS "Allow anonymous update" ON public.search_tasks;
      CREATE POLICY "Allow anonymous update" ON public.search_tasks FOR UPDATE USING (true);
      DROP POLICY IF EXISTS "Allow anonymous delete" ON public.search_tasks;
      CREATE POLICY "Allow anonymous delete" ON public.search_tasks FOR DELETE USING (true);
    `;
    
    // 更新トリガー作成SQL
    const createTriggerSQL = `
      CREATE OR REPLACE FUNCTION update_updated_at_column()
      RETURNS TRIGGER AS $$
      BEGIN
          NEW.updated_at = now();
          RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;

      DROP TRIGGER IF EXISTS update_search_tasks_updated_at ON public.search_tasks;
      CREATE TRIGGER update_search_tasks_updated_at
      BEFORE UPDATE ON public.search_tasks
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at_column();
    `;

    // Supabase MCPを使用してSQLを実行
    const response = await fetch(`${supabaseUrl}/rest/v1/rpc/execute_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        query: createTableSQL
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('テーブル作成エラー:', errorData);
      process.exit(1);
    }

    console.log('テーブルを作成しました');

    // インデックスを作成
    const indexResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/execute_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        query: createIndexSQL
      })
    });

    if (!indexResponse.ok) {
      const errorData = await indexResponse.json();
      console.error('インデックス作成エラー:', errorData);
      // エラーがあっても続行
    } else {
      console.log('インデックスを作成しました');
    }

    // RLSポリシーを設定
    const rlsResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/execute_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        query: createRLSSQL
      })
    });

    if (!rlsResponse.ok) {
      const errorData = await rlsResponse.json();
      console.error('RLSポリシー設定エラー:', errorData);
      // エラーがあっても続行
    } else {
      console.log('RLSポリシーを設定しました');
    }

    // 更新トリガーを作成
    const triggerResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/execute_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        query: createTriggerSQL
      })
    });

    if (!triggerResponse.ok) {
      const errorData = await triggerResponse.json();
      console.error('更新トリガー作成エラー:', errorData);
      // エラーがあっても続行
    } else {
      console.log('更新トリガーを作成しました');
    }

    console.log('search_tasksテーブルの作成が完了しました');
  } catch (error) {
    console.error('エラーが発生しました:', error);
    process.exit(1);
  }
}

main();
