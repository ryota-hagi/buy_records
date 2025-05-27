/**
 * 統一検索リクエストインターフェース
 */

export enum SearchType {
  JAN_CODE = 'jan_code',
  PRODUCT_NAME = 'product_name',
  IMAGE = 'image',
  NATURAL_LANGUAGE = 'natural_language'
}

export interface BaseSearchRequest {
  type: SearchType;
  limit?: number;
  minPrice?: number;
  maxPrice?: number;
  condition?: ProductCondition[];
  platforms?: Platform[];
}

export interface JANSearchRequest extends BaseSearchRequest {
  type: SearchType.JAN_CODE;
  janCode: string;
}

export interface ProductNameSearchRequest extends BaseSearchRequest {
  type: SearchType.PRODUCT_NAME;
  productName: string;
  category?: string;
}

export interface ImageSearchRequest extends BaseSearchRequest {
  type: SearchType.IMAGE;
  imageData: string; // Base64 encoded image
  imageUrl?: string;
}

export interface NaturalLanguageSearchRequest extends BaseSearchRequest {
  type: SearchType.NATURAL_LANGUAGE;
  query: string;
}

export type SearchRequest = 
  | JANSearchRequest 
  | ProductNameSearchRequest 
  | ImageSearchRequest 
  | NaturalLanguageSearchRequest;

export enum ProductCondition {
  NEW = 'new',
  LIKE_NEW = 'like_new',
  VERY_GOOD = 'very_good',
  GOOD = 'good',
  ACCEPTABLE = 'acceptable'
}

export enum Platform {
  EBAY = 'ebay',
  MERCARI = 'mercari',
  YAHOO_SHOPPING = 'yahoo_shopping'
}

export interface SearchContext {
  keywords: string[];
  originalQuery: string;
  detectedJanCode?: string;
  detectedProductName?: string;
  priceRange?: {
    min?: number;
    max?: number;
  };
  conditions?: ProductCondition[];
  confidence: number;
}