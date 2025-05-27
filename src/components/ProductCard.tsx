import React from 'react';

interface ProductCardProps {
  product: {
    item_id?: string;
    item_title?: string;
    title?: string;
    item_url?: string;
    url?: string;
    image_url?: string;
    price?: number;
    total_price?: number;
    shipping_cost?: number;
    shipping_fee?: string;
    condition?: string;
    seller?: string;
    location?: string;
    platform?: string;
    currency?: string;
    description?: string;
    is_sold?: boolean;
  };
}

export default function ProductCard({ product }: ProductCardProps) {
  const title = product.item_title || product.title || '商品名なし';
  const url = product.item_url || product.url;
  const price = product.total_price || product.price;
  
  // プラットフォーム名を日本語に変換
  const getPlatformName = (platform: string) => {
    const platformNames: Record<string, string> = {
      'ebay': 'eBay',
      'mercari': 'メルカリ',
      'yahoo_auction': 'Yahoo!オークション',
      'yahoo': 'Yahoo!ショッピング',
      'paypay': 'PayPayフリマ',
      'rakuma': 'ラクマ',
      'discogs': 'Discogs'
    };
    return platformNames[platform] || platform;
  };

  // 価格を円でフォーマット
  const formatPrice = (price: number | undefined, currency?: string) => {
    if (!price) return '価格なし';
    
    if (currency === 'USD') {
      return `$${price.toLocaleString()}`;
    }
    return `¥${price.toLocaleString()}`;
  };

  // 送料の表示
  const getShippingInfo = () => {
    if (product.shipping_fee === '送料無料' || product.shipping_fee === '送料込み') {
      return true;
    }
    if (product.shipping_cost === 0) {
      return true;
    }
    return false;
  };

  // 商品の状態を表示用に変換
  const getConditionDisplay = (condition?: string) => {
    if (!condition || condition === '不明') return null;
    
    const conditionMap: Record<string, string> = {
      'new': '新品',
      'used': '中古',
      '未使用': '新品・未使用',
      '新品、未使用': '新品・未使用',
      '未使用に近い': '未使用に近い',
      '目立った傷や汚れなし': '美品',
      'やや傷や汚れあり': '中古',
      '傷や汚れあり': '中古（傷あり）',
      '全体的に状態が悪い': '難あり'
    };
    
    return conditionMap[condition] || condition;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow duration-200 h-full flex flex-col">
      {/* 商品画像 */}
      <div className="aspect-square bg-gray-50 relative">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={title}
            className="w-full h-full object-contain p-4"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              // エラー時はダミー画像アイコンを親要素に表示
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent && !parent.querySelector('svg')) {
                const placeholder = document.createElement('div');
                placeholder.className = 'w-full h-full flex items-center justify-center';
                placeholder.innerHTML = `
                  <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                `;
                parent.appendChild(placeholder);
              }
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
        
        {/* プラットフォームバッジ */}
        {product.platform && (
          <div className="absolute top-2 left-2">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
              {getPlatformName(product.platform)}
            </span>
          </div>
        )}
        
        {/* 売り切れバッジ */}
        {product.is_sold && (
          <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
            <span className="text-white font-bold text-lg">売り切れ</span>
          </div>
        )}
      </div>

      {/* 商品情報 */}
      <div className="p-4 flex-1 flex flex-col">
        {/* タイトル */}
        <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2 min-h-[2.5rem]">
          {url ? (
            <a 
              href={url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-blue-600 hover:underline"
            >
              {title}
            </a>
          ) : (
            title
          )}
        </h3>

        {/* 価格 */}
        <div className="mb-2">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold text-gray-900">
              {formatPrice(price, product.currency)}
            </span>
            {product.currency === 'USD' && price && (
              <span className="text-xs text-gray-500">
                (約¥{Math.round(price * 150).toLocaleString()})
              </span>
            )}
          </div>
          {getShippingInfo() && (
            <span className="text-xs text-green-600">送料無料</span>
          )}
        </div>

        {/* 商品状態 */}
        {getConditionDisplay(product.condition) && (
          <div className="mb-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
              {getConditionDisplay(product.condition)}
            </span>
          </div>
        )}

        {/* 販売者情報（小さく表示） */}
        <div className="mt-auto">
          {product.seller && product.seller !== '不明' && (
            <p className="text-xs text-gray-500 truncate">
              販売者: {product.seller}
            </p>
          )}
          {product.location && product.location !== '不明' && (
            <p className="text-xs text-gray-500 truncate">
              発送元: {product.location}
            </p>
          )}
        </div>

        {/* アクションボタン */}
        {url && (
          <div className="mt-3">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              詳細を見る
            </a>
          </div>
        )}
      </div>
    </div>
  );
}