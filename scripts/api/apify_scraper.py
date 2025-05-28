#!/usr/bin/env python3
"""
Apifyを使用した実際の商品スクレイピング
JANコード 4901777300446 (サントリー 緑茶 伊右衛門 600ml ペット) の検索
"""

import requests
import json
import time
import sys
import os
from typing import List, Dict, Any

# Apify設定
APIFY_API_TOKEN = "apify_api_CkhJNITqcJeFNgPkQAbgIOJrond1Ha10zIN2"
APIFY_BASE_URL = "https://api.apify.com/v2"

class ApifyMercariScraper:
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def search_mercari(self, search_term: str, max_items: int = 20) -> List[Dict[str, Any]]:
        """メルカリで商品を検索"""
        print(f"メルカリで検索中: {search_term}")
        
        # Apify Mercari Scraperを使用
        actor_id = "apify/mercari-scraper"
        
        # 検索パラメータ
        run_input = {
            "searchTerms": [search_term],
            "maxItems": max_items,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        }
        
        try:
            # Actorを実行
            response = requests.post(
                f"{APIFY_BASE_URL}/acts/{actor_id}/runs",
                headers=self.headers,
                json=run_input
            )
            
            if response.status_code != 201:
                print(f"エラー: Apify Actor実行失敗 - {response.status_code}")
                print(response.text)
                return []
            
            run_data = response.json()
            run_id = run_data["data"]["id"]
            
            print(f"Apify実行ID: {run_id}")
            print("スクレイピング実行中...")
            
            # 実行完了を待機
            max_wait_time = 300  # 5分
            wait_time = 0
            
            while wait_time < max_wait_time:
                time.sleep(10)
                wait_time += 10
                
                # 実行状況を確認
                status_response = requests.get(
                    f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                    headers=self.headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["data"]["status"]
                    
                    print(f"ステータス: {status} ({wait_time}秒経過)")
                    
                    if status == "SUCCEEDED":
                        break
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        print(f"スクレイピング失敗: {status}")
                        return []
            
            if wait_time >= max_wait_time:
                print("タイムアウト: スクレイピングが完了しませんでした")
                return []
            
            # 結果を取得
            dataset_response = requests.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}/dataset/items",
                headers=self.headers
            )
            
            if dataset_response.status_code == 200:
                items = dataset_response.json()
                print(f"取得した商品数: {len(items)}")
                return items
            else:
                print(f"結果取得エラー: {dataset_response.status_code}")
                return []
                
        except Exception as e:
            print(f"Apifyスクレイピングエラー: {e}")
            return []

class ApifyYahooAuctionScraper:
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def search_yahoo_auction(self, search_term: str, max_items: int = 20) -> List[Dict[str, Any]]:
        """Yahoo!オークションで商品を検索"""
        print(f"Yahoo!オークションで検索中: {search_term}")
        
        # 汎用Webスクレイパーを使用
        actor_id = "apify/web-scraper"
        
        # Yahoo!オークション検索URL
        search_url = f"https://auctions.yahoo.co.jp/search/search?p={search_term.replace(' ', '+')}"
        
        run_input = {
            "startUrls": [{"url": search_url}],
            "linkSelector": "a[href*='/auction/']",
            "pageFunction": """
                async function pageFunction(context) {
                    const { page, request } = context;
                    
                    // 商品リストページの場合
                    if (request.url.includes('/search/')) {
                        const items = await page.$$eval('.Product', elements => {
                            return elements.slice(0, 20).map(el => {
                                const titleEl = el.querySelector('.Product__title a');
                                const priceEl = el.querySelector('.Product__price');
                                const imageEl = el.querySelector('.Product__image img');
                                
                                return {
                                    title: titleEl ? titleEl.textContent.trim() : '',
                                    url: titleEl ? titleEl.href : '',
                                    price: priceEl ? priceEl.textContent.trim() : '',
                                    image: imageEl ? imageEl.src : ''
                                };
                            });
                        });
                        
                        return items.filter(item => item.title && item.url);
                    }
                    
                    return null;
                }
            """,
            "maxRequestsPerCrawl": 50,
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        try:
            # Actorを実行
            response = requests.post(
                f"{APIFY_BASE_URL}/acts/{actor_id}/runs",
                headers=self.headers,
                json=run_input
            )
            
            if response.status_code != 201:
                print(f"エラー: Yahoo!オークションスクレイピング失敗 - {response.status_code}")
                return []
            
            run_data = response.json()
            run_id = run_data["data"]["id"]
            
            print(f"Yahoo!オークション実行ID: {run_id}")
            
            # 実行完了を待機（簡略版）
            time.sleep(30)
            
            # 結果を取得
            dataset_response = requests.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}/dataset/items",
                headers=self.headers
            )
            
            if dataset_response.status_code == 200:
                items = dataset_response.json()
                print(f"Yahoo!オークション取得商品数: {len(items)}")
                return items
            else:
                return []
                
        except Exception as e:
            print(f"Yahoo!オークションスクレイピングエラー: {e}")
            return []

def main():
    """メイン実行関数"""
    print("=== Apifyを使用したJANコード商品検索 ===")
    print("JANコード: 4901777300446")
    print("商品: サントリー 緑茶 伊右衛門 600ml ペット")
    print()
    
    # 検索キーワード
    search_terms = [
        "サントリー 伊右衛門 600ml",
        "伊右衛門 緑茶 600ml",
        "4901777300446"
    ]
    
    all_results = []
    
    # メルカリ検索
    mercari_scraper = ApifyMercariScraper()
    for term in search_terms:
        mercari_results = mercari_scraper.search_mercari(term, max_items=10)
        for item in mercari_results:
            if item and 'title' in item and 'url' in item:
                all_results.append({
                    'platform': 'mercari',
                    'title': item.get('title', ''),
                    'price': item.get('price', ''),
                    'url': item.get('url', ''),
                    'image': item.get('image', ''),
                    'seller': item.get('seller', ''),
                    'condition': item.get('condition', '')
                })
    
    # Yahoo!オークション検索
    yahoo_scraper = ApifyYahooAuctionScraper()
    for term in search_terms[:1]:  # 1つのキーワードのみ
        yahoo_results = yahoo_scraper.search_yahoo_auction(term, max_items=10)
        for item in yahoo_results:
            if item and 'title' in item and 'url' in item:
                all_results.append({
                    'platform': 'yahoo_auction',
                    'title': item.get('title', ''),
                    'price': item.get('price', ''),
                    'url': item.get('url', ''),
                    'image': item.get('image', ''),
                    'seller': '',
                    'condition': ''
                })
    
    print(f"\n=== 検索結果 ===")
    print(f"総取得商品数: {len(all_results)}")
    
    # 結果をJSONファイルに保存
    output_file = "jan_search_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"結果を {output_file} に保存しました")
    
    # 上位10件を表示
    print("\n=== 上位10件 ===")
    for i, item in enumerate(all_results[:10], 1):
        print(f"{i}. [{item['platform']}] {item['title']}")
        print(f"   価格: {item['price']}")
        print(f"   URL: {item['url']}")
        print()

if __name__ == "__main__":
    main()
