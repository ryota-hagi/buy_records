#!/usr/bin/env python3
"""
Apify Web Scraperを使用したMercari検索
汎用的なWeb Scraperを使用してMercariの商品情報を取得
"""

import sys
import json
import os
import requests
import time
from urllib.parse import quote

def search_mercari_with_web_scraper(keyword, limit=20):
    """
    Apify Web Scraperを使用してMercari検索を実行
    """
    try:
        # 環境変数からApify APIトークンを取得
        apify_token = os.getenv('APIFY_API_TOKEN')
        if not apify_token:
            print("APIFY_API_TOKENが設定されていません", file=sys.stderr)
            return []

        # Apify Web Scraper (公式、実行回数169,731,323回)
        actor_id = "apify/web-scraper"
        
        # Apify API URL
        run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
        
        # Mercari検索URL
        search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale"
        
        # Web Scraperの設定
        run_input = {
            "startUrls": [{"url": search_url}],
            "globs": [{"glob": "https://jp.mercari.com/search*"}],
            "pseudoUrls": [],
            "pageFunction": """
async function pageFunction(context) {
    const { page, request, log } = context;
    
    // ページが読み込まれるまで待機
    await page.waitForSelector('body', { timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const items = [];
    
    try {
        // 商品要素を取得（Mercariの商品リスト）
        const itemElements = await page.$$('[id^="m"]');
        
        log.info(`Found ${itemElements.length} item elements`);
        
        for (let i = 0; i < Math.min(itemElements.length, """ + str(limit) + """); i++) {
            const element = itemElements[i];
            
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
                    log.info('Image extraction failed:', e.message);
                }
                
                const item = {
                    platform: 'mercari',
                    title: title,
                    url: itemUrl,
                    image_url: imageUrl,
                    price: price,
                    shipping_fee: 0,
                    total_price: price,
                    condition: '新品',
                    store_name: 'メルカリ出品者',
                    location: '',
                    currency: 'JPY',
                    // 旧形式との互換性
                    item_title: title,
                    item_url: itemUrl,
                    item_image_url: imageUrl,
                    base_price: price,
                    item_condition: '新品',
                    seller_name: 'メルカリ出品者'
                };
                
                items.push(item);
                
            } catch (e) {
                log.info('Error processing item:', e.message);
                continue;
            }
        }
        
        log.info(`Successfully extracted ${items.length} items`);
        
        return items;
        
    } catch (e) {
        log.error('Error during scraping:', e.message);
        return [];
    }
}
""",
            "proxyConfiguration": {"useApifyProxy": True},
            "maxRequestRetries": 3,
            "maxPagesPerCrawl": 1,
            "maxResultsPerCrawl": limit,
            "maxCrawlingDepth": 0,
            "maxConcurrency": 1,
            "pageLoadTimeoutSecs": 60,
            "pageFunctionTimeoutSecs": 60
        }
        
        headers = {
            "Authorization": f"Bearer {apify_token}",
            "Content-Type": "application/json"
        }
        
        print(f"Apify Web Scraper開始: {keyword}", file=sys.stderr)
        print(f"検索URL: {search_url}", file=sys.stderr)
        
        # Actorを実行
        response = requests.post(run_url, json=run_input, headers=headers)
        response.raise_for_status()
        
        run_data = response.json()["data"]
        run_id = run_data["id"]
        
        print(f"Apify Run ID: {run_id}", file=sys.stderr)
        
        # 実行完了まで待機
        max_wait_time = 180  # 3分
        wait_interval = 10   # 10秒間隔
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            
            # 実行状況を確認
            status_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}"
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            
            run_status = status_response.json()["data"]["status"]
            print(f"Apify実行状況: {run_status} ({elapsed_time}秒経過)", file=sys.stderr)
            
            if run_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
        
        if run_status != "SUCCEEDED":
            print(f"Apify実行失敗: {run_status}", file=sys.stderr)
            return []
        
        # 結果を取得
        results_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items"
        results_response = requests.get(results_url, headers=headers)
        results_response.raise_for_status()
        
        raw_results = results_response.json()
        print(f"Apify結果取得: {len(raw_results)}件", file=sys.stderr)
        
        # 結果をフラット化（Web Scraperは配列の配列を返す可能性がある）
        formatted_results = []
        for result in raw_results:
            if isinstance(result, list):
                formatted_results.extend(result)
            elif isinstance(result, dict):
                formatted_results.append(result)
        
        print(f"Mercari Web Scraper検索完了: {len(formatted_results)}件", file=sys.stderr)
        return formatted_results
        
    except requests.exceptions.RequestException as e:
        print(f"Apify APIリクエストエラー: {str(e)}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Apify検索エラー: {str(e)}", file=sys.stderr)
        return []

def search_mercari_fallback(keyword, limit=20):
    """
    Apify APIが利用できない場合のフォールバック（直接スクレイピング）
    """
    try:
        print(f"フォールバック: 直接スクレイピング開始", file=sys.stderr)
        
        # 実際のMercari検索を実行
        search_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&status=on_sale"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"Mercari検索URL: {search_url}", file=sys.stderr)
        
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Mercari検索レスポンス取得成功 (ステータス: {response.status_code})", file=sys.stderr)
        print(f"レスポンスサイズ: {len(response.text)} 文字", file=sys.stderr)
        
        # 簡単なHTMLパースを試行
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mercariの商品要素を検索
        items = []
        product_elements = soup.find_all(attrs={'id': lambda x: x and x.startswith('m')})
        
        print(f"見つかった商品要素: {len(product_elements)}件", file=sys.stderr)
        
        for element in product_elements[:limit]:
            try:
                aria_label = element.get('aria-label', '')
                if not aria_label:
                    continue
                
                # タイトルと価格を抽出
                import re
                match = re.search(r'(.+)の画像\s+(?:売り切れ\s+)?([0-9,]+)円', aria_label)
                if not match:
                    continue
                
                title = match.group(1)
                price = int(match.group(2).replace(',', ''))
                item_id = element.get('id', '')
                
                if item_id:
                    item_url = f"https://jp.mercari.com/item/{item_id}"
                    
                    # 画像URL取得
                    img_element = element.find('img')
                    image_url = img_element.get('src', '') if img_element else ''
                    
                    item = {
                        'platform': 'mercari',
                        'title': title,
                        'url': item_url,
                        'image_url': image_url,
                        'price': price,
                        'shipping_fee': 0,
                        'total_price': price,
                        'condition': '新品',
                        'store_name': 'メルカリ出品者',
                        'location': '',
                        'currency': 'JPY',
                        # 旧形式との互換性
                        'item_title': title,
                        'item_url': item_url,
                        'item_image_url': image_url,
                        'base_price': price,
                        'item_condition': '新品',
                        'seller_name': 'メルカリ出品者'
                    }
                    items.append(item)
                    
            except Exception as e:
                print(f"商品解析エラー: {str(e)}", file=sys.stderr)
                continue
        
        print(f"フォールバック検索完了: {len(items)}件の結果", file=sys.stderr)
        return items
        
    except Exception as e:
        print(f"フォールバック検索エラー: {str(e)}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_web_scraper.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    try:
        # まずApify Web Scraperを試行
        results = search_mercari_with_web_scraper(keyword, limit)
        
        # Apify APIが失敗した場合はフォールバック
        if not results:
            print("Apify Web Scraper失敗、フォールバックを実行", file=sys.stderr)
            results = search_mercari_fallback(keyword, limit)
        
        print(json.dumps(results, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
