/**
 * 本番環境での検索機能テストスクリプト
 */

const https = require('https');

// 本番環境のURL（実際のVercelのURLに置き換えてください）
const PRODUCTION_URL = 'https://buy-records.vercel.app'; // または実際のURL

async function testProductionAPI() {
  console.log('本番環境での検索APIテストを開始します...');
  console.log(`テスト対象: ${PRODUCTION_URL}`);
  
  try {
    // 検索タスクを作成
    const createTaskResponse = await makeRequest('POST', '/api/search/tasks', {
      jan_code: '4902370548501'
    });
    
    console.log('✅ 検索タスク作成:', createTaskResponse.success ? '成功' : '失敗');
    
    if (createTaskResponse.success) {
      const taskId = createTaskResponse.task.id;
      console.log(`📝 タスクID: ${taskId}`);
      console.log(`📝 タスク名: ${createTaskResponse.task.name}`);
      console.log(`📝 ステータス: ${createTaskResponse.task.status}`);
      
      // 少し待ってからタスクの状態を確認
      console.log('\n⏳ 5秒待機してからタスクの状態を確認します...');
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // タスクの詳細を取得
      const taskDetailResponse = await makeRequest('GET', `/api/search/tasks/${taskId}`);
      
      if (taskDetailResponse.success) {
        const task = taskDetailResponse.task;
        console.log(`\n📊 タスク詳細:`);
        console.log(`   ステータス: ${task.status}`);
        console.log(`   結果数: ${task.results_count || 0}件`);
        
        if (task.status === 'completed' && task.results && task.results.length > 0) {
          console.log('\n🎉 検索成功! 結果の一部:');
          task.results.slice(0, 3).forEach((result, index) => {
            console.log(`   ${index + 1}. ${result.item_title}`);
            console.log(`      価格: ¥${result.total_price?.toLocaleString() || 'N/A'}`);
            console.log(`      プラットフォーム: ${result.platform}`);
          });
        } else if (task.status === 'running') {
          console.log('⏳ タスクはまだ実行中です。しばらく待ってから再度確認してください。');
        } else if (task.status === 'failed') {
          console.log('❌ タスクが失敗しました。');
          if (task.error) {
            console.log(`   エラー: ${task.error}`);
          }
        }
      }
      
      // タスク一覧も確認
      console.log('\n📋 最近のタスク一覧:');
      const tasksResponse = await makeRequest('GET', '/api/search/tasks?limit=3');
      
      if (tasksResponse.success && tasksResponse.tasks) {
        tasksResponse.tasks.forEach((task, index) => {
          console.log(`   ${index + 1}. ${task.name} (${task.status}) - ${task.results_count || 0}件`);
        });
      }
    }
    
    console.log('\n✅ 本番環境テスト完了');
    
  } catch (error) {
    console.error('❌ 本番環境テストでエラーが発生しました:', error.message);
    
    if (error.message.includes('python')) {
      console.error('🚨 まだPythonエラーが発生しています。デプロイが完了していない可能性があります。');
    }
  }
}

function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(PRODUCTION_URL + path);
    
    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'ProductionTest/1.0'
      }
    };
    
    if (data) {
      const postData = JSON.stringify(data);
      options.headers['Content-Length'] = Buffer.byteLength(postData);
    }
    
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonResponse = JSON.parse(responseData);
          resolve(jsonResponse);
        } catch (parseError) {
          reject(new Error(`JSON解析エラー: ${parseError.message}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (data) {
      req.write(JSON.stringify(data));
    }
    
    req.end();
  });
}

// テスト実行
if (require.main === module) {
  testProductionAPI()
    .then(() => {
      console.log('\n🎯 テスト完了');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 予期しないエラー:', error);
      process.exit(1);
    });
}

module.exports = { testProductionAPI };
