import axios from 'axios';

// 検索結果の型定義
interface SearchResult {
  platform: string;
  item_title: string;
  item_url: string;
  item_image_url: string;
  price: number;
  total_price: number;
  shipping_cost: number;
  condition: string;
  seller: string;
  jan_code?: string;
}

interface UnifiedSearchResponse {
  success: boolean;
  product_name: string;
  total_results: number;
  final_results: SearchResult[];
  platform_results: {
    yahoo_shopping: SearchResult[];
    mercari: SearchResult[];
    ebay: SearchResult[];
  };
  summary: {
    total_found: number;
    after_deduplication: number;
    final_count: number;
    execution_time_ms: number;
  };
}

/**
 * シンプル版統合JANコード検索エンジン
 * 確実に動作する直接API呼び出し方式
 */
export class UnifiedJanSearchEngineSimple {
  private readonly baseUrl: string;

  constructor() {
    // 本番環境とローカル環境の判定
    this.baseUrl = process.env.NODE_ENV === 'production' 
      ? 'https://buy-records.vercel.app'
      : 'http://localhost:3000';
    
    console.log(`[UNIFIED_SIMPLE] Using base URL: ${this.baseUrl}`);
  }

  /**
   * メイン検索実行関数 - シンプルで確実な実装
   */
  async executeUnifiedJanSearch(janCode: string): Promise<UnifiedSearchResponse> {
    const startTime = Date.now();
    
    try {
      console.log(`[UNIFIED_SIMPLE] Starting unified JAN search for: ${janCode}`);
      
      // Step 1: JANコードから商品名を特定
      const productName = await this.getProductNameFromJan(janCode);
      console.log(`[UNIFIED_SIMPLE] Product name identified: ${productName}`);
      
      // Step 2: 順次検索実行（並行処理ではなく順次処理で確実に）
      console.log(`[UNIFIED_SIMPLE] Starting sequential search...`);
      
      const yahooResults = await this.searchYahooShopping(janCode, 20);
      console.log(`[UNIFIED_SIMPLE] Yahoo results: ${yahooResults.length}`);
      
      const mercariResults = await this.searchMercari(productName, 20);
      console.log(`[UNIFIED_SIMPLE] Mercari results: ${mercariResults.length}`);
      
      const ebayResults = await this.searchEbay(productName, 20);
      console.log(`[UNIFIED_SIMPLE] eBay results: ${ebayResults.length}`);

      // Step 3: 結果統合・重複除去・価格順ソート
      const allResults = [...yahooResults, ...mercariResults, ...ebayResults];
      console.log(`[UNIFIED_SIMPLE] Total results before deduplication: ${allResults.length}`);
      
      const deduplicatedResults = this.removeDuplicates(allResults);
      console.log(`[UNIFIED_SIMPLE] Results after deduplication: ${deduplicatedResults.length}`);
      
      const sortedResults = deduplicatedResults.sort((a, b) => a.total_price - b.total_price);
      const finalResults = sortedResults.slice(0, 20);

      const executionTime = Date.now() - startTime;
      
      console.log(`[UNIFIED_SIMPLE] Search completed in ${executionTime}ms. Final results: ${finalResults.length}/20`);

      return {
        success: true,
        product_name: productName,
        total_results: allResults.length,
        final_results: finalResults,
        platform_results: {
          yahoo_shopping: yahooResults,
          mercari: mercariResults,
          ebay: ebayResults
        },
        summary: {
          total_found: allResults.length,
          after_deduplication: deduplicatedResults.length,
          final_count: finalResults.length,
          execution_time_ms: executionTime
        }
      };

    } catch (error) {
      console.error('[UNIFIED_SIMPLE] Search failed:', error);
      return {
        success: false,
        product_name: `商品 (JANコード: ${janCode})`,
        total_results: 0,
        final_results: [],
        platform_results: {
          yahoo_shopping: [],
          mercari: [],
          ebay: []
        },
        summary: {
          total_found: 0,
          after_deduplication: 0,
          final_count: 0,
          execution_time_ms: Date.now() - startTime
        }
      };
    }
  }

  /**
   * JANコードから商品名を特定
   */
  private async getProductNameFromJan(janCode: string): Promise<string> {
    try {
      console.log(`[PRODUCT_NAME_SIMPLE] Fetching product name for JAN: ${janCode}`);
      
      const url = `${this.baseUrl}/api/search/yahoo`;
      const params = new URLSearchParams({
        jan_code: janCode,
        limit: '1'
      });
      
      console.log(`[PRODUCT_NAME_SIMPLE] Request URL: ${url}?${params.toString()}`);
      
      const response = await axios.get(url, {
        params: {
          jan_code: janCode,
          limit: 1
        },
        timeout: 10000,
        headers: {
          'User-Agent': 'UnifiedSearchEngine/1.0'
        }
      });

      console.log(`[PRODUCT_NAME_SIMPLE] Yahoo API response status: ${response.status}`);
      console.log(`[PRODUCT_NAME_SIMPLE] Yahoo API response data:`, {
        success: response.data?.success,
        resultsLength: response.data?.results?.length,
        firstResult: response.data?.results?.[0]?.title?.substring(0, 50)
      });

      if (response.data?.success && response.data?.results?.length > 0) {
        const productName = response.data.results[0].title;
        console.log(`[PRODUCT_NAME_SIMPLE] Found from Yahoo API: ${productName}`);
        return productName;
      }

      console.warn(`[PRODUCT_NAME_SIMPLE] No product name found for JAN: ${janCode}`);
      return `商品 (JANコード: ${janCode})`;
      
    } catch (error) {
      console.error(`[PRODUCT_NAME_SIMPLE] Error:`, error);
      return `商品 (JANコード: ${janCode})`;
    }
  }

  /**
   * Yahoo Shopping検索
   */
  private async searchYahooShopping(janCode: string, limit: number): Promise<SearchResult[]> {
    try {
      console.log(`[YAHOO_SIMPLE] Starting search with JAN: ${janCode}`);
      
      const url = `${this.baseUrl}/api/search/yahoo`;
      const params = new URLSearchParams({
        jan_code: janCode,
        limit: limit.toString()
      });
      
      console.log(`[YAHOO_SIMPLE] Request URL: ${url}?${params.toString()}`);
      
      const response = await axios.get(url, {
        params: {
          jan_code: janCode,
          limit: limit
        },
        timeout: 15000,
        headers: {
          'User-Agent': 'UnifiedSearchEngine/1.0'
        }
      });

      console.log(`[YAHOO_SIMPLE] API response status: ${response.status}`);
      console.log(`[YAHOO_SIMPLE] API response data:`, {
        success: response.data?.success,
        resultsLength: response.data?.results?.length
      });
      
      if (response.data?.success && response.data?.results) {
        const results = response.data.results.map((item: any) => ({
          platform: 'yahoo_shopping',
          item_title: item.title || '',
          item_url: item.url || '',
          item_image_url: item.image_url || '',
          price: item.price || 0,
          total_price: item.total_price || item.price || 0,
          shipping_cost: item.shipping_fee || 0,
          condition: item.condition || '新品',
          seller: item.store_name || '',
          jan_code: janCode
        }));
        
        console.log(`[YAHOO_SIMPLE] Successfully processed ${results.length} items`);
        return results;
      }

      console.warn(`[YAHOO_SIMPLE] No results from API`);
      return [];

    } catch (error) {
      console.error('[YAHOO_SIMPLE] Search failed:', error);
      return [];
    }
  }

  /**
   * メルカリ検索
   */
  private async searchMercari(productName: string, limit: number): Promise<SearchResult[]> {
    try {
      console.log(`[MERCARI_SIMPLE] Starting search for: ${productName}`);
      
      const url = `${this.baseUrl}/api/search/mercari`;
      const params = new URLSearchParams({
        query: productName,
        limit: limit.toString()
      });
      
      console.log(`[MERCARI_SIMPLE] Request URL: ${url}?${params.toString()}`);
      
      const response = await axios.get(url, {
        params: {
          query: productName,
          limit: limit
        },
        timeout: 15000,
        headers: {
          'User-Agent': 'UnifiedSearchEngine/1.0'
        }
      });

      console.log(`[MERCARI_SIMPLE] API response status: ${response.status}`);
      console.log(`[MERCARI_SIMPLE] API response data:`, {
        success: response.data?.success,
        resultsLength: response.data?.results?.length
      });
      
      if (response.data?.success && response.data?.results) {
        const results = response.data.results.map((item: any) => ({
          platform: 'mercari',
          item_title: item.title || '',
          item_url: item.url || '',
          item_image_url: item.image_url || '',
          price: item.price || 0,
          total_price: item.total_price || item.price || 0,
          shipping_cost: item.shipping_fee || 0,
          condition: item.condition || '中古',
          seller: item.store_name || item.seller || ''
        }));
        
        console.log(`[MERCARI_SIMPLE] Successfully processed ${results.length} items`);
        return results;
      }

      console.warn(`[MERCARI_SIMPLE] No results from API`);
      return [];

    } catch (error) {
      console.error('[MERCARI_SIMPLE] Search failed:', error);
      return [];
    }
  }

  /**
   * eBay検索
   */
  private async searchEbay(productName: string, limit: number): Promise<SearchResult[]> {
    try {
      console.log(`[EBAY_SIMPLE] Starting search for: ${productName}`);
      
      const url = `${this.baseUrl}/api/search/ebay`;
      const params = new URLSearchParams({
        query: productName,
        limit: limit.toString()
      });
      
      console.log(`[EBAY_SIMPLE] Request URL: ${url}?${params.toString()}`);
      
      const response = await axios.get(url, {
        params: {
          query: productName,
          limit: limit
        },
        timeout: 15000,
        headers: {
          'User-Agent': 'UnifiedSearchEngine/1.0'
        }
      });

      console.log(`[EBAY_SIMPLE] API response status: ${response.status}`);
      console.log(`[EBAY_SIMPLE] API response data:`, {
        success: response.data?.success,
        resultsLength: response.data?.results?.length
      });
      
      if (response.data?.success && response.data?.results) {
        const results = response.data.results.map((item: any) => ({
          platform: 'ebay',
          item_title: item.title || '',
          item_url: item.url || '',
          item_image_url: item.image_url || '',
          price: item.price || 0,
          total_price: item.total_price || item.price || 0,
          shipping_cost: item.shipping_fee || 0,
          condition: item.condition || 'Used',
          seller: item.store_name || item.seller || ''
        }));
        
        console.log(`[EBAY_SIMPLE] Successfully processed ${results.length} items`);
        return results;
      }

      console.warn(`[EBAY_SIMPLE] No results from API`);
      return [];

    } catch (error) {
      console.error('[EBAY_SIMPLE] Search failed:', error);
      return [];
    }
  }

  /**
   * 重複除去
   */
  private removeDuplicates(results: SearchResult[]): SearchResult[] {
    const seen = new Set<string>();
    return results.filter((item) => {
      const key = `${item.platform}-${item.item_title.toLowerCase()}-${item.price}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }
}

// デフォルトエクスポート
export default UnifiedJanSearchEngineSimple;
