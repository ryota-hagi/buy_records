/**
 * 統一検索レスポンスインターフェース
 */

export interface SearchResult {
  id: string;
  platform: string;
  title: string;
  description?: string;
  url: string;
  imageUrl: string;
  price: number;
  shippingFee: number;
  totalPrice: number;
  condition: string;
  storeName: string;
  location?: string;
  currency: string;
  exchangeRate?: number;
  matchScore?: number; // 検索クエリとの一致度
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  success: boolean;
  searchType: string;
  query: string | Record<string, any>;
  totalResults: number;
  results: SearchResult[];
  platformsSearched: string[];
  platformMetadata?: Record<string, PlatformSearchMetadata>;
  searchContext?: SearchContext;
  errors?: string[];
  timestamp: string;
}

export interface PlatformSearchMetadata {
  platform: string;
  resultsCount: number;
  searchTime: number;
  searchMethod?: string;
  error?: string;
}

export interface SearchContext {
  keywords: string[];
  originalQuery: string;
  detectedJanCode?: string;
  detectedProductName?: string;
  imageAnalysis?: ImageAnalysisResult;
  naturalLanguageAnalysis?: NLPAnalysisResult;
  confidence: number;
}

export interface ImageAnalysisResult {
  detectedText?: string[];
  detectedJanCode?: string;
  productCategory?: string;
  productFeatures?: string[];
  confidence: number;
}

export interface NLPAnalysisResult {
  intent: string;
  extractedKeywords: string[];
  priceConstraints?: {
    min?: number;
    max?: number;
  };
  conditionConstraints?: string[];
  colorConstraints?: string[];
  sizeConstraints?: string[];
}