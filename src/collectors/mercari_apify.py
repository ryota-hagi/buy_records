"""
Mercari Apify APIクライアント
Apify APIを使用してMercariの商品情報を取得します。
"""

import time
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..utils.config import get_config

class MercariApifyClient:
    """Apify APIを使用してMercariからデータを取得するクライアントクラス"""
    
    def __init__(self):
        """
        MercariApifyClientを初期化します。
        """
        self.api_token = get_config("APIFY_API_TOKEN")
        self.base_url = "https://api.apify.com/v2"
        self.actor_id = None  # 後で設定
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.delay = float(get_config("MERCARI_REQUEST_DELAY", "2.0"))
        
        if not self.api_token:
            print("警告: APIFY_API_TOKENが設定されていません。Apify APIは利用できません。")
    
    def create_mercari_actor(self) -> str:
        """
        Mercari検索用のApify Actorを作成します。
        
        Returns:
            str: 作成されたActorのID
        """
        if not self.api_token:
            raise ValueError("APIFY_API_TOKENが設定されていません。")
        
        actor_config = {
            "name": "mercari-search-scraper",
            "title": "Mercari Search Scraper",
            "description": "Scrapes Mercari search results for products",
            "isPublic": False,
            "seoTitle": "Mercari Search Scraper",
            "seoDescription": "Scrapes Mercari search results",
            "sourceCode": self._get_actor_source_code(),
            "dockerfile": "FROM apify/actor-node:16",
            "inputSchema": self._get_input_schema(),
            "readme": "# Mercari Search Scraper\n\nThis actor scrapes Mercari search results for specified keywords."
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/acts",
                headers=self.headers,
                json=actor_config
            )
            response.raise_for_status()
            
            actor_data = response.json()["data"]
            self.actor_id = actor_data["id"]
            print(f"Mercari Actor created successfully: {self.actor_id}")
            
            return self.actor_id
        except Exception as e:
            print(f"Error creating Mercari actor: {str(e)}")
            raise
    
    def _get_actor_source_code(self) -> str:
        """
        Mercari検索用のActorソースコードを返します。
        
        Returns:
            str: Actorのソースコード
        """
        return '''
const Apify = require('apify');
const { PuppeteerCrawler } = Apify;

Apify.main(async () => {
    const input = await Apify.getInput();
    const { keyword, maxItems = 50, status = 'on_sale' } = input;
    
    if (!keyword) {
        throw new Error('Keyword is required');
    }
    
    const requestQueue = await Apify.openRequestQueue();
    
    // 検索URLを構築
    const searchUrl = `https://jp.mercari.com/search?keyword=${encodeURIComponent(keyword)}&status=${status}&sort=price_asc`;
    await requestQueue.addRequest({ url: searchUrl });
    
    const crawler = new PuppeteerCrawler({
        requestQueue,
        launchContext: {
            launchOptions: {
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            }
        },
        handlePageFunction: async ({ page, request }) => {
            console.log(`Processing: ${request.url}`);
            
            // ページが読み込まれるまで待機
            await page.waitForSelector('body', { timeout: 30000 });
            await page.waitForTimeout(5000);
            
            const items = [];
            let itemCount = 0;
            
            try {
                // 商品要素を取得
                const itemElements = await page.$$('[id^="m"]');
                
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
                            seller: 'メルカリ出品者'
                        };
                        
                        items.push(item);
                        itemCount++;
                        
                    } catch (e) {
                        console.log('Error processing item:', e.message);
                        continue;
                    }
                }
                
                console.log(`Found ${items.length} items for keyword: ${keyword}`);
                
                // 結果を保存
                await Apify.pushData(items);
                
            } catch (e) {
                console.log('Error during scraping:', e.message);
                throw e;
            }
        },
        maxRequestsPerCrawl: 1,
        requestHandlerTimeoutSecs: 60
    });
    
    await crawler.run();
    console.log('Crawler finished.');
});
'''
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """
        ActorのInputスキーマを返します。
        
        Returns:
            Dict[str, Any]: Inputスキーマ
        """
        return {
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
        }
    
    def run_actor(self, keyword: str, max_items: int = 50, status: str = "on_sale") -> List[Dict[str, Any]]:
        """
        Actorを実行してMercari検索結果を取得します。
        
        Args:
            keyword: 検索キーワード
            max_items: 取得する最大アイテム数
            status: アイテムのステータス（"on_sale" または "sold_out"）
            
        Returns:
            List[Dict[str, Any]]: 検索結果のリスト
        """
        if not self.api_token:
            print(f"Mercari Apify検索をスキップしました（API Token未設定）: {keyword}")
            return []
        
        if not self.actor_id:
            print("Actor IDが設定されていません。Actorを作成します...")
            self.create_mercari_actor()
        
        # Actorの実行
        run_input = {
            "keyword": keyword,
            "maxItems": max_items,
            "status": status
        }
        
        try:
            # Actorを実行
            response = requests.post(
                f"{self.base_url}/acts/{self.actor_id}/runs",
                headers=self.headers,
                json=run_input
            )
            response.raise_for_status()
            
            run_data = response.json()["data"]
            run_id = run_data["id"]
            
            print(f"Actor run started: {run_id}")
            
            # 実行完了まで待機
            max_wait_time = 300  # 5分
            wait_interval = 10   # 10秒間隔
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # 実行状況を確認
                status_response = requests.get(
                    f"{self.base_url}/acts/{self.actor_id}/runs/{run_id}",
                    headers=self.headers
                )
                status_response.raise_for_status()
                
                run_status = status_response.json()["data"]["status"]
                print(f"Actor run status: {run_status}")
                
                if run_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                    break
            
            if run_status != "SUCCEEDED":
                print(f"Actor run failed with status: {run_status}")
                return []
            
            # 結果を取得
            results_response = requests.get(
                f"{self.base_url}/acts/{self.actor_id}/runs/{run_id}/dataset/items",
                headers=self.headers
            )
            results_response.raise_for_status()
            
            results = results_response.json()
            print(f"Retrieved {len(results)} items from Mercari")
            
            return results
            
        except Exception as e:
            print(f"Error running Mercari actor for '{keyword}': {str(e)}")
            return []
    
    def search_active_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        出品中のアイテムを検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 出品中アイテムのリスト
        """
        return self.run_actor(keyword, limit, "on_sale")
    
    def search_sold_items(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        売り切れ済みのアイテムを検索します。
        
        Args:
            keyword: 検索キーワード
            limit: 取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 売り切れ済みアイテムのリスト
        """
        return self.run_actor(keyword, limit, "sold_out")
    
    def get_complete_data(self, keyword: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        キーワードの完全なデータ（出品中と売り切れ済み）を取得します。
        
        Args:
            keyword: 検索キーワード
            limit: 各カテゴリ（出品中・売り切れ済み）ごとに取得する結果の最大数
            
        Returns:
            List[Dict[str, Any]]: 完全なデータ
        """
        try:
            # 出品中のアイテムを取得
            print(f"出品中のアイテムを取得中...")
            active_items = self.search_active_items(keyword, limit)
            print(f"出品中のアイテム数: {len(active_items)}")
            
            time.sleep(self.delay)  # APIレート制限対応
            
            # 売り切れ済みのアイテムを取得
            print(f"売り切れ済みのアイテムを取得中...")
            sold_items = self.search_sold_items(keyword, limit)
            print(f"売り切れ済みのアイテム数: {len(sold_items)}")
            
            # 統計情報を計算
            active_prices = [item["price"] for item in active_items if item["price"] > 0]
            sold_prices = [item["price"] for item in sold_items if item["price"] > 0]
            
            lowest_active_price = min(active_prices) if active_prices else 0
            avg_sold_price = sum(sold_prices) / len(sold_prices) if sold_prices else 0
            
            # 中央値を計算
            median_sold_price = 0
            if sold_prices:
                sold_prices.sort()
                mid = len(sold_prices) // 2
                if len(sold_prices) % 2 == 0 and len(sold_prices) > 1:
                    median_sold_price = (sold_prices[mid - 1] + sold_prices[mid]) / 2
                else:
                    median_sold_price = sold_prices[mid]
            
            # 結果を統合
            all_items = []
            
            # 出品中アイテムに統計情報を追加
            for item in active_items:
                # URLが空の場合はスキップ（モックデータを除外）
                if not item.get("url"):
                    continue
                    
                item.update({
                    "lowest_active_price": lowest_active_price,
                    "active_listings_count": len(active_items),
                    "avg_sold_price": round(avg_sold_price, 2),
                    "median_sold_price": round(median_sold_price, 2),
                    "sold_count": len(sold_items)
                })
                all_items.append(item)
            
            # 売り切れ済みアイテムに統計情報を追加
            for item in sold_items:
                # URLが空の場合はスキップ（モックデータを除外）
                if not item.get("url"):
                    continue
                    
                item.update({
                    "lowest_active_price": lowest_active_price,
                    "active_listings_count": len(active_items),
                    "avg_sold_price": round(avg_sold_price, 2),
                    "median_sold_price": round(median_sold_price, 2),
                    "sold_count": len(sold_items)
                })
                all_items.append(item)
            
            # データがない場合は空のリストを返す
            if not all_items:
                print(f"'{keyword}'の検索結果はありませんでした。")
            
            return all_items
        except Exception as e:
            print(f"Error getting complete data for '{keyword}': {str(e)}")
            return []
    
    def set_actor_id(self, actor_id: str):
        """
        既存のActor IDを設定します。
        
        Args:
            actor_id: 使用するActor ID
        """
        self.actor_id = actor_id
        print(f"Actor ID set to: {actor_id}")
    
    def list_actors(self) -> List[Dict[str, Any]]:
        """
        利用可能なActorのリストを取得します。
        
        Returns:
            List[Dict[str, Any]]: Actorのリスト
        """
        if not self.api_token:
            print("API Token未設定のため、Actorリストを取得できません。")
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/acts",
                headers=self.headers
            )
            response.raise_for_status()
            
            actors = response.json()["data"]["items"]
            return actors
        except Exception as e:
            print(f"Error listing actors: {str(e)}")
            return []
