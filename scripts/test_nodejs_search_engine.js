/**
 * Node.js版検索エンジンのテストスクリプト
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
    
    // 検索実行テスト
    const results = await searchEngine.searchByJan(janCode, 20);
    
    console.log(`\n検索結果: ${results.length}件`);
    
    if (results.length > 0) {
      console.log('\n最初の5件の結果:');
      results.slice(0, 5).forEach((result, index) => {
        console.log(`${index + 1}. ${result.item_title}`);
        console.log(`   価格: ¥${result.total_price.toLocaleString()}`);
        console.log(`   プラットフォーム: ${result.platform}`);
        console.log(`   URL: ${result.item_url}`);
        console.log('');
      });
      
      // 価格統計
      const prices = results.map(r => r.total_price).filter(p => p > 0);
      if (prices.length > 0) {
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
        
        console.log('価格統計:');
        console.log(`最安値: ¥${minPrice.toLocaleString()}`);
        console.log(`最高値: ¥${maxPrice.toLocaleString()}`);
        console.log(`平均価格: ¥${Math.round(avgPrice).toLocaleString()}`);
      }
    } else {
      console.log('検索結果が見つかりませんでした。');
    }
    
    console.log('\nテスト完了: 成功');
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
