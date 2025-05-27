import axios, { AxiosError } from 'axios';
import {
  SearchRequest,
  SearchType,
  SearchFilters,
  SortOption,
  ItemCondition,
  Pagination
} from '../search/interfaces/search-request';
import {
  SearchResult,
  UnifiedSearchResponse,
  PlatformSearchResults,
  SearchSummary,
  SearchMetadata,
  SearchError,
  SellerInfo,
  ShippingInfo,
  ProductImage
} from '../search/interfaces/search-response';
import {
  BaseError,
  ErrorSeverity,
  ErrorCategory,
  ApiError,
  ErrorHandler,
  ErrorHandlingResult,
  ErrorAggregator
} from '../search/interfaces/error-handling';

/**
 * キャッシュエントリの型定義
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

/**
 * プラットフォーム設定
 */
interface PlatformConfig {
  enabled: boolean;
  priority: number;
  timeout: number;
  maxRetries: number;
  rateLimitDelay: number;
}

/**
 * 統合検索エンジン
 * 全検索タイプ（JAN、商品名、画像、自然言語）に対応
 */
export class UnifiedSearchEngine implements ErrorHandler {
  private readonly GOOGLE_TRANSLATE_API_KEY: string;
  private readonly YAHOO_SHOPPING_APP_ID: string;
  private readonly EBAY_APP_ID: string;
  private cache: Map<string, CacheEntry<any>> = new Map();
  private readonly DEFAULT_CACHE_TTL = 5 * 60 * 1000; // 5分
  private errorAggregator: ErrorAggregator;
  
  // プラットフォーム設定
  private platformConfigs: Record<string, PlatformConfig> = {
    yahoo_shopping: {
      enabled: true,
      priority: 1,
      timeout: 8000,
      maxRetries: 3,
      rateLimitDelay: 100
    },
    mercari: {
      enabled: true,
      priority: 2,
      timeout: 10000,
      maxRetries: 2,
      rateLimitDelay: 200
    },
    ebay: {
      enabled: true,
      priority: 3,
      timeout: 8000,
      maxRetries: 3,
      rateLimitDelay: 100
    }
  };

  constructor() {
    // 環境変数を取得
    this.GOOGLE_TRANSLATE_API_KEY = process.env.GOOGLE_TRANSLATE_API_KEY || '';
    this.YAHOO_SHOPPING_APP_ID = process.env.YAHOO_SHOPPING_APP_ID || process.env.YAHOO_APP_ID || '';
    this.EBAY_APP_ID = process.env.EBAY_APP_ID || '';
    
    // エラーアグリゲーターの初期化
    this.errorAggregator = this.createErrorAggregator();
    
    // 環境変数のバリデーション
    this.validateConfiguration();
  }

  /**
   * 統一検索インターフェース
   */
  public async search(request: SearchRequest): Promise<UnifiedSearchResponse> {
    const startTime = Date.now();
    const metadata = this.createSearchMetadata(request);
    
    try {
      // リクエストのバリデーション
      this.validateSearchRequest(request);
      
      // キャッシュチェック
      const cacheKey = this.generateCacheKey(request);
      const cachedResult = this.getFromCache<UnifiedSearchResponse>(cacheKey);
      if (cachedResult && request.cacheEnabled !== false) {
        return cachedResult;
      }
      
      // 検索タイプに応じた処理
      let response: UnifiedSearchResponse;
      
      switch (request.searchType) {
        case SearchType.JAN_CODE:
          response = await this.searchByJanCode(request, metadata);
          break;
        case SearchType.PRODUCT_NAME:
        case SearchType.KEYWORD:
          response = await this.searchByKeyword(request, metadata);
          break;
        case SearchType.IMAGE:
          response = await this.searchByImage(request, metadata);
          break;
        case SearchType.NATURAL_LANGUAGE:
          response = await this.searchByNaturalLanguage(request, metadata);
          break;
        default:
          throw this.createError(
            ErrorCategory.INVALID_SEARCH_TYPE,
            `Unsupported search type: ${request.searchType}`,
            ErrorSeverity.ERROR
          );
      }
      
      // キャッシュに保存
      if (request.cacheEnabled !== false) {
        this.saveToCache(cacheKey, response, request.cacheTTL);
      }
      
      return response;
      
    } catch (error) {
      return this.handleSearchError(error, request, metadata, Date.now() - startTime);
    }
  }

  /**
   * JANコード検索
   */
  private async searchByJanCode(
    request: SearchRequest,
    metadata: SearchMetadata
  ): Promise<UnifiedSearchResponse> {
    const janCode = request.query;
    console.log(`[UNIFIED] Starting JAN code search for: ${janCode}`);
    
    // JANコードから商品名を特定
    const productName = await this.getProductNameFromJan(janCode);
    
    // 並行検索実行
    const platformResults = await this.executePlatformSearches(productName, janCode, request);
    
    // 結果の統合と処理
    return this.processSearchResults(platformResults, request, metadata, productName);
  }

  /**
   * キーワード検索
   */
  private async searchByKeyword(
    request: SearchRequest,
    metadata: SearchMetadata
  ): Promise<UnifiedSearchResponse> {
    const keyword = request.query;
    console.log(`[UNIFIED] Starting keyword search for: ${keyword}`);
    
    // 並行検索実行
    const platformResults = await this.executePlatformSearches(keyword, null, request);
    
    // 結果の統合と処理
    return this.processSearchResults(platformResults, request, metadata, keyword);
  }

  /**
   * 画像検索（未実装）
   */
  private async searchByImage(
    request: SearchRequest,
    metadata: SearchMetadata
  ): Promise<UnifiedSearchResponse> {
    throw this.createError(
      ErrorCategory.UNSUPPORTED_OPERATION,
      'Image search is not yet implemented',
      ErrorSeverity.ERROR
    );
  }

  /**
   * 自然言語検索（未実装）
   */
  private async searchByNaturalLanguage(
    request: SearchRequest,
    metadata: SearchMetadata
  ): Promise<UnifiedSearchResponse> {
    throw this.createError(
      ErrorCategory.UNSUPPORTED_OPERATION,
      'Natural language search is not yet implemented',
      ErrorSeverity.ERROR
    );
  }

  /**
   * プラットフォーム横断検索の実行
   */
  private async executePlatformSearches(
    query: string,
    janCode: string | null,
    request: SearchRequest
  ): Promise<Record<string, PlatformSearchResults>> {
    const platforms = request.platforms || Object.keys(this.platformConfigs);
    const limit = request.pagination?.limit || 20;
    
    // 有効なプラットフォームのみフィルタリング
    const enabledPlatforms = platforms.filter(
      p => this.platformConfigs[p]?.enabled
    );
    
    // 並行検索実行
    const searchPromises = enabledPlatforms.map(async (platform) => {
      const startTime = Date.now();
      try {
        let results: SearchResult[] = [];
        
        switch (platform) {
          case 'yahoo_shopping':
            results = await this.searchYahooShopping(janCode || query, query, limit, request.filters);
            break;
          case 'mercari':
            results = await this.searchMercari(query, limit, request.filters);
            break;
          case 'ebay':
            results = await this.searchEbay(query, limit, request.filters);
            break;
        }
        
        return {
          platform,
          result: {
            platform,
            results,
            totalCount: results.length,
            hasMore: results.length >= limit,
            searchTime: Date.now() - startTime
          } as PlatformSearchResults
        };
      } catch (error) {
        // プラットフォーム個別のエラーをログに記録
        const platformError = this.createPlatformError(error, platform);
        this.errorAggregator.add(platformError);
        
        return {
          platform,
          result: {
            platform,
            results: [],
            totalCount: 0,
            hasMore: false,
            searchTime: Date.now() - startTime,
            error: {
              code: platformError.code,
              message: platformError.message,
              platform,
              timestamp: new Date(),
              recoverable: platformError.recoverable
            } as SearchError
          } as PlatformSearchResults
        };
      }
    });
    
    const results = await Promise.all(searchPromises);
    
    // 結果をオブジェクトに変換
    return results.reduce((acc, { platform, result }) => {
      acc[platform] = result;
      return acc;
    }, {} as Record<string, PlatformSearchResults>);
  }

  /**
   * Yahoo Shopping検索
   */
  private async searchYahooShopping(
    janCode: string,
    productName: string,
    limit: number,
    filters?: SearchFilters
  ): Promise<SearchResult[]> {
    if (!this.YAHOO_SHOPPING_APP_ID) {
      throw this.createError(
        ErrorCategory.CONFIGURATION_ERROR,
        'Yahoo Shopping API key not configured',
        ErrorSeverity.WARNING
      );
    }

    try {
      const params: any = {
        appid: this.YAHOO_SHOPPING_APP_ID,
        results: limit,
        sort: this.mapSortOption(filters?.sortBy)
      };

      // JANコード検索を優先
      if (this.isValidJanCode(janCode)) {
        params.jan_code = janCode;
      } else {
        params.query = productName;
      }

      // フィルター適用
      if (filters?.minPrice) params.price_from = filters.minPrice;
      if (filters?.maxPrice) params.price_to = filters.maxPrice;

      const response = await axios.get(
        'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch',
        { params, timeout: this.platformConfigs.yahoo_shopping.timeout }
      );

      const items = response.data?.hits || [];
      return items.map((item: any) => this.mapYahooItem(item, janCode));

    } catch (error) {
      throw this.handleApiError(error, 'yahoo_shopping');
    }
  }

  /**
   * メルカリ検索
   */
  private async searchMercari(
    query: string,
    limit: number,
    filters?: SearchFilters
  ): Promise<SearchResult[]> {
    // 実装が必要
    console.log(`[MERCARI] Search not implemented yet for: ${query}`);
    return [];
  }

  /**
   * eBay検索
   */
  private async searchEbay(
    query: string,
    limit: number,
    filters?: SearchFilters
  ): Promise<SearchResult[]> {
    if (!this.EBAY_APP_ID) {
      throw this.createError(
        ErrorCategory.CONFIGURATION_ERROR,
        'eBay API key not configured',
        ErrorSeverity.WARNING
      );
    }

    try {
      // 日本語を英語に翻訳
      const translatedQuery = await this.translateToEnglish(query);

      const params: any = {
        'OPERATION-NAME': 'findItemsByKeywords',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': this.EBAY_APP_ID,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': translatedQuery,
        'paginationInput.entriesPerPage': limit
      };

      // フィルター適用
      let filterIndex = 0;
      if (filters?.minPrice) {
        params[`itemFilter(${filterIndex}).name`] = 'MinPrice';
        params[`itemFilter(${filterIndex}).value`] = filters.minPrice;
        filterIndex++;
      }
      if (filters?.maxPrice) {
        params[`itemFilter(${filterIndex}).name`] = 'MaxPrice';
        params[`itemFilter(${filterIndex}).value`] = filters.maxPrice;
        filterIndex++;
      }

      const response = await axios.get(
        'https://svcs.ebay.com/services/search/FindingService/v1',
        { params, timeout: this.platformConfigs.ebay.timeout }
      );

      const items = response.data?.findItemsByKeywordsResponse?.[0]?.searchResult?.[0]?.item || [];
      return items.map((item: any) => this.mapEbayItem(item));

    } catch (error) {
      throw this.handleApiError(error, 'ebay');
    }
  }

  /**
   * 検索結果の処理と統合
   */
  private processSearchResults(
    platformResults: Record<string, PlatformSearchResults>,
    request: SearchRequest,
    metadata: SearchMetadata,
    productName: string
  ): UnifiedSearchResponse {
    // 全結果を統合
    const allResults: SearchResult[] = [];
    Object.values(platformResults).forEach(pr => {
      allResults.push(...pr.results);
    });

    // 重複除去
    const deduplicatedResults = this.removeDuplicates(allResults);

    // フィルタリング
    const filteredResults = this.applyFilters(deduplicatedResults, request.filters);

    // ソート
    const sortedResults = this.sortResults(filteredResults, request.filters?.sortBy);

    // ページネーション適用
    const paginatedResults = this.applyPagination(sortedResults, request.pagination);

    // サマリー生成
    const summary = this.generateSummary(
      allResults,
      filteredResults,
      deduplicatedResults,
      paginatedResults.results,
      metadata
    );

    return {
      success: true,
      searchType: request.searchType,
      query: request.query,
      results: paginatedResults.results,
      totalResults: filteredResults.length,
      platformResults,
      pagination: paginatedResults.pagination,
      summary,
      metadata,
      errors: this.errorAggregator.errors.map(e => ({
        code: e.code,
        message: e.message,
        platform: e.platform,
        timestamp: e.timestamp,
        recoverable: e.recoverable,
        details: e.details
      } as SearchError))
    };
  }

  /**
   * アイテムマッピング: Yahoo
   */
  private mapYahooItem(item: any, janCode?: string): SearchResult {
    return {
      id: `yahoo_shopping_${item.code}`,
      platform: 'yahoo_shopping',
      itemId: item.code,
      title: item.name || '',
      description: item.description,
      url: item.url || '',
      price: parseInt(item.price || '0'),
      currency: 'JPY',
      shippingCost: 0,
      totalPrice: parseInt(item.price || '0'),
      taxIncluded: true,
      condition: ItemCondition.NEW,
      images: [{
        url: item.image?.medium || item.image?.small || '',
        isPrimary: true
      }],
      janCode: janCode || item.janCode,
      seller: {
        id: item.store?.code || '',
        name: item.store?.name || '',
        url: item.store?.url
      } as SellerInfo,
      shippingOptions: [],
      rating: item.review ? {
        average: parseFloat(item.review.rate || '0'),
        count: parseInt(item.review.count || '0')
      } : undefined
    };
  }

  /**
   * アイテムマッピング: eBay
   */
  private mapEbayItem(item: any): SearchResult {
    const price = parseFloat(item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__ || '0');
    const shippingCost = parseFloat(
      item.shippingInfo?.[0]?.shippingServiceCost?.[0]?.__value__ || '0'
    );

    return {
      id: `ebay_${item.itemId?.[0]}`,
      platform: 'ebay',
      itemId: item.itemId?.[0] || '',
      title: item.title?.[0] || '',
      url: item.viewItemURL?.[0] || '',
      price,
      currency: item.sellingStatus?.[0]?.currentPrice?.[0]?.['@currencyId'] || 'USD',
      shippingCost,
      totalPrice: price + shippingCost,
      taxIncluded: false,
      condition: this.mapEbayCondition(item.condition?.[0]?.conditionId?.[0]),
      images: [{
        url: item.galleryURL?.[0] || '',
        isPrimary: true
      }],
      seller: {
        id: item.sellerInfo?.[0]?.sellerUserName?.[0] || '',
        name: item.sellerInfo?.[0]?.sellerUserName?.[0] || '',
        rating: parseFloat(item.sellerInfo?.[0]?.feedbackScore?.[0] || '0')
      } as SellerInfo,
      shippingOptions: [{
        method: item.shippingInfo?.[0]?.shippingType?.[0] || 'Standard',
        cost: shippingCost,
        currency: 'USD'
      } as ShippingInfo]
    };
  }

  /**
   * 条件マッピング
   */
  private mapEbayCondition(conditionId?: string): ItemCondition {
    const conditionMap: Record<string, ItemCondition> = {
      '1000': ItemCondition.NEW,
      '1500': ItemCondition.NEW,
      '2000': ItemCondition.LIKE_NEW,
      '3000': ItemCondition.VERY_GOOD,
      '4000': ItemCondition.GOOD,
      '5000': ItemCondition.ACCEPTABLE
    };
    return conditionMap[conditionId || ''] || ItemCondition.GOOD;
  }

  /**
   * ソートオプションのマッピング
   */
  private mapSortOption(sortOption?: SortOption): string {
    const sortMap: Record<SortOption, string> = {
      [SortOption.PRICE_ASC]: 'price',
      [SortOption.PRICE_DESC]: '-price',
      [SortOption.RELEVANCE]: 'score',
      [SortOption.DATE_NEWEST]: '-update',
      [SortOption.DATE_OLDEST]: 'update',
      [SortOption.POPULARITY]: '-review_count',
      [SortOption.RATING]: '-review_rate',
      [SortOption.SHIPPING_COST]: 'shipping'
    };
    return sortOption ? sortMap[sortOption] || 'score' : 'score';
  }

  /**
   * 重複除去
   */
  private removeDuplicates(results: SearchResult[]): SearchResult[] {
    const seen = new Set<string>();
    return results.filter((item) => {
      const key = `${item.title.toLowerCase()}-${item.price}-${item.platform}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  /**
   * フィルター適用
   */
  private applyFilters(
    results: SearchResult[],
    filters?: SearchFilters
  ): SearchResult[] {
    if (!filters) return results;

    return results.filter(item => {
      // 価格フィルター
      if (filters.minPrice && item.totalPrice < filters.minPrice) return false;
      if (filters.maxPrice && item.totalPrice > filters.maxPrice) return false;

      // 状態フィルター
      if (filters.condition && filters.condition.length > 0) {
        if (!filters.condition.includes(item.condition) && 
            !filters.condition.includes(ItemCondition.ANY)) {
          return false;
        }
      }

      // 販売者フィルター
      if (filters.sellers && filters.sellers.length > 0) {
        if (!filters.sellers.includes(item.seller.name)) return false;
      }
      if (filters.excludeSellers && filters.excludeSellers.length > 0) {
        if (filters.excludeSellers.includes(item.seller.name)) return false;
      }

      return true;
    });
  }

  /**
   * 結果のソート
   */
  private sortResults(
    results: SearchResult[],
    sortBy?: SortOption
  ): SearchResult[] {
    if (!sortBy) sortBy = SortOption.PRICE_ASC;

    const sorted = [...results];
    
    switch (sortBy) {
      case SortOption.PRICE_ASC:
        sorted.sort((a, b) => a.totalPrice - b.totalPrice);
        break;
      case SortOption.PRICE_DESC:
        sorted.sort((a, b) => b.totalPrice - a.totalPrice);
        break;
      case SortOption.DATE_NEWEST:
        sorted.sort((a, b) => {
          const dateA = a.listingDate?.getTime() || 0;
          const dateB = b.listingDate?.getTime() || 0;
          return dateB - dateA;
        });
        break;
      case SortOption.RATING:
        sorted.sort((a, b) => {
          const ratingA = a.rating?.average || 0;
          const ratingB = b.rating?.average || 0;
          return ratingB - ratingA;
        });
        break;
      case SortOption.SHIPPING_COST:
        sorted.sort((a, b) => a.shippingCost - b.shippingCost);
        break;
    }

    return sorted;
  }

  /**
   * ページネーション適用
   */
  private applyPagination(
    results: SearchResult[],
    pagination?: Pagination
  ): { results: SearchResult[], pagination: any } {
    const page = pagination?.page || 1;
    const limit = pagination?.limit || 20;
    const offset = pagination?.offset || (page - 1) * limit;

    const paginatedResults = results.slice(offset, offset + limit);
    const totalPages = Math.ceil(results.length / limit);

    return {
      results: paginatedResults,
      pagination: {
        page,
        limit,
        totalPages,
        hasNext: page < totalPages,
        hasPrevious: page > 1
      }
    };
  }

  /**
   * サマリー生成
   */
  private generateSummary(
    allResults: SearchResult[],
    filteredResults: SearchResult[],
    deduplicatedResults: SearchResult[],
    finalResults: SearchResult[],
    metadata: SearchMetadata
  ): SearchSummary {
    const prices = finalResults.map(r => r.totalPrice).filter(p => p > 0);
    const platformCounts: Record<string, number> = {};
    const conditionCounts: Record<ItemCondition, number> = {} as any;

    finalResults.forEach(result => {
      // プラットフォーム別カウント
      platformCounts[result.platform] = (platformCounts[result.platform] || 0) + 1;
      
      // 状態別カウント
      conditionCounts[result.condition] = (conditionCounts[result.condition] || 0) + 1;
    });

    return {
      totalFound: allResults.length,
      afterFiltering: filteredResults.length,
      afterDeduplication: deduplicatedResults.length,
      finalCount: finalResults.length,
      priceRange: prices.length > 0 ? {
        min: Math.min(...prices),
        max: Math.max(...prices),
        average: prices.reduce((a, b) => a + b, 0) / prices.length,
        median: this.calculateMedian(prices)
      } : {
        min: 0,
        max: 0,
        average: 0,
        median: 0
      },
      platformCounts,
      conditionCounts,
      executionTimeMs: Date.now() - metadata.timestamp.getTime()
    };
  }

  /**
   * 中央値計算
   */
  private calculateMedian(numbers: number[]): number {
    if (numbers.length === 0) return 0;
    const sorted = [...numbers].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];
  }

  /**
   * JANコードから商品名を取得
   */
  private async getProductNameFromJan(janCode: string): Promise<string> {
    try {
      // Yahoo Shopping APIで商品名を取得
      if (this.YAHOO_SHOPPING_APP_ID) {
        const response = await axios.get(
          'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch',
          {
            params: {
              appid: this.YAHOO_SHOPPING_APP_ID,
              jan_code: janCode,
              results: 1,
              output: 'json'
            },
            timeout: 5000
          }
        );

        const items = response.data?.hits || [];
        if (items.length > 0 && items[0].name) {
          return items[0].name;
        }
      }

      return `商品 (JANコード: ${janCode})`;
    } catch (error) {
      console.warn(`[PRODUCT_NAME] Failed to get name for JAN: ${janCode}`, error);
      return `商品 (JANコード: ${janCode})`;
    }
  }

  /**
   * 英語翻訳
   */
  private async translateToEnglish(text: string): Promise<string> {
    if (!this.GOOGLE_TRANSLATE_API_KEY) {
      return text;
    }

    try {
      const response = await axios.post(
        `https://translation.googleapis.com/language/translate/v2`,
        {
          q: text,
          source: 'ja',
          target: 'en',
          format: 'text'
        },
        {
          params: { key: this.GOOGLE_TRANSLATE_API_KEY },
          timeout: 5000
        }
      );

      return response.data?.data?.translations?.[0]?.translatedText || text;
    } catch (error) {
      console.warn('[TRANSLATE] Translation failed:', error);
      return text;
    }
  }

  // エラーハンドリング実装

  /**
   * エラーハンドリング
   */
  public async handle(error: Error | BaseError): Promise<ErrorHandlingResult> {
    const baseError = this.isBaseError(error) ? error : this.convertToBaseError(error);
    
    this.log(baseError);
    
    const isRetryable = this.isRetryable(baseError);
    const retryDelay = isRetryable ? this.calculateRetryDelay(baseError) : undefined;
    
    return {
      handled: true,
      shouldRetry: isRetryable,
      retryDelay,
      userNotification: {
        type: baseError.severity === ErrorSeverity.CRITICAL ? 'error' : 'warning',
        title: 'Search Error',
        message: this.getUserMessage(baseError)
      }
    };
  }

  /**
   * エラーログ
   */
  public log(error: BaseError): void {
    const logLevel = error.severity === ErrorSeverity.CRITICAL ? 'error' : 'warn';
    console[logLevel](`[${error.category}] ${error.message}`, {
      id: error.id,
      code: error.code,
      platform: error.platform,
      details: error.details
    });
  }

  /**
   * エラー報告
   */
  public async report(error: BaseError): Promise<void> {
    // 外部エラー報告サービスへの送信を実装
    console.error('[ERROR_REPORT] Would report error:', error);
  }

  /**
   * リトライ可能判定
   */
  public isRetryable(error: BaseError): boolean {
    return error.retryable && error.category !== ErrorCategory.INVALID_DATA_FORMAT;
  }

  /**
   * ユーザー向けメッセージ生成
   */
  public getUserMessage(error: BaseError, locale?: string): string {
    // ロケールに応じたメッセージを返す
    if (locale === 'ja' || !locale) {
      const messages: Record<ErrorCategory, string> = {
        [ErrorCategory.NETWORK_ERROR]: 'ネットワークエラーが発生しました。',
        [ErrorCategory.TIMEOUT]: '検索がタイムアウトしました。',
        [ErrorCategory.API_RATE_LIMIT]: 'API制限に達しました。しばらくお待ちください。',
        [ErrorCategory.API_AUTHENTICATION]: 'API認証エラーが発生しました。',
        [ErrorCategory.INVALID_DATA_FORMAT]: '無効なデータ形式です。',
        [ErrorCategory.CONFIGURATION_ERROR]: '設定エラーが発生しました。',
        [ErrorCategory.SYSTEM_ERROR]: 'システムエラーが発生しました。',
        [ErrorCategory.INVALID_SEARCH_TYPE]: '無効な検索タイプです。',
        [ErrorCategory.UNSUPPORTED_OPERATION]: 'サポートされていない操作です。',
        [ErrorCategory.UNKNOWN]: '不明なエラーが発生しました。',
        [ErrorCategory.DNS_RESOLUTION]: 'DNS解決エラーが発生しました。',
        [ErrorCategory.SSL_ERROR]: 'SSL接続エラーが発生しました。',
        [ErrorCategory.API_QUOTA_EXCEEDED]: 'APIクォータを超過しました。',
        [ErrorCategory.API_INVALID_REQUEST]: '無効なAPIリクエストです。',
        [ErrorCategory.API_SERVER_ERROR]: 'APIサーバーエラーが発生しました。',
        [ErrorCategory.API_MAINTENANCE]: 'APIメンテナンス中です。',
        [ErrorCategory.MISSING_REQUIRED_FIELD]: '必須フィールドが不足しています。',
        [ErrorCategory.DATA_VALIDATION]: 'データ検証エラーが発生しました。',
        [ErrorCategory.PARSING_ERROR]: 'データ解析エラーが発生しました。',
        [ErrorCategory.BUSINESS_LOGIC]: 'ビジネスロジックエラーが発生しました。',
        [ErrorCategory.RESOURCE_EXHAUSTED]: 'リソースが枯渇しました。',
        [ErrorCategory.PERMISSION_DENIED]: 'アクセスが拒否されました。'
      };
      
      return messages[error.category] || error.message;
    }
    
    return error.message;
  }

  // ユーティリティメソッド

  /**
   * リクエストバリデーション
   */
  private validateSearchRequest(request: SearchRequest): void {
    if (!request.query || request.query.trim().length === 0) {
      throw this.createError(
        ErrorCategory.INVALID_DATA_FORMAT,
        'Search query is required',
        ErrorSeverity.ERROR
      );
    }

    if (!Object.values(SearchType).includes(request.searchType)) {
      throw this.createError(
        ErrorCategory.INVALID_SEARCH_TYPE,
        `Invalid search type: ${request.searchType}`,
        ErrorSeverity.ERROR
      );
    }
  }

  /**
   * 設定バリデーション
   */
  private validateConfiguration(): void {
    const warnings: string[] = [];
    
    if (!this.YAHOO_SHOPPING_APP_ID) {
      warnings.push('Yahoo Shopping API key not configured');
      this.platformConfigs.yahoo_shopping.enabled = false;
    }
    
    if (!this.EBAY_APP_ID) {
      warnings.push('eBay API key not configured');
      this.platformConfigs.ebay.enabled = false;
    }
    
    if (!this.GOOGLE_TRANSLATE_API_KEY) {
      warnings.push('Google Translate API key not configured');
    }
    
    if (warnings.length > 0) {
      console.warn('[UNIFIED_ENGINE] Configuration warnings:', warnings);
    }
  }

  /**
   * JANコードバリデーション
   */
  private isValidJanCode(code: string): boolean {
    // JANコードは8桁または13桁の数字
    return /^(\d{8}|\d{13})$/.test(code);
  }

  /**
   * キャッシュキー生成
   */
  private generateCacheKey(request: SearchRequest): string {
    const key = {
      type: request.searchType,
      query: request.query,
      filters: request.filters,
      platforms: request.platforms,
      pagination: request.pagination
    };
    return `search_${JSON.stringify(key)}`;
  }

  /**
   * キャッシュから取得
   */
  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * キャッシュに保存
   */
  private saveToCache<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl ? ttl * 1000 : this.DEFAULT_CACHE_TTL,
      key
    });

    // キャッシュサイズ制限
    if (this.cache.size > 100) {
      const oldestKey = Array.from(this.cache.keys())[0];
      this.cache.delete(oldestKey);
    }
  }

  /**
   * メタデータ生成
   */
  private createSearchMetadata(request: SearchRequest): SearchMetadata {
    return {
      requestId: request.requestId || this.generateRequestId(),
      timestamp: new Date(),
      searchVersion: '2.0.0',
      locale: request.locale || 'ja-JP',
      currency: request.currency || 'JPY'
    };
  }

  /**
   * リクエストID生成
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * エラー生成
   */
  private createError(
    category: ErrorCategory,
    message: string,
    severity: ErrorSeverity,
    details?: any
  ): BaseError {
    return {
      id: this.generateRequestId(),
      code: `${category}_${Date.now()}`,
      message,
      severity,
      category,
      timestamp: new Date(),
      recoverable: severity !== ErrorSeverity.CRITICAL,
      retryable: category === ErrorCategory.NETWORK_ERROR || 
                 category === ErrorCategory.TIMEOUT,
      details
    };
  }

  /**
   * APIエラーハンドリング
   */
  private handleApiError(error: any, platform: string): BaseError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      
      let category = ErrorCategory.API_SERVER_ERROR;
      let severity = ErrorSeverity.ERROR;
      
      if (axiosError.response?.status === 429) {
        category = ErrorCategory.API_RATE_LIMIT;
      } else if (axiosError.response?.status === 401) {
        category = ErrorCategory.API_AUTHENTICATION;
      } else if (axiosError.code === 'ECONNABORTED') {
        category = ErrorCategory.TIMEOUT;
      } else if (!axiosError.response) {
        category = ErrorCategory.NETWORK_ERROR;
      }
      
      return {
        id: this.generateRequestId(),
        code: `${platform}_${category}`,
        message: axiosError.message,
        severity,
        category,
        timestamp: new Date(),
        platform,
        recoverable: true,
        retryable: category !== ErrorCategory.API_AUTHENTICATION,
        details: {
          status: axiosError.response?.status,
          statusText: axiosError.response?.statusText,
          data: axiosError.response?.data
        }
      } as ApiError;
    }
    
    return this.createError(
      ErrorCategory.UNKNOWN,
      error.message || 'Unknown error',
      ErrorSeverity.ERROR,
      { platform, originalError: error }
    );
  }

  /**
   * プラットフォームエラー生成
   */
  private createPlatformError(error: any, platform: string): BaseError {
    if (this.isBaseError(error)) {
      return { ...error, platform };
    }
    return this.handleApiError(error, platform);
  }

  /**
   * BaseError判定
   */
  private isBaseError(error: any): error is BaseError {
    return error && 
           typeof error === 'object' && 
           'id' in error && 
           'code' in error && 
           'severity' in error;
  }

  /**
   * エラー変換
   */
  private convertToBaseError(error: Error): BaseError {
    return this.createError(
      ErrorCategory.UNKNOWN,
      error.message,
      ErrorSeverity.ERROR,
      { stack: error.stack }
    );
  }

  /**
   * リトライ遅延計算
   */
  private calculateRetryDelay(error: BaseError): number {
    // エクスポネンシャルバックオフ
    const baseDelay = 1000; // 1秒
    const maxDelay = 30000; // 30秒
    
    if (error.category === ErrorCategory.API_RATE_LIMIT && error.details?.retryAfter) {
      return error.details.retryAfter * 1000;
    }
    
    return Math.min(baseDelay * Math.pow(2, 0), maxDelay);
  }

  /**
   * 検索エラーハンドリング
   */
  private handleSearchError(
    error: any,
    request: SearchRequest,
    metadata: SearchMetadata,
    executionTime: number
  ): UnifiedSearchResponse {
    const baseError = this.isBaseError(error) ? error : this.convertToBaseError(error);
    
    return {
      success: false,
      searchType: request.searchType,
      query: request.query,
      results: [],
      totalResults: 0,
      platformResults: {},
      pagination: {
        page: 1,
        limit: request.pagination?.limit || 20,
        totalPages: 0,
        hasNext: false,
        hasPrevious: false
      },
      summary: {
        totalFound: 0,
        afterFiltering: 0,
        afterDeduplication: 0,
        finalCount: 0,
        priceRange: {
          min: 0,
          max: 0,
          average: 0,
          median: 0
        },
        platformCounts: {},
        conditionCounts: {} as any,
        executionTimeMs: executionTime
      },
      metadata,
      errors: [{
        code: baseError.code,
        message: baseError.message,
        timestamp: baseError.timestamp,
        recoverable: baseError.recoverable,
        details: baseError.details
      }]
    };
  }

  /**
   * エラーアグリゲーター生成
   */
  private createErrorAggregator(): ErrorAggregator {
    const errors: BaseError[] = [];
    
    return {
      errors,
      add(error: BaseError): void {
        errors.push(error);
      },
      getBySeverity(severity: ErrorSeverity): BaseError[] {
        return errors.filter(e => e.severity === severity);
      },
      getByCategory(category: ErrorCategory): BaseError[] {
        return errors.filter(e => e.category === category);
      },
      getByPlatform(platform: string): BaseError[] {
        return errors.filter(e => e.platform === platform);
      },
      hasCriticalErrors(): boolean {
        return errors.some(e => e.severity === ErrorSeverity.CRITICAL);
      },
      getSummary(): any {
        const summary: any = {
          totalErrors: errors.length,
          bySeverity: {},
          byCategory: {},
          byPlatform: {},
          criticalErrors: []
        };
        
        errors.forEach(error => {
          // 重要度別
          summary.bySeverity[error.severity] = (summary.bySeverity[error.severity] || 0) + 1;
          
          // カテゴリ別
          summary.byCategory[error.category] = (summary.byCategory[error.category] || 0) + 1;
          
          // プラットフォーム別
          if (error.platform) {
            summary.byPlatform[error.platform] = (summary.byPlatform[error.platform] || 0) + 1;
          }
          
          // クリティカルエラー
          if (error.severity === ErrorSeverity.CRITICAL) {
            summary.criticalErrors.push(error);
          }
        });
        
        return summary;
      }
    };
  }
}

// エクスポート
export default UnifiedSearchEngine;