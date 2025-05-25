#!/usr/bin/env python3
"""
Mercari Apify Actor作成スクリプト
Apify APIを使用してMercari検索用のActorを作成・展開します。
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_env_vars():
    """環境変数を読み込み"""
    env_vars = {}
    env_files = ['.env.local', '.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
    
    return env_vars

def create_mercari_actor():
    """Mercari検索用のApify Actorを作成"""
    print("=" * 60)
    print("Mercari Apify Actor作成")
    print("=" * 60)
    
    env_vars = load_env_vars()
    api_token = env_vars.get('APIFY_API_TOKEN')
    
    if not api_token:
        print("❌ APIFY_API_TOKENが設定されていません")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Actorの設定
    actor_config = {
        "name": "mercari-search-scraper",
        "title": "Mercari Search Scraper",
        "description": "Scrapes Mercari search results for products",
        "isPublic": False,
        "seoTitle": "Mercari Search Scraper",
        "seoDescription": "Scrapes Mercari search results",
        "inputSchema": {
            "title": "Mercari Search Input",
            "type": "object",
            "schemaVersion": 1,
            "properties": {
                "keyword": {
                    "title": "Search Keyword",
                    "type": "string",
                    "description": "Keyword to search for on Mercari",
                    "example": "Nintendo Switch"
                },
                "maxItems": {
                    "title": "Maximum Items",
                    "type": "integer",
                    "description": "Maximum number of items to scrape",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100
                },
                "status": {
                    "title": "Item Status",
                    "type": "string",
                    "description": "Status of items to search for",
                    "default": "on_sale",
                    "enum": ["on_sale", "sold_out"],
                    "enumTitles": ["On Sale", "Sold Out"]
                }
            },
            "required": ["keyword"]
        },
        "readme": "# Mercari Search Scraper\n\nThis actor scrapes Mercari search results for specified keywords."
    }
    
    try:
        print("🔄 Actorを作成中...")
        response = requests.post(
            "https://api.apify.com/v2/acts",
            headers=headers,
            json=actor_config,
            timeout=30
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 201:
            actor_data = response.json()["data"]
            actor_id = actor_data["id"]
            print(f"✅ Actor作成成功: {actor_id}")
            return actor_id
        else:
            print(f"❌ Actor作成失敗: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Actor作成エラー: {str(e)}")
        return None

def upload_actor_source_code(actor_id):
    """Actorのソースコードをアップロード"""
    print("\n" + "=" * 60)
    print("Actorソースコードアップロード")
    print("=" * 60)
    
    env_vars = load_env_vars()
    api_token = env_vars.get('APIFY_API_TOKEN')
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # メインのソースコード
    main_js = '''const Apify = require('apify');
const { PuppeteerCrawler } = Apify;

Apify.main(async () => {
    const input = await Apify.getInput();
    const { keyword, maxItems = 50, status = 'on_sale' } = input;
    
    if (!keyword) {
        throw new Error('Keyword is required');
    }
    
    console.log(`Starting Mercari search for: ${keyword}`);
    
    const requestQueue = await Apify.openRequestQueue();
    
    // 検索URLを構築
    const searchUrl = `https://jp.mercari.com/search?keyword=${encodeURIComponent(keyword)}&status=${status}&sort=price_asc`;
    await requestQueue.addRequest({ url: searchUrl });
    
    const crawler = new PuppeteerCrawler({
        requestQueue,
        launchContext: {
            launchOptions: {
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            }
        },
        handlePageFunction: async ({ page, request }) => {
            console.log(`Processing: ${request.url}`);
            
            try {
                // ページが読み込まれるまで待機
                await page.waitForSelector('body', { timeout: 30000 });
                await page.waitForTimeout(5000);
                
                const items = [];
                let itemCount = 0;
                
                // 商品要素を取得
                const itemElements = await page.$$('[id^="m"]');
                console.log(`Found ${itemElements.length} potential items`);
                
                for (const element of itemElements) {
                    if (itemCount >= maxItems) break;
                    
                    try {
                        // aria-label属性から情報を抽出
                        const ariaLabel = await element.getAttribute('aria-label');
                        if (!ariaLabel) continue;
                        
                        // タイトルと価格を抽出
                        const match = ariaLabel.match(/(.+)の画像\\s+(?:売り切れ\\s+)?([0-9,]+)円/);
                        if (!match) continue;
                        
                        const title = match[1];
                        const price = parseInt(match[2].replace(/,/g, ''));
                        
                        // 商品IDを取得
                        const itemId = await element.getAttribute('id');
                        if (!itemId) continue;
                        
                        // 商品URLを構築
                        const itemUrl = `https://jp.mercari.com/item/${itemId}`;
                        
                        // 商品画像を取得
                        let imageUrl = '';
                        try {
                            const imgElement = await element.$('img');
                            if (imgElement) {
                                imageUrl = await imgElement.getAttribute('src') || '';
                            }
                        } catch (e) {
                            console.log('Image extraction failed:', e.message);
                        }
                        
                        const item = {
                            search_term: keyword,
                            item_id: itemId.startsWith('m') ? itemId.substring(1) : itemId,
                            title: title,
                            price: price,
                            currency: 'JPY',
                            status: status === 'sold_out' ? 'sold_out' : 'active',
                            sold_date: status === 'sold_out' ? new Date().toISOString() : null,
                            condition: '新品',
                            url: itemUrl,
                            image_url: imageUrl,
                            seller: 'メルカリ出品者',
                            platform: 'mercari',
                            scraped_at: new Date().toISOString()
                        };
                        
                        items.push(item);
                        itemCount++;
                        
                    } catch (e) {
                        console.log('Error processing item:', e.message);
                        continue;
                    }
                }
                
                console.log(`Successfully scraped ${items.length} items for keyword: ${keyword}`);
                
                // 結果を保存
                if (items.length > 0) {
                    await Apify.pushData(items);
                } else {
                    console.log('No items found, pushing empty result');
                    await Apify.pushData([{
                        search_term: keyword,
                        message: 'No items found',
                        scraped_at: new Date().toISOString()
                    }]);
                }
                
            } catch (e) {
                console.log('Error during scraping:', e.message);
                await Apify.pushData([{
                    search_term: keyword,
                    error: e.message,
                    scraped_at: new Date().toISOString()
                }]);
            }
        },
        maxRequestsPerCrawl: 1,
        requestHandlerTimeoutSecs: 120
    });
    
    await crawler.run();
    console.log('Mercari scraping finished.');
});
'''
    
    # package.jsonファイル
    package_json = '''{
  "name": "mercari-search-scraper",
  "version": "1.0.0",
  "description": "Scrapes Mercari search results",
  "main": "main.js",
  "dependencies": {
    "apify": "^2.3.2",
    "puppeteer": "^19.0.0"
  },
  "scripts": {
    "start": "node main.js"
  }
}
'''
    
    # ソースコードをアップロード
    source_files = [
        {
            "name": "main.js",
            "content": main_js
        },
        {
            "name": "package.json",
            "content": package_json
        }
    ]
    
    try:
        for file_info in source_files:
            print(f"📁 アップロード中: {file_info['name']}")
            
            response = requests.put(
                f"https://api.apify.com/v2/acts/{actor_id}/versions/0.0/source-code/{file_info['name']}",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "text/plain"
                },
                data=file_info['content'],
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ {file_info['name']} アップロード成功")
            else:
                print(f"   ❌ {file_info['name']} アップロード失敗: {response.text}")
                return False
        
        print("✅ 全ソースコードのアップロード完了")
        return True
        
    except Exception as e:
        print(f"❌ ソースコードアップロードエラー: {str(e)}")
        return False

def build_actor(actor_id):
    """Actorをビルド"""
    print("\n" + "=" * 60)
    print("Actorビルド")
    print("=" * 60)
    
    env_vars = load_env_vars()
    api_token = env_vars.get('APIFY_API_TOKEN')
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🔄 Actorビルド開始...")
        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/builds",
            headers=headers,
            json={"tag": "latest"},
            timeout=30
        )
        
        if response.status_code == 201:
            build_data = response.json()["data"]
            build_id = build_data["id"]
            print(f"✅ ビルド開始: {build_id}")
            
            # ビルド完了まで待機
            print("⏳ ビルド完了を待機中...")
            max_wait_time = 300  # 5分
            wait_interval = 10   # 10秒間隔
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # ビルド状況を確認
                status_response = requests.get(
                    f"https://api.apify.com/v2/acts/{actor_id}/builds/{build_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    build_status = status_response.json()["data"]["status"]
                    print(f"   ビルド状況: {build_status}")
                    
                    if build_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                        if build_status == "SUCCEEDED":
                            print("✅ ビルド成功")
                            return True
                        else:
                            print(f"❌ ビルド失敗: {build_status}")
                            return False
            
            print("❌ ビルドタイムアウト")
            return False
        else:
            print(f"❌ ビルド開始失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ビルドエラー: {str(e)}")
        return False

def test_actor(actor_id):
    """Actorをテスト実行"""
    print("\n" + "=" * 60)
    print("Actorテスト実行")
    print("=" * 60)
    
    env_vars = load_env_vars()
    api_token = env_vars.get('APIFY_API_TOKEN')
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # テスト用の入力データ
    test_input = {
        "keyword": "Nintendo Switch",
        "maxItems": 5,
        "status": "on_sale"
    }
    
    try:
        print("🔄 テスト実行開始...")
        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers=headers,
            json=test_input,
            timeout=30
        )
        
        if response.status_code == 201:
            run_data = response.json()["data"]
            run_id = run_data["id"]
            print(f"✅ テスト実行開始: {run_id}")
            
            # 実行完了まで待機
            print("⏳ 実行完了を待機中...")
            max_wait_time = 180  # 3分
            wait_interval = 10   # 10秒間隔
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # 実行状況を確認
                status_response = requests.get(
                    f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    run_status = status_response.json()["data"]["status"]
                    print(f"   実行状況: {run_status}")
                    
                    if run_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                        if run_status == "SUCCEEDED":
                            print("✅ テスト実行成功")
                            
                            # 結果を取得
                            results_response = requests.get(
                                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items",
                                headers=headers
                            )
                            
                            if results_response.status_code == 200:
                                results = results_response.json()
                                print(f"📊 取得結果: {len(results)}件")
                                if results:
                                    print(f"サンプル: {results[0].get('title', 'N/A')[:50]}...")
                            
                            return True
                        else:
                            print(f"❌ テスト実行失敗: {run_status}")
                            return False
            
            print("❌ テスト実行タイムアウト")
            return False
        else:
            print(f"❌ テスト実行開始失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        return False

def update_env_with_actor_id(actor_id):
    """環境変数ファイルにActor IDを追加"""
    print(f"\n📝 Actor IDを環境変数に追加: {actor_id}")
    
    env_line = f"\n# Mercari Apify Actor ID\nMERCARI_APIFY_ACTOR_ID={actor_id}\n"
    
    with open('.env.local', 'a', encoding='utf-8') as f:
        f.write(env_line)
    
    print("✅ .env.localに追加完了")

def main():
    """メイン処理"""
    print("🚀 Mercari Apify Actor作成スクリプト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Actor作成プロセス
    actor_id = create_mercari_actor()
    if not actor_id:
        print("❌ Actor作成に失敗しました")
        return
    
    # ソースコードアップロード
    if not upload_actor_source_code(actor_id):
        print("❌ ソースコードアップロードに失敗しました")
        return
    
    # Actorビルド
    if not build_actor(actor_id):
        print("❌ Actorビルドに失敗しました")
        return
    
    # テスト実行
    if not test_actor(actor_id):
        print("❌ Actorテストに失敗しました")
        return
    
    # 環境変数に追加
    update_env_with_actor_id(actor_id)
    
    print("\n" + "=" * 60)
    print("Mercari Apify Actor作成完了")
    print("=" * 60)
    print(f"🎯 Actor ID: {actor_id}")
    print("📋 完了した作業:")
    print("1. Actorの作成")
    print("2. ソースコードのアップロード")
    print("3. Actorのビルド")
    print("4. テスト実行")
    print("5. 環境変数への追加")
    print("\n✅ Mercari検索機能が利用可能になりました！")

if __name__ == "__main__":
    main()
