import { NextRequest, NextResponse } from 'next/server';
import { getProfitResults, getProfitResultsCount } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    // URLパラメータを取得
    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '50');
    const sortBy = searchParams.get('sortBy') || 'profit_amount';
    const sortOrder = (searchParams.get('sortOrder') || 'desc') as 'asc' | 'desc';
    const platform = searchParams.get('platform') || undefined;
    const minProfit = searchParams.get('minProfit') ? parseInt(searchParams.get('minProfit')!) : undefined;
    const maxProfit = searchParams.get('maxProfit') ? parseInt(searchParams.get('maxProfit')!) : undefined;
    const search = searchParams.get('search') || undefined;

    // オフセットを計算
    const offset = (page - 1) * limit;

    // データを取得
    const { data, count } = await getProfitResults({
      sortBy,
      sortOrder,
      platform,
      minProfit,
      maxProfit,
      limit,
      offset,
    });

    // 検索フィルタリング（クライアントサイド）
    let filteredData = data;
    if (search) {
      const searchLower = search.toLowerCase();
      filteredData = data.filter(
        (item) =>
          item.title?.toLowerCase().includes(searchLower) ||
          item.artist?.toLowerCase().includes(searchLower)
      );
    }

    // 総数を取得
    let totalCount = count || 0;
    if (totalCount === 0) {
      const countResult = await getProfitResultsCount({
        platform,
        minProfit,
        maxProfit,
      });
      totalCount = countResult || 0;
    }

    // 総ページ数を計算
    const totalPages = Math.ceil(totalCount / limit) || 1;

    // レスポンスを返す
    return NextResponse.json({
      data: filteredData,
      pagination: {
        page,
        limit,
        totalItems: totalCount,
        totalPages,
      },
    });
  } catch (error) {
    console.error('Error fetching profit results:', error);
    return NextResponse.json(
      { error: 'Failed to fetch profit results' },
      { status: 500 }
    );
  }
}
