/**
 * プラットフォームレジストリ
 * すべてのプラットフォームアダプターの登録・管理を行う
 */

import { PlatformAdapter, PlatformRegistration, PlatformPriority } from '../interfaces/platform-adapter';
import { SearchRequest } from '../../search/interfaces/search-request';
import { SearchResult } from '../../search/interfaces/search-response';

export class PlatformRegistry {
  private static instance: PlatformRegistry;
  private platforms: Map<string, PlatformRegistration> = new Map();
  
  private constructor() {}
  
  static getInstance(): PlatformRegistry {
    if (!PlatformRegistry.instance) {
      PlatformRegistry.instance = new PlatformRegistry();
    }
    return PlatformRegistry.instance;
  }
  
  /**
   * プラットフォームを登録
   */
  register(registration: PlatformRegistration): void {
    const { adapter } = registration;
    if (this.platforms.has(adapter.code)) {
      throw new Error(`Platform ${adapter.code} is already registered`);
    }
    
    this.platforms.set(adapter.code, registration);
    console.log(`Platform ${adapter.name} (${adapter.code}) registered successfully`);
  }
  
  /**
   * プラットフォームを登録解除
   */
  unregister(code: string): boolean {
    return this.platforms.delete(code);
  }
  
  /**
   * プラットフォームを取得
   */
  getPlatform(code: string): PlatformAdapter | undefined {
    return this.platforms.get(code)?.adapter;
  }
  
  /**
   * 有効なプラットフォーム一覧を取得
   */
  getEnabledPlatforms(): PlatformAdapter[] {
    return Array.from(this.platforms.values())
      .filter(reg => reg.priority.enabled)
      .sort((a, b) => a.priority.priority - b.priority.priority)
      .map(reg => reg.adapter);
  }
  
  /**
   * 検索タイプをサポートするプラットフォームを取得
   */
  getPlatformsForSearchType(searchType: string): PlatformAdapter[] {
    return this.getEnabledPlatforms()
      .filter(platform => 
        platform.supportedSearchTypes.includes(searchType as any)
      );
  }
  
  /**
   * 地域をサポートするプラットフォームを取得
   */
  getPlatformsForRegion(region: string): PlatformAdapter[] {
    return this.getEnabledPlatforms()
      .filter(platform => 
        platform.supportedRegions.includes(region)
      );
  }
  
  /**
   * すべてのプラットフォームで並列検索を実行
   */
  async searchAll(
    request: SearchRequest,
    platforms?: string[]
  ): Promise<Map<string, SearchResult[]>> {
    const targetPlatforms = platforms 
      ? this.getEnabledPlatforms().filter(p => platforms.includes(p.code))
      : this.getPlatformsForSearchType(request.type);
    
    const searchPromises = targetPlatforms.map(async platform => {
      try {
        const result = await platform.search(request);
        return {
          code: platform.code,
          results: result.results
        };
      } catch (error) {
        console.error(`Search failed for ${platform.name}:`, error);
        return {
          code: platform.code,
          results: []
        };
      }
    });
    
    const results = await Promise.allSettled(searchPromises);
    const resultMap = new Map<string, SearchResult[]>();
    
    results.forEach(result => {
      if (result.status === 'fulfilled' && result.value) {
        resultMap.set(result.value.code, result.value.results);
      }
    });
    
    return resultMap;
  }
  
  /**
   * プラットフォームの健全性をチェック
   */
  async checkHealth(): Promise<Map<string, any>> {
    const healthChecks = new Map<string, any>();
    
    for (const [code, registration] of this.platforms) {
      try {
        const health = await registration.adapter.healthCheck();
        healthChecks.set(code, health);
      } catch (error) {
        healthChecks.set(code, {
          status: 'unhealthy',
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
    
    return healthChecks;
  }
  
  /**
   * プラットフォームの統計情報を取得
   */
  getStatistics(): any {
    const stats = {
      totalPlatforms: this.platforms.size,
      enabledPlatforms: this.getEnabledPlatforms().length,
      platformsByRegion: new Map<string, number>(),
      platformsBySearchType: new Map<string, number>()
    };
    
    for (const platform of this.getEnabledPlatforms()) {
      // 地域別集計
      for (const region of platform.supportedRegions) {
        stats.platformsByRegion.set(
          region,
          (stats.platformsByRegion.get(region) || 0) + 1
        );
      }
      
      // 検索タイプ別集計
      for (const searchType of platform.supportedSearchTypes) {
        stats.platformsBySearchType.set(
          searchType,
          (stats.platformsBySearchType.get(searchType) || 0) + 1
        );
      }
    }
    
    return stats;
  }
}