import { NextRequest, NextResponse } from 'next/server';
import { searchEbayItems, isEbayTokenValid } from '@/lib/ebay';

/**
 * eBay商品検索API
 * @route GET /api/ebay/search
 * @query keyword - 検索キーワード
 * @query limit - 取得件数（デフォルト: 10）
 * @query page - ページ番号（デフォルト: 1）
 */
export async function GET(request: NextRequest) {
  try {
    // トークンの有効性をチェック
    if (!isEbayTokenValid()) {
      return NextResponse.json(
        { error: 'eBay API token is expired or not configured' },
        { status: 401 }
      );
    }

    // クエリパラメータを取得
    const { searchParams } = new URL(request.url);
    const keyword = searchParams.get('keyword');
    const limit = parseInt(searchParams.get('limit') || '10', 10);
    const page = parseInt(searchParams.get('page') || '1', 10);

    // キーワードが指定されていない場合はエラー
    if (!keyword) {
      return NextResponse.json(
        { error: 'Keyword parameter is required' },
        { status: 400 }
      );
    }

    // eBay APIを使用して商品を検索
    const result = await searchEbayItems(keyword, limit, page);

    // 結果を返す
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in eBay search API:', error);
    return NextResponse.json(
      { error: 'Failed to search eBay items' },
      { status: 500 }
    );
  }
}
