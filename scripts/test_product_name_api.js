#!/usr/bin/env node
/**
 * 商品名検索APIの簡易テストスクリプト
 */

const axios = require('axios');

async function testProductNameSearch(productName, baseUrl = 'http://localhost:3000') {
  console.log('\n' + '='.repeat(60));
  console.log(`商品名検索テスト: ${productName}`);
  console.log('='.repeat(60) + '\n');

  try {
    const url = `${baseUrl}/api/search/product-name`;
    const params = {
      product_name: productName,
      limit: 10
    };

    console.log(`リクエストURL: ${url}`);
    console.log(`パラメータ:`, params);

    const startTime = Date.now();
    const response = await axios.get(url, { params, timeout: 60000 });
    const elapsedTime = (Date.now() - startTime) / 1000;

    console.log(`\nステータスコード: ${response.status}`);
    console.log(`応答時間: ${elapsedTime.toFixed(2)}秒`);

    const data = response.data;

    if (data.success) {
      console.log('\n[検索結果サマリー]');
      console.log(`検索タイプ: ${data.search_type}`);
      console.log(`総結果数: ${data.total_results}`);
      console.log(`検索プラットフォーム数: ${data.platforms_searched}`);

      // 関連性統計
      if (data.relevance_stats) {
        console.log('\n[関連性統計]');
        console.log(`高関連性 (80以上): ${data.relevance_stats.high_relevance}件`);
        console.log(`中関連性 (50-79): ${data.relevance_stats.medium_relevance}件`);
        console.log(`低関連性 (50未満): ${data.relevance_stats.low_relevance}件`);
        console.log(`平均スコア: ${data.relevance_stats.average_score}`);
      }

      // プラットフォーム別結果
      if (data.platforms) {
        console.log('\n[プラットフォーム別結果]');
        Object.entries(data.platforms).forEach(([platform, items]) => {
          console.log(`- ${platform}: ${items.length}件`);
        });
      }

      // 上位3件の結果
      if (data.results && data.results.length > 0) {
        console.log('\n[上位結果 (最大3件)]');
        data.results.slice(0, 3).forEach((item, index) => {
          console.log(`\n${index + 1}. ${item.title}`);
          console.log(`   プラットフォーム: ${item.platform}`);
          console.log(`   価格: ¥${item.price.toLocaleString()}`);
          console.log(`   関連性スコア: ${item.relevance_score}`);
        });
      }

      return { success: true, totalResults: data.total_results };
    } else {
      console.log(`\nエラー: ${data.error}`);
      return { success: false, error: data.error };
    }
  } catch (error) {
    console.error('\n例外エラー:', error.message);
    if (error.response) {
      console.error('レスポンスデータ:', error.response.data);
    }
    return { success: false, error: error.message };
  }
}

async function runTests() {
  const testCases = [
    'Nintendo Switch',
    'iPhone 15 Pro',
    'サントリー 緑茶 伊右衛門'
  ];

  const results = [];

  for (const productName of testCases) {
    const result = await testProductNameSearch(productName);
    results.push({ productName, ...result });
    // API負荷軽減のため待機
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // サマリー表示
  console.log('\n' + '='.repeat(60));
  console.log('テスト結果サマリー');
  console.log('='.repeat(60) + '\n');

  const successCount = results.filter(r => r.success).length;
  console.log(`成功: ${successCount}/${results.length}`);
  console.log(`失敗: ${results.length - successCount}/${results.length}`);

  results.forEach(result => {
    if (result.success) {
      console.log(`✅ ${result.productName}: ${result.totalResults}件`);
    } else {
      console.log(`❌ ${result.productName}: ${result.error}`);
    }
  });
}

// メイン実行
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length > 0) {
    // コマンドライン引数で商品名が指定された場合
    testProductNameSearch(args.join(' ')).then(result => {
      process.exit(result.success ? 0 : 1);
    });
  } else {
    // 引数なしの場合は全テストケースを実行
    runTests().catch(error => {
      console.error('テスト実行エラー:', error);
      process.exit(1);
    });
  }
}

module.exports = { testProductNameSearch };