import { NextRequest, NextResponse } from 'next/server';
import { getEbayItemDetails, isEbayTokenValid } from '@/lib/ebay';

/**
 * eBay商品詳細API
 * @route GET /api/ebay/item/[id]
 * @param id - 商品ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // トークンの有効性をチェック
    if (!isEbayTokenValid()) {
      return NextResponse.json(
        { error: 'eBay API token is expired or not configured' },
        { status: 401 }
      );
    }

    const itemId = params.id;

    // 商品IDが指定されていない場合はエラー
    if (!itemId) {
      return NextResponse.json(
        { error: 'Item ID is required' },
        { status: 400 }
      );
    }

    // eBay APIを使用して商品詳細を取得
    const result = await getEbayItemDetails(itemId);

    // 結果を返す
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in eBay item details API:', error);
    return NextResponse.json(
      { error: 'Failed to get eBay item details' },
      { status: 500 }
    );
  }
}
