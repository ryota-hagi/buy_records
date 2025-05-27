# 統一検索インターフェース使用ガイド

## 概要

Buy Recordsプロジェクトの統一検索インターフェースは、全ての検索タイプ（JAN、商品名、画像、自然言語）に対応した柔軟で拡張可能な設計となっています。

## インターフェース構造

### 1. 検索リクエスト (`SearchRequest`)

```typescript
import { SearchRequest, SearchType, SortOption, ItemCondition } from '@/search/interfaces';

const request: SearchRequest = {
  // 必須フィールド
  searchType: SearchType.JAN_CODE,
  query: '4549660894254',
  
  // オプションフィールド
  filters: {
    minPrice: 1000,
    maxPrice: 50000,
    condition: [ItemCondition.NEW],
    sortBy: SortOption.PRICE_ASC
  },
  
  pagination: {
    page: 1,
    limit: 20
  },
  
  platforms: ['yahoo_shopping', 'mercari', 'ebay'],
  locale: 'ja-JP',
  currency: 'JPY',
  cacheEnabled: true,
  cacheTTL: 300
};
```

### 2. 検索レスポンス (`UnifiedSearchResponse`)

```typescript
interface UnifiedSearchResponse {
  success: boolean;
  searchType: SearchType;
  query: string;
  results: SearchResult[];
  totalResults: number;
  platformResults: Record<string, PlatformSearchResults>;
  pagination: PaginationInfo;
  summary: SearchSummary;
  metadata: SearchMetadata;
  errors?: SearchError[];
}
```

## 使用例

### 基本的な使用方法

```typescript
import { UnifiedSearchEngine } from '@/jan/unified_search_engine_v2';

const engine = new UnifiedSearchEngine();

// JANコード検索
const janResult = await engine.search({
  searchType: SearchType.JAN_CODE,
  query: '4549660894254'
});

// 商品名検索
const productResult = await engine.search({
  searchType: SearchType.PRODUCT_NAME,
  query: 'Nintendo Switch',
  filters: {
    minPrice: 30000,
    maxPrice: 50000
  }
});
```

### 高度な使用方法

```typescript
// フィルタリングとソート
const filteredResult = await engine.search({
  searchType: SearchType.KEYWORD,
  query: 'PlayStation 5',
  filters: {
    minPrice: 40000,
    maxPrice: 80000,
    condition: [ItemCondition.NEW, ItemCondition.LIKE_NEW],
    sortBy: SortOption.PRICE_ASC,
    includeShippingCost: true,
    onlyInStock: true
  },
  pagination: {
    page: 1,
    limit: 50
  },
  platforms: ['yahoo_shopping', 'mercari'],
  cacheEnabled: true,
  cacheTTL: 600, // 10分
  timeout: 30000  // 30秒
});

// 結果の処理
if (filteredResult.success) {
  console.log(`総結果数: ${filteredResult.totalResults}`);
  console.log(`価格範囲: ¥${filteredResult.summary.priceRange.min} - ¥${filteredResult.summary.priceRange.max}`);
  
  filteredResult.results.forEach(item => {
    console.log(`${item.title} - ¥${item.totalPrice} (${item.platform})`);
  });
} else {
  console.error('検索エラー:', filteredResult.errors);
}
```

## エラーハンドリング

統一されたエラーハンドリングシステムにより、エラーの種類に応じた適切な対処が可能です。

```typescript
const result = await engine.search(request);

if (!result.success && result.errors) {
  result.errors.forEach(error => {
    switch (error.code) {
      case 'API_RATE_LIMIT':
        console.log('API制限に達しました。しばらくお待ちください。');
        break;
      case 'NETWORK_ERROR':
        console.log('ネットワークエラーが発生しました。');
        break;
      default:
        console.log(`エラー: ${error.message}`);
    }
  });
}
```

## 検索タイプ

### 対応済み
- `JAN_CODE`: JANコード検索
- `PRODUCT_NAME`: 商品名検索
- `KEYWORD`: キーワード検索

### 今後実装予定
- `IMAGE`: 画像検索
- `NATURAL_LANGUAGE`: 自然言語検索
- `BARCODE`: バーコード検索
- `SKU`: SKU検索
- `CATEGORY`: カテゴリ検索

## フィルターオプション

- **価格フィルター**: `minPrice`, `maxPrice`
- **商品状態**: `NEW`, `LIKE_NEW`, `VERY_GOOD`, `GOOD`, `ACCEPTABLE`
- **配送オプション**: `FREE_SHIPPING`, `EXPEDITED`, `STANDARD`
- **ソート順**: `PRICE_ASC`, `PRICE_DESC`, `RELEVANCE`, `DATE_NEWEST`, `RATING`

## パフォーマンス最適化

1. **キャッシュ機能**
   - デフォルトで5分間のキャッシュ
   - `cacheEnabled`と`cacheTTL`で制御可能

2. **並行検索**
   - 全プラットフォームへの検索を並行実行
   - プラットフォーム個別のエラーは他の検索に影響しない

3. **レート制限対応**
   - 自動リトライ機能
   - エクスポネンシャルバックオフ

## 拡張性

新しいプラットフォームを追加する場合：

1. プラットフォーム設定を追加
2. 検索メソッドを実装
3. アイテムマッピングを定義

```typescript
// プラットフォーム設定追加
private platformConfigs: Record<string, PlatformConfig> = {
  // ... 既存設定
  new_platform: {
    enabled: true,
    priority: 4,
    timeout: 10000,
    maxRetries: 3,
    rateLimitDelay: 150
  }
};

// 検索メソッド実装
private async searchNewPlatform(
  query: string,
  limit: number,
  filters?: SearchFilters
): Promise<SearchResult[]> {
  // 実装
}
```