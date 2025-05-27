#!/usr/bin/env ts-node
/**
 * 統一検索インターフェースのテストスクリプト
 */

import { UnifiedSearchEngine } from '../src/jan/unified_search_engine_v2';
import {
  SearchRequest,
  SearchType,
  SortOption,
  ItemCondition
} from '../src/search/interfaces/search-request';

async function testUnifiedInterface() {
  console.log('=== 統一検索インターフェーステスト開始 ===\n');

  const engine = new UnifiedSearchEngine();

  // テストケース1: JANコード検索
  console.log('1. JANコード検索テスト');
  try {
    const janRequest: SearchRequest = {
      searchType: SearchType.JAN_CODE,
      query: '4549660894254',
      filters: {
        minPrice: 1000,
        maxPrice: 50000,
        sortBy: SortOption.PRICE_ASC
      },
      pagination: {
        page: 1,
        limit: 10
      },
      platforms: ['yahoo_shopping', 'ebay'],
      locale: 'ja-JP',
      currency: 'JPY'
    };

    const janResult = await engine.search(janRequest);
    console.log(`✓ JANコード検索完了: ${janResult.results.length}件の結果`);
    console.log(`  総検索時間: ${janResult.summary.executionTimeMs}ms`);
    console.log(`  プラットフォーム別: ${JSON.stringify(janResult.summary.platformCounts)}`);
  } catch (error) {
    console.error('✗ JANコード検索エラー:', error);
  }

  // テストケース2: 商品名検索
  console.log('\n2. 商品名検索テスト');
  try {
    const productRequest: SearchRequest = {
      searchType: SearchType.PRODUCT_NAME,
      query: 'Nintendo Switch',
      filters: {
        condition: [ItemCondition.NEW, ItemCondition.LIKE_NEW],
        sortBy: SortOption.PRICE_ASC
      },
      pagination: {
        page: 1,
        limit: 5
      },
      cacheEnabled: true,
      cacheTTL: 300
    };

    const productResult = await engine.search(productRequest);
    console.log(`✓ 商品名検索完了: ${productResult.results.length}件の結果`);
    if (productResult.results.length > 0) {
      console.log('  最安値商品:');
      const cheapest = productResult.results[0];
      console.log(`    - ${cheapest.title}`);
      console.log(`    - 価格: ¥${cheapest.totalPrice}`);
      console.log(`    - プラットフォーム: ${cheapest.platform}`);
    }
  } catch (error) {
    console.error('✗ 商品名検索エラー:', error);
  }

  // テストケース3: エラーハンドリングテスト
  console.log('\n3. エラーハンドリングテスト');
  try {
    const invalidRequest: SearchRequest = {
      searchType: SearchType.IMAGE,
      query: '',
      imageData: {
        imageUrl: 'https://example.com/image.jpg'
      }
    };

    const errorResult = await engine.search(invalidRequest);
    console.log(`✓ エラーハンドリング成功: ${errorResult.success ? '成功' : '失敗'}`);
    if (errorResult.errors && errorResult.errors.length > 0) {
      console.log(`  エラー: ${errorResult.errors[0].message}`);
    }
  } catch (error) {
    console.error('✗ エラーハンドリングテストエラー:', error);
  }

  // テストケース4: キャッシュテスト
  console.log('\n4. キャッシュ機能テスト');
  try {
    const cacheRequest: SearchRequest = {
      searchType: SearchType.KEYWORD,
      query: 'PlayStation 5',
      pagination: {
        page: 1,
        limit: 3
      },
      cacheEnabled: true
    };

    console.log('  初回検索...');
    const firstResult = await engine.search(cacheRequest);
    const firstTime = firstResult.summary.executionTimeMs;
    console.log(`  実行時間: ${firstTime}ms`);

    console.log('  キャッシュからの検索...');
    const cachedResult = await engine.search(cacheRequest);
    const cachedTime = cachedResult.summary.executionTimeMs;
    console.log(`  実行時間: ${cachedTime}ms`);
    console.log(`✓ キャッシュ効果: ${firstTime - cachedTime}ms短縮`);
  } catch (error) {
    console.error('✗ キャッシュテストエラー:', error);
  }

  // テストケース5: フィルタリングテスト
  console.log('\n5. フィルタリング機能テスト');
  try {
    const filterRequest: SearchRequest = {
      searchType: SearchType.KEYWORD,
      query: 'MacBook Pro',
      filters: {
        minPrice: 100000,
        maxPrice: 300000,
        condition: [ItemCondition.NEW],
        sortBy: SortOption.RATING
      },
      pagination: {
        page: 1,
        limit: 5
      }
    };

    const filterResult = await engine.search(filterRequest);
    console.log(`✓ フィルタリング完了: ${filterResult.results.length}件の結果`);
    console.log(`  価格範囲: ¥${filterResult.summary.priceRange.min} - ¥${filterResult.summary.priceRange.max}`);
    console.log(`  平均価格: ¥${Math.round(filterResult.summary.priceRange.average)}`);
  } catch (error) {
    console.error('✗ フィルタリングテストエラー:', error);
  }

  console.log('\n=== テスト完了 ===');
}

// 実行
if (require.main === module) {
  testUnifiedInterface().catch(console.error);
}