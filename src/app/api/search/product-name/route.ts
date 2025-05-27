import { NextRequest, NextResponse } from 'next/server';

interface SearchResult {
  platform: string;
  title: string;
  url: string;
  image_url: string;
  price: number;
  shipping_fee?: number;
  total_price: number;
  condition: string;
  store_name: string;
  location: string;
  currency: string;
  relevance_score?: number;
  [key: string]: unknown;
}

// レーベンシュタイン距離を計算する関数
function levenshteinDistance(str1: string, str2: string): number {
  const m = str1.length;
  const n = str2.length;
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 0; i <= m; i++) {
    dp[i][0] = i;
  }
  for (let j = 0; j <= n; j++) {
    dp[0][j] = j;
  }

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (str1[i - 1] === str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }

  return dp[m][n];
}

// 関連性スコアを計算する関数
function calculateRelevanceScore(productName: string, itemTitle: string): number {
  // 両方を小文字に変換して比較
  const normalizedProductName = productName.toLowerCase().trim();
  const normalizedItemTitle = itemTitle.toLowerCase().trim();

  // 完全一致
  if (normalizedItemTitle === normalizedProductName) {
    return 100;
  }

  // 商品名が完全に含まれている
  if (normalizedItemTitle.includes(normalizedProductName)) {
    return 90;
  }

  // 各単語が含まれているかチェック
  const productWords = normalizedProductName.split(/\s+/);
  const titleWords = normalizedItemTitle.split(/\s+/);
  
  let matchedWords = 0;
  const totalWords = productWords.length;
  
  for (const word of productWords) {
    if (titleWords.some(titleWord => titleWord.includes(word) || word.includes(titleWord))) {
      matchedWords++;
    }
  }
  
  const wordMatchScore = (matchedWords / totalWords) * 70;

  // レーベンシュタイン距離による類似度
  const maxLength = Math.max(normalizedProductName.length, normalizedItemTitle.length);
  const distance = levenshteinDistance(normalizedProductName, normalizedItemTitle);
  const similarityScore = (1 - distance / maxLength) * 30;

  return Math.round(wordMatchScore + similarityScore);
}

async function searchByProductName(productName: string, limit: number = 50) {
  const baseUrl = process.env.NODE_ENV === 'production' 
    ? 'https://buy-records.vercel.app' 
    : `http://localhost:${process.env.PORT || 3000}`;
  
  console.log(`商品名検索開始: ${productName}`);

  const platforms = [
    { name: 'yahoo_shopping', endpoint: '/api/search/yahoo' },
    { name: 'ebay', endpoint: '/api/search/ebay' },
    { name: 'mercari', endpoint: '/api/search/mercari' }
  ];

  const results: SearchResult[] = [];
  const errors: string[] = [];
  const platformMetadata: Record<string, unknown> = {};

  // 並行検索実行
  const searchPromises = platforms.map(async (platform) => {
    try {
      const controller = new AbortController();
      // Mercariの視覚スクレイピングは時間がかかるため、タイムアウトを延長
      const timeout = platform.name === 'mercari' ? 45000 : 15000;
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      // product_nameパラメータを使用
      const params = new URLSearchParams();
      params.append('product_name', productName);
      params.append('limit', limit.toString());
      
      const response = await fetch(`${baseUrl}${platform.endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.results) {
          // 各結果に関連性スコアを追加
          const resultsWithScore = data.results.map((item: SearchResult) => ({
            ...item,
            relevance_score: calculateRelevanceScore(productName, item.title)
          }));
          
          results.push(...resultsWithScore);
          console.log(`${platform.name}: ${data.results.length}件取得`);
          
          // メタデータを保存
          if (data.metadata || data.scraping_method) {
            platformMetadata[platform.name] = {
              metadata: data.metadata,
              scraping_method: data.scraping_method,
              data_source: data.data_source,
              total_results: data.total_results
            };
          }
        } else {
          errors.push(`${platform.name}: ${data.error || 'Unknown error'}`);
          console.error(`${platform.name} APIエラー:`, data.error);
        }
      } else {
        errors.push(`${platform.name}: HTTP ${response.status}`);
        console.error(`${platform.name} HTTPエラー:`, response.status);
      }
    } catch (error) {
      errors.push(`${platform.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error(`${platform.name} 検索エラー:`, error);
    }
  });

  await Promise.allSettled(searchPromises);

  // 結果を関連性スコアと価格でソート
  results.sort((a, b) => {
    // まず関連性スコアの高い順
    const scoreDiff = (b.relevance_score || 0) - (a.relevance_score || 0);
    if (scoreDiff !== 0) {
      return scoreDiff;
    }
    // 同じスコアの場合は価格順
    return (a.total_price || a.price || 0) - (b.total_price || b.price || 0);
  });

  // プラットフォーム別の結果を集計
  const platformResults: { [key: string]: SearchResult[] } = {};
  for (const result of results) {
    if (!platformResults[result.platform]) {
      platformResults[result.platform] = [];
    }
    platformResults[result.platform].push(result);
  }

  // 総コストを計算
  let totalEstimatedCost = 0;
  if (platformMetadata.mercari?.metadata?.cost_tracking) {
    totalEstimatedCost += platformMetadata.mercari.metadata.cost_tracking.estimated_cost || 0;
  }

  // 関連性スコアの統計情報
  const relevanceStats = {
    high_relevance: results.filter(r => (r.relevance_score || 0) >= 80).length,
    medium_relevance: results.filter(r => (r.relevance_score || 0) >= 50 && (r.relevance_score || 0) < 80).length,
    low_relevance: results.filter(r => (r.relevance_score || 0) < 50).length,
    average_score: results.length > 0 
      ? Math.round(results.reduce((sum, r) => sum + (r.relevance_score || 0), 0) / results.length)
      : 0
  };

  return {
    success: true,
    search_type: 'product_name',
    query: productName,
    total_results: results.length,
    results: results.slice(0, limit), // 制限数まで
    platforms: platformResults, // プラットフォーム別結果
    platforms_searched: platforms.length,
    platform_metadata: platformMetadata, // 各プラットフォームのメタデータ
    relevance_stats: relevanceStats, // 関連性統計
    cost_summary: {
      total_estimated_cost: totalEstimatedCost,
      currency: 'USD',
      details: platformMetadata.mercari?.metadata?.cost_tracking || null
    },
    errors: errors.length > 0 ? errors : undefined,
    timestamp: new Date().toISOString()
  };
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const productName = searchParams.get('product_name');
    const limit = parseInt(searchParams.get('limit') || '50');
    
    if (!productName) {
      return NextResponse.json(
        { error: 'product_nameパラメータが必要です' },
        { status: 400 }
      );
    }

    const response = await searchByProductName(productName, limit);
    console.log(`商品名検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('商品名検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '商品名検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_name, limit = 50 } = body;
    
    if (!product_name) {
      return NextResponse.json(
        { error: 'product_nameが必要です' },
        { status: 400 }
      );
    }

    const response = await searchByProductName(product_name, limit);
    console.log(`商品名検索完了: ${response.results.length}件`);
    return NextResponse.json(response);

  } catch (error) {
    console.error('商品名検索エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '商品名検索中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}