#!/usr/bin/env npx tsx

/**
 * AI商品フィルタリングテストスクリプト
 * 
 * 使用方法:
 * npx tsx scripts/test_ai_product_filter.ts
 */

import { aiProductFilter } from '../src/utils/ai_product_filter';

// テスト用の模擬検索結果
const mockSearchResults = [
  {
    platform: 'test',
    title: 'iPhone 15 128GB ブラック 新品未開封',
    item_title: 'iPhone 15 128GB ブラック 新品未開封',
    url: 'https://example.com/1',
    price: 95000,
    total_price: 95000
  },
  {
    platform: 'test',
    title: 'iPhone 15 Pro 256GB シルバー',
    item_title: 'iPhone 15 Pro 256GB シルバー',
    url: 'https://example.com/2',
    price: 120000,
    total_price: 120000
  },
  {
    platform: 'test',
    title: 'iPhone 15 ケース 透明 クリア',
    item_title: 'iPhone 15 ケース 透明 クリア',
    url: 'https://example.com/3',
    price: 1500,
    total_price: 1500
  },
  {
    platform: 'test',
    title: 'iPhone 15 用 充電器 USB-C',
    item_title: 'iPhone 15 用 充電器 USB-C',
    url: 'https://example.com/4',
    price: 3000,
    total_price: 3000
  },
  {
    platform: 'test',
    title: 'Samsung Galaxy S24 256GB',
    item_title: 'Samsung Galaxy S24 256GB',
    url: 'https://example.com/5',
    price: 110000,
    total_price: 110000
  },
  {
    platform: 'test',
    title: 'Nintendo Switch 本体 有機EL',
    item_title: 'Nintendo Switch 本体 有機EL',
    url: 'https://example.com/6',
    price: 38000,
    total_price: 38000
  }
];

async function testAIFiltering() {
  console.log('=== AI商品フィルタリングテスト ===\n');
  
  const searchQuery = 'iPhone 15';
  console.log(`検索クエリ: "${searchQuery}"`);
  console.log(`検索結果: ${mockSearchResults.length}件\n`);
  
  // 個別の関連性チェック
  console.log('--- 個別関連性チェック ---');
  for (const product of mockSearchResults) {
    try {
      const relevance = await aiProductFilter.checkProductRelevance(
        searchQuery,
        product.title
      );
      
      console.log(`商品: ${product.title}`);
      console.log(`  関連性: ${relevance.isRelevant ? '✅' : '❌'} (${relevance.confidence.toFixed(2)})`);
      console.log(`  カテゴリ: ${relevance.category}`);
      console.log(`  理由: ${relevance.reason}\n`);
    } catch (error) {
      console.error(`エラー: ${product.title} - ${error}\n`);
    }
  }
  
  // 一括フィルタリング
  console.log('--- 一括フィルタリング ---');
  try {
    const filteredProducts = await aiProductFilter.filterProducts(
      searchQuery,
      mockSearchResults
    );
    
    console.log(`フィルタリング結果: ${mockSearchResults.length}件 → ${filteredProducts.length}件\n`);
    
    console.log('フィルタリング後の商品:');
    filteredProducts.forEach((product, index) => {
      console.log(`${index + 1}. ${product.title} (¥${product.price.toLocaleString()})`);
    });
    
    console.log('\n除外された商品:');
    const excludedProducts = mockSearchResults.filter(
      product => !filteredProducts.some(filtered => filtered.title === product.title)
    );
    excludedProducts.forEach((product, index) => {
      console.log(`${index + 1}. ${product.title} (¥${product.price.toLocaleString()})`);
    });
    
  } catch (error) {
    console.error('一括フィルタリングエラー:', error);
  }
  
  // アクセサリーを許可した場合のテスト
  console.log('\n--- アクセサリー許可テスト ---');
  try {
    // Create a filter that allows accessories
    const { AIProductFilter } = await import('../src/utils/ai_product_filter');
    const accessoryAllowingFilter = new AIProductFilter({
      allowAccessories: true,
      minConfidence: 0.5
    });
    
    const filteredWithAccessories = await accessoryAllowingFilter.filterProducts(
      searchQuery,
      mockSearchResults
    );
    
    console.log(`アクセサリー許可時: ${mockSearchResults.length}件 → ${filteredWithAccessories.length}件\n`);
    
    filteredWithAccessories.forEach((product, index) => {
      console.log(`${index + 1}. ${product.title} (¥${product.price.toLocaleString()})`);
    });
    
  } catch (error) {
    console.error('アクセサリー許可テストエラー:', error);
  }
}

// テスト実行
if (require.main === module) {
  testAIFiltering().catch(console.error);
}

export { testAIFiltering };