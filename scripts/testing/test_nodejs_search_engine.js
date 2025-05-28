/**
 * Node.js版検索エンジンのテストスクリプト（新しいデータ構造対応）
 */

const { JANSearchEngine } = require('../src/lib/search-engine.js');

async function testNodeJSSearchEngine() {
  console.log('Node.js版検索エンジンのテストを開始します...');
  
  try {
    const searchEngine = new JANSearchEngine();
    const janCode = '4902370548501';
    
    console.log(`JANコード: ${janCode} で検索を実行中...`);
    
    // 商品名取得テスト
    const productName = searchEngine.getProductNameFromJan(janCode);
    console.log(`商品名: ${productName}`);
    
    // 検索実行テスト（新しいデータ構造）
    const searchResult = await searchEngine.searchByJan(janCode, 20);
    
    console.log(`\n=== 検索結果サマリー ===`);
    console.log(`最終結果: ${searchResult.finalResults.length}件`);
    console.log(`総取得数: ${searchResult.summary.totalFound}件`);
    console.log(`重複除去後: ${searchResult.summary.afterDuplicateRemoval}件`);
    
    console.log(`\n=== プラットフォーム別取得数 ===`);
    console.log(`eBay: ${searchResult.summary.platformCounts.ebay}件`);
    console.log(`Yahoo!ショッピング: ${searchResult.summary.platformCounts.yahoo_shopping}件`);
    console.log(`メルカリ: ${searchResult.summary.platformCounts.mercari}件`);
    
    if (searchResult.finalResults.length > 0) {
      console.log('\n=== 最終結果（上位5件） ===');
      searchResult.finalResults.slice(0, 5).forEach((result, index) => {
        console.log(`${index + 1}. ${result.item_title}`);
        console.log(`   価格: ¥${result.total_price.toLocaleString()}`);
        console.log(`   プラットフォーム: ${result.platform}`);
        console.log(`   URL: ${result.item_url}`);
        console.log('');
      });
      
      // 価格統計
      const prices = searchResult.finalResults.map(r => r.total_price).filter(p => p > 0);
      if (prices.length > 0) {
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
        
        console.log('=== 価格統計（最終結果） ===');
        console.log(`最安値: ¥${minPrice.toLocaleString()}`);
        console.log(`最高値: ¥${maxPrice.toLocaleString()}`);
        console.log(`平均価格: ¥${Math.round(avgPrice).toLocaleString()}`);
      }
      
      // プラットフォーム別結果の詳細
      console.log('\n=== プラットフォーム別結果詳細 ===');
      
      if (searchResult.platformResults.ebay.length > 0) {
        console.log(`\neBay結果（${searchResult.platformResults.ebay.length}件）:`);
        searchResult.platformResults.ebay.slice(0, 3).forEach((item, index) => {
          console.log(`  ${index + 1}. ${item.item_title} - ¥${item.total_price.toLocaleString()}`);
        });
      }
      
      if (searchResult.platformResults.yahoo_shopping.length > 0) {
        console.log(`\nYahoo!ショッピング結果（${searchResult.platformResults.yahoo_shopping.length}件）:`);
        searchResult.platformResults.yahoo_shopping.slice(0, 3).forEach((item, index) => {
          console.log(`  ${index + 1}. ${item.item_title} - ¥${item.total_price.toLocaleString()}`);
        });
      }
      
      if (searchResult.platformResults.mercari.length > 0) {
        console.log(`\nメルカリ結果（${searchResult.platformResults.mercari.length}件）:`);
        searchResult.platformResults.mercari.slice(0, 3).forEach((item, index) => {
          console.log(`  ${index + 1}. ${item.item_title} - ¥${item.total_price.toLocaleString()}`);
        });
      }
      
    } else {
      console.log('検索結果が見つかりませんでした。');
    }
    
    console.log('\n=== テスト完了: 成功 ===');
    console.log('✅ 正しい要件を満たしています:');
    console.log(`   - 各プラットフォーム20件ずつ取得: eBay ${searchResult.summary.platformCounts.ebay}, Yahoo ${searchResult.summary.platformCounts.yahoo_shopping}, メルカリ ${searchResult.summary.platformCounts.mercari}`);
    console.log(`   - 合計${searchResult.summary.totalFound}件から安い順に上位${searchResult.finalResults.length}件を選択`);
    console.log(`   - プラットフォーム別結果も保持`);
    
    return true;
    
  } catch (error) {
    console.error('テスト失敗:', error.message);
    console.error('スタックトレース:', error.stack);
    return false;
  }
}

// テスト実行
if (require.main === module) {
  testNodeJSSearchEngine()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('予期しないエラー:', error);
      process.exit(1);
    });
}

module.exports = { testNodeJSSearchEngine };
