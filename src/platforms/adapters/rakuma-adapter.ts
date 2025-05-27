/**
 * Rakuma Platform Adapter
 * ラクマのプラットフォームアダプター実装
 */

export interface RakumaSearchResult {
  platform: string;
  title: string;
  url: string;
  image_url: string;
  price: number;
  shipping_fee: number;
  total_price: number;
  condition: string;
  store_name: string;
  location: string;
  currency: string;
  item_id?: string;
  seller_name?: string;
  is_sold?: boolean;
}

export interface RakumaSearchParams {
  product_name?: string;
  jan_code?: string;
  query?: string;
  limit?: number;
}

export class RakumaAdapter {
  private readonly platform = 'rakuma';
  private readonly baseUrl = 'https://fril.jp';

  /**
   * 商品状態を正規化
   */
  normalizeCondition(condition: string): string {
    const conditionMap: { [key: string]: string } = {
      '新品、未使用': '新品',
      '未使用に近い': '未使用に近い',
      '目立った傷や汚れなし': '目立った傷や汚れなし',
      'やや傷や汚れあり': 'やや傷や汚れあり',
      '傷や汚れあり': '傷や汚れあり',
      '全体的に状態が悪い': '全体的に状態が悪い',
    };

    // 正規化
    for (const [key, value] of Object.entries(conditionMap)) {
      if (condition.includes(key)) {
        return value;
      }
    }

    return condition || '中古';
  }

  /**
   * 検索結果を統一フォーマットに変換
   */
  transformResult(item: any): RakumaSearchResult {
    return {
      platform: this.platform,
      title: item.title || '',
      url: item.url || '',
      image_url: item.image_url || '',
      price: parseInt(item.price) || 0,
      shipping_fee: item.shipping_fee || 0,
      total_price: (parseInt(item.price) || 0) + (item.shipping_fee || 0),
      condition: this.normalizeCondition(item.condition || ''),
      store_name: item.seller_name || 'ラクマ',
      location: item.location || '日本',
      currency: 'JPY',
      item_id: item.item_id,
      seller_name: item.seller_name,
      is_sold: item.is_sold || false,
    };
  }

  /**
   * 検索クエリを構築
   */
  buildSearchQuery(params: RakumaSearchParams): string {
    if (params.product_name) {
      return params.product_name;
    } else if (params.jan_code) {
      return params.jan_code;
    } else if (params.query) {
      return params.query;
    }
    throw new Error('検索パラメータが不足しています');
  }

  /**
   * レート制限の遅延時間を取得（ミリ秒）
   */
  getRateLimitDelay(): number {
    // 2秒から3秒のランダムな遅延
    return 2000 + Math.random() * 1000;
  }

  /**
   * 検索URLを構築
   */
  buildSearchUrl(query: string): string {
    const encodedQuery = encodeURIComponent(query);
    return `${this.baseUrl}/s?query=${encodedQuery}&sort=price_asc&status=1`;
  }

  /**
   * 売り切れ商品の検索URLを構築
   */
  buildSoldSearchUrl(query: string): string {
    const encodedQuery = encodeURIComponent(query);
    return `${this.baseUrl}/s?query=${encodedQuery}&sort=created_at_desc&status=2`;
  }
}

export default RakumaAdapter;