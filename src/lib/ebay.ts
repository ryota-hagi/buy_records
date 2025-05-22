/**
 * eBay API用のユーティリティ関数
 */

// eBay APIのベースURL
const EBAY_API_BASE_URL = 'https://api.ebay.com';

// eBay APIのエンドポイント
const ENDPOINTS = {
  FIND_ITEMS: '/services/search/FindingService/v1',
  GET_ITEM: '/buy/browse/v1/item',
  GET_ITEM_DETAILS: '/buy/browse/v1/item/{item_id}',
};

/**
 * eBay APIリクエスト用のヘッダーを生成
 */
export const getEbayHeaders = () => {
  return {
    'X-EBAY-API-IAF-TOKEN': process.env.EBAY_USER_TOKEN || '',
    'X-EBAY-API-APP-ID': process.env.EBAY_APP_ID || '',
    'Content-Type': 'application/json',
  };
};

/**
 * eBay APIを使用して商品を検索
 * @param keyword 検索キーワード
 * @param limit 取得件数
 * @param page ページ番号
 */
export const searchEbayItems = async (
  keyword: string,
  limit: number = 10,
  page: number = 1
) => {
  try {
    const url = `${EBAY_API_BASE_URL}${ENDPOINTS.FIND_ITEMS}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: getEbayHeaders(),
      body: JSON.stringify({
        'findItemsByKeywordsRequest': {
          'keywords': keyword,
          'paginationInput': {
            'entriesPerPage': limit,
            'pageNumber': page,
          },
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`eBay API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error searching eBay items:', error);
    throw error;
  }
};

/**
 * eBay APIを使用して商品詳細を取得
 * @param itemId 商品ID
 */
export const getEbayItemDetails = async (itemId: string) => {
  try {
    const url = `${EBAY_API_BASE_URL}${ENDPOINTS.GET_ITEM_DETAILS.replace('{item_id}', itemId)}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: getEbayHeaders(),
    });

    if (!response.ok) {
      throw new Error(`eBay API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting eBay item details:', error);
    throw error;
  }
};

/**
 * eBay APIトークンの有効期限をチェック
 * @returns トークンが有効かどうか
 */
export const isEbayTokenValid = (): boolean => {
  const tokenExpiry = process.env.EBAY_TOKEN_EXPIRY;
  if (!tokenExpiry) return false;
  
  const expiryDate = new Date(tokenExpiry);
  const now = new Date();
  
  return expiryDate > now;
};
