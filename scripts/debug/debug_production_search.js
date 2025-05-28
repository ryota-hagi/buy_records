/**
 * 本番環境検索デバッグスクリプト
 * 詳細なログとエラー情報を取得
 */

const axios = require('axios');

// テスト用JANコード
const TEST_JAN_CODE = '4902370540734';
const PRODUCTION_URL = 'https://buy-records.vercel.app';

/**
 * 環境変数デバッグ
 */
async function debugEnvironment() {
  try {
    console.log('🔍 環境変数デバッグ');
    console.log('===================');
    
    const response = await axios.get(`${PRODUCTION_URL}/api/debug/env`, {
      timeout: 10000
    });
    
    console.log('環境変数状況:');
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
    
  } catch (error) {
    console.error('❌ 環境変数取得エラー:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.status, error.response.data);
    }
    return null;
  }
}

/**
 * 統合検索エンジンの直接テスト
 */
async function testUnifiedSearchEngine() {
  try {
    console.log('\n🚀 統合検索エンジン直接テスト');
    console.log('===============================');
    
    // 検索テストエンドポイントがあるかチェック
    const response = await axios.post(`${PRODUCTION_URL}/api/search/test`, {
      jan_code: TEST_JAN_CODE
    }, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ 統合検索エンジンテスト結果:');
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
    
  } catch (error) {
    console.error('❌ 統合検索エンジンテストエラー:', error.message);
    if (error.response) {
      console.error('ステータス:', error.response.status);
      console.error('レスポンス:', error.response.data);
    }
    return null;
  }
}

/**
 * 個別プラットフォームテスト
 */
async function testIndividualPlatforms() {
  console.log('\n🔧 個別プラットフォームテスト');
  console.log('============================');
  
  // Yahoo Shopping APIテスト
  try {
    console.log('\n📍 Yahoo Shopping APIテスト...');
    const yahooResponse = await axios.get(`${PRODUCTION_URL}/api/search/yahoo`, {
      params: { jan_code: TEST_JAN_CODE },
      timeout: 15000
    });
    console.log('✅ Yahoo Shopping:', yahooResponse.data);
  } catch (error) {
    console.error('❌ Yahoo Shopping エラー:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
  }
  
  // eBay APIテスト
  try {
    console.log('\n📍 eBay APIテスト...');
    const ebayResponse = await axios.get(`${PRODUCTION_URL}/api/search/ebay`, {
      params: { product_name: '大乱闘スマッシュブラザーズ SPECIAL' },
      timeout: 15000
    });
    console.log('✅ eBay:', ebayResponse.data);
  } catch (error) {
    console.error('❌ eBay エラー:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
  }
}

/**
 * タスク詳細ログ取得
 */
async function getTaskLogs(taskId) {
  try {
    console.log(`\n📋 タスクログ取得: ${taskId}`);
    console.log('========================');
    
    const response = await axios.get(`${PRODUCTION_URL}/api/search/tasks/${taskId}`, {
      timeout: 10000
    });
    
    const task = response.data;
    
    console.log('タスク詳細:');
    console.log(`- ID: ${task.id}`);
    console.log(`- 名前: ${task.name}`);
    console.log(`- ステータス: ${task.status}`);
    console.log(`- 作成日時: ${task.created_at}`);
    console.log(`- 更新日時: ${task.updated_at}`);
    console.log(`- 完了日時: ${task.completed_at || 'なし'}`);
    
    if (task.processing_logs && task.processing_logs.length > 0) {
      console.log('\n処理ログ:');
      task.processing_logs.forEach((log, index) => {
        console.log(`${index + 1}. [${log.timestamp}] ${log.status}: ${log.message}`);
      });
    } else {
      console.log('処理ログ: なし');
    }
    
    if (task.result) {
      console.log('\nタスク結果:');
      console.log(JSON.stringify(task.result, null, 2));
    } else {
      console.log('タスク結果: なし');
    }
    
    if (task.error) {
      console.log(`\nエラー: ${task.error}`);
    }
    
    return task;
    
  } catch (error) {
    console.error('❌ タスクログ取得エラー:', error.message);
    return null;
  }
}

/**
 * メイン実行
 */
async function main() {
  console.log('🐛 本番環境検索デバッグ');
  console.log('========================');
  
  // 1. 環境変数チェック
  const envData = await debugEnvironment();
  
  // 2. 統合検索エンジン直接テスト
  const searchResult = await testUnifiedSearchEngine();
  
  // 3. 個別プラットフォームテスト
  await testIndividualPlatforms();
  
  // 4. 新しいタスクを作成してログを確認
  try {
    console.log('\n🎯 新しいタスク作成とログ確認');
    console.log('==============================');
    
    const createResponse = await axios.post(`${PRODUCTION_URL}/api/search/tasks`, {
      jan_code: TEST_JAN_CODE
    }, {
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const taskId = createResponse.data.task.id;
    console.log(`✅ タスク作成成功: ${taskId}`);
    
    // 少し待ってからログを取得
    await new Promise(resolve => setTimeout(resolve, 10000));
    await getTaskLogs(taskId);
    
  } catch (error) {
    console.error('❌ タスク作成エラー:', error.message);
  }
  
  console.log('\n🏁 デバッグ完了');
}

// 実行
main().catch(console.error);
