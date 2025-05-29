const axios = require('axios');

async function testAPIs() {
  const baseUrl = 'http://localhost:3000';
  const testQuery = '4988006763173';
  
  console.log('=== API動作確認テスト ===\n');
  
  // 1. Yahoo Shopping API
  console.log('1. Yahoo Shopping API テスト');
  try {
    const yahooResponse = await axios.get(`${baseUrl}/api/search/yahoo`, {
      params: { jan_code: testQuery },
      timeout: 10000
    });
    console.log(`✅ Yahoo: ${yahooResponse.data.results?.length || 0}件の結果`);
  } catch (error) {
    console.log(`❌ Yahoo: ${error.message}`);
  }
  
  // 2. Mercari API
  console.log('\n2. Mercari API テスト');
  try {
    const mercariResponse = await axios.get(`${baseUrl}/api/search/mercari`, {
      params: { query: testQuery },
      timeout: 30000
    });
    console.log(`✅ Mercari: ${mercariResponse.data.results?.length || 0}件の結果`);
  } catch (error) {
    console.log(`❌ Mercari: ${error.message}`);
  }
  
  // 3. eBay API  
  console.log('\n3. eBay API テスト');
  try {
    const ebayResponse = await axios.get(`${baseUrl}/api/search/ebay`, {
      params: { query: testQuery },
      timeout: 10000
    });
    console.log(`✅ eBay: ${ebayResponse.data.results?.length || 0}件の結果`);
  } catch (error) {
    console.log(`❌ eBay: ${error.message}`);
  }
  
  // 4. 統合検索 API
  console.log('\n4. 統合検索 API テスト');
  try {
    const allResponse = await axios.post(`${baseUrl}/api/search/all`, {
      keyword: testQuery
    }, {
      timeout: 60000
    });
    console.log(`✅ 統合検索: 合計${allResponse.data.totalResults || 0}件の結果`);
    if (allResponse.data.results) {
      Object.entries(allResponse.data.results).forEach(([platform, results]) => {
        console.log(`  - ${platform}: ${results.length}件`);
      });
    }
  } catch (error) {
    console.log(`❌ 統合検索: ${error.message}`);
  }
}

testAPIs().catch(console.error);