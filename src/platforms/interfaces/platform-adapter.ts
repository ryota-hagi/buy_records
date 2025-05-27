/**
 * プラットフォームアダプターの標準インターフェース
 * 新しいプラットフォームを追加する際は、このインターフェースを実装する
 */

import { SearchRequest, SearchType } from '../../search/interfaces/search-request';
import { SearchResult } from '../../search/interfaces/search-response';

export interface PlatformAdapter {
  /**
   * プラットフォームの表示名
   */
  name: string;
  
  /**
   * プラットフォームの識別コード（URLやキー等で使用）
   */
  code: string;
  
  /**
   * サポートする検索タイプ
   */
  supportedSearchTypes: SearchType[];
  
  /**
   * サポートする地域コード（ISO 3166-1 alpha-2）
   */
  supportedRegions: string[];
  
  /**
   * プラットフォーム固有の設定
   */
  config?: PlatformConfig;
  
  /**
   * 検索を実行
   */
  search(request: SearchRequest): Promise<PlatformSearchResult>;
  
  /**
   * API認証情報の検証
   */
  validateCredentials(): Promise<boolean>;
  
  /**
   * APIの利用制限情報を取得
   */
  getApiLimits(): ApiLimits;
  
  /**
   * プラットフォームの健全性チェック
   */
  healthCheck(): Promise<HealthCheckResult>;
}

export interface PlatformSearchResult {
  results: SearchResult[];
  metadata: {
    totalFound: number;
    searchTime: number;
    searchMethod: string;
    cacheHit?: boolean;
  };
  errors?: string[];
}

export interface PlatformConfig {
  apiKey?: string;
  apiSecret?: string;
  apiEndpoint?: string;
  searchMethods?: string[];
  rateLimit?: RateLimitConfig;
  timeout?: number;
  retryAttempts?: number;
  customHeaders?: Record<string, string>;
}

export interface ApiLimits {
  requestsPerMinute: number;
  requestsPerDay: number;
  requestsPerMonth?: number;
  maxResultsPerRequest: number;
  maxConcurrentRequests?: number;
  quotaResetTime?: string; // ISO 8601
}

export interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
  strategy: 'sliding' | 'fixed';
}

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency: number;
  lastError?: string;
  lastSuccessfulRequest?: Date;
}

/**
 * プラットフォームの優先度設定
 */
export interface PlatformPriority {
  code: string;
  priority: number;
  enabled: boolean;
  fallbackTo?: string; // 障害時のフォールバック先
}

/**
 * プラットフォーム登録情報
 */
export interface PlatformRegistration {
  adapter: PlatformAdapter;
  priority: PlatformPriority;
  metadata: {
    addedDate: Date;
    version: string;
    maintainer?: string;
    documentation?: string;
  };
}