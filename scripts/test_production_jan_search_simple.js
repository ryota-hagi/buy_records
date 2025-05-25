/**
 * 本番環境JANコード検索テストスクリプト（簡易版）
 * 統合検索エンジンの動作確認
 */

const axios = require('axios');

// テスト用JANコード
const TEST_JAN_CODE = '4902370540734'; // 大乱闘スマッシュブラザーズ SPECIAL

// 本番環境URL
const PRODUCTION_URL = 'https://buy-records.vercel.app';

/**
 * JANコード検索タスク作成テスト
 */
async function testJanSearch() {
  try {
    console.log(`🚀 JANコード検索テスト開始: ${TEST_JAN_CODE}`);
    console.log(`📍 URL: ${PRODUCTION_URL}`);
    
    // 1. 検索タスク作成
    console.log('\n1️⃣ 検索タスク作成中...');
    const createResponse = await axios.post(`${PRODUCTION_URL}/api/search/tasks`, {
      jan_code: TEST_JAN_CODE
    }, {
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ タスク作成成功:');
    console.log(`- タスクID: ${createResponse.data.task.id}`);
    console.log(`- 商品名: ${createResponse.data.task.name}`);
    console.log(`- ステータス: ${createResponse.data.task.status}`);
    
    const taskId = createResponse.data.task.id;
    
    // 2. タスク完了まで待機
    console.log('\n2️⃣ タスク完了待機中...');
    let attempts = 0;
    const maxAttempts = 12; // 最大60秒待機
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // 5秒待機
      attempts++;
      
      try {
        const statusResponse = await axios.get(`${PRODUCTION_URL}/api/search/tasks/${taskId}`, {
          timeout: 10000
        });
        
        const task = statusResponse.data;
        console.log(`⏳ 試行 ${attempts}/${maxAttempts} - ステータス: ${task.status}`);
        
        if (task.status === 'completed') {
          console.log('\n✅ タスク完了！');
          console.log('📊 検索結果:');
          console.log(`- 総件数: ${task.results_count}件`);
          
          if (task.result && task.result.integrated_results) {
            const results = task.result.integrated_results;
            console.log(`- 統合結果: ${results.count}件`);
            
            if (task.result.platform_results) {
              const platforms = task.result.platform_results;
              console.log(`- Yahoo Shopping: ${platforms.yahoo_shopping?.length || 0}件`);
              console.log(`- メルカリ: ${platforms.mercari?.length || 0}件`);
              console.log(`- eBay: ${platforms.ebay?.length || 0}件`);
            }
            
            if (results.items && results.items.length > 0) {
              console.log('\n🏆 最安値商品:');
              const cheapest = results.items[0];
              console.log(`- 商品名: ${cheapest.item_title}`);
              console.log(`- 価格: ¥${cheapest.total_price}`);
              console.log(`- プラットフォーム: ${cheapest.platform}`);
            }
          }
          
          return true;
          
        } else if (task.status === 'failed') {
          console.log('\n❌ タスク失敗');
          console.log(`エラー: ${task.error || '不明なエラー'}`);
          return false;
        }
        
      } catch (error) {
        console.log(`⚠️ ステータス確認エラー (試行 ${attempts}): ${error.message}`);
      }
    }
    
    console.log('\n⏰ タイムアウト: タスクが完了しませんでした');
    return false;
    
  } catch (error) {
    console.error('\n❌ テスト失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.status, error.response.data);
    }
    return false;
  }
}

/**
 * メイン実行
 */
async function main() {
  console.log('🔍 本番環境JANコード検索テスト');
  console.log('=====================================');
  
  const success = await testJanSearch();
  
  console.log('\n=====================================');
  if (success) {
    console.log('🎉 テスト成功！統合検索エンジンが正常に動作しています。');
  } else {
    console.log('💥 テスト失敗。問題を確認してください。');
  }
}

// 実行
main().catch(console.error);
