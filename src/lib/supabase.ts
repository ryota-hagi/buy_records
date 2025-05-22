import { createClient } from '@supabase/supabase-js';

// 環境変数からSupabaseの接続情報を取得
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Supabaseクライアントを作成
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 利益計算結果を取得する関数
export async function getProfitResults(options: {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  platform?: string;
  minProfit?: number;
  maxProfit?: number;
  limit?: number;
  offset?: number;
}) {
  const {
    sortBy = 'profit_amount',
    sortOrder = 'desc',
    platform,
    minProfit,
    maxProfit,
    limit = 50,
    offset = 0,
  } = options;

  // クエリを構築
  let query = supabase
    .from('price_comparison_results')
    .select('*')
    .order(sortBy, { ascending: sortOrder === 'asc' })
    .range(offset, offset + limit - 1);

  // フィルタリング条件を追加
  if (platform) {
    query = query.or(`best_source_platform.eq.${platform},best_target_platform.eq.${platform}`);
  }

  if (minProfit !== undefined) {
    query = query.gte('profit_amount', minProfit);
  }

  if (maxProfit !== undefined) {
    query = query.lte('profit_amount', maxProfit);
  }

  // クエリを実行
  const { data, error, count } = await query;

  if (error) {
    console.error('Error fetching profit results:', error);
    throw error;
  }

  return { data, count };
}

// 利益計算結果の総数を取得する関数
export async function getProfitResultsCount(options: {
  platform?: string;
  minProfit?: number;
  maxProfit?: number;
}) {
  const { platform, minProfit, maxProfit } = options;

  // クエリを構築
  let query = supabase
    .from('price_comparison_results')
    .select('*', { count: 'exact', head: true });

  // フィルタリング条件を追加
  if (platform) {
    query = query.or(`best_source_platform.eq.${platform},best_target_platform.eq.${platform}`);
  }

  if (minProfit !== undefined) {
    query = query.gte('profit_amount', minProfit);
  }

  if (maxProfit !== undefined) {
    query = query.lte('profit_amount', maxProfit);
  }

  // クエリを実行
  const { count, error } = await query;

  if (error) {
    console.error('Error fetching profit results count:', error);
    throw error;
  }

  return count;
}

// 利用可能なプラットフォームのリストを取得する関数
export async function getAvailablePlatforms() {
  // ソースプラットフォームを取得
  const { data: sourcePlatforms, error: sourceError } = await supabase
    .from('price_comparison_results')
    .select('best_source_platform');

  if (sourceError) {
    console.error('Error fetching source platforms:', sourceError);
    throw sourceError;
  }

  // ターゲットプラットフォームを取得
  const { data: targetPlatforms, error: targetError } = await supabase
    .from('price_comparison_results')
    .select('best_target_platform');

  if (targetError) {
    console.error('Error fetching target platforms:', targetError);
    throw targetError;
  }

  // プラットフォームのセットを作成
  const platformSet = new Set<string>();
  
  sourcePlatforms.forEach((item: { best_source_platform: string | null }) => {
    if (item.best_source_platform) {
      platformSet.add(item.best_source_platform);
    }
  });
  
  targetPlatforms.forEach((item: { best_target_platform: string | null }) => {
    if (item.best_target_platform) {
      platformSet.add(item.best_target_platform);
    }
  });

  // 配列に変換して返す
  return Array.from(platformSet);
}
