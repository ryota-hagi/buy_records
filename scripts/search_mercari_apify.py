#!/usr/bin/env python3
import sys
import json
import os
import requests
import time
from urllib.parse import quote

def search_mercari_apify(keyword, limit=20):
    """
    Apify APIを使用してMercari検索を実行
    """
    try:
        # 環境変数からApify APIトークンを取得
        apify_token = os.getenv('APIFY_API_TOKEN')
        if not apify_token:
            print("APIFY_API_TOKENが設定されていません", file=sys.stderr)
            return []

        # Apify Actor ID (Mercari Scraper) - 実際に存在するActor
        actor_id = "jupri/mercari-scraper"
        
        # Apify API URL
        run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
        
        # 検索パラメータ
        run_input = {
            "searchKeyword": keyword,
            "maxItems": limit,
            "includeImages": True,
            "includeDescription": True
        }
        
        headers = {
            "Authorization": f"Bearer {apify_token}",
            "Content-Type": "application/json"
        }
        
        print(f"Apify Mercari検索開始: {keyword}", file=sys.stderr)
        
        # Actorを実行
        response = requests.post(run_url, json=run_input, headers=headers)
        response.raise_for_status()
        
        run_data = response.json()["data"]
        run_id = run_data["id"]
        
        print(f"Apify Run ID: {run_id}", file=sys.stderr)
        
        # 実行完了まで待機
        max_wait_time = 300  # 5分
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
        
        # 結果を統一フォーマットに変換
        formatted_results = []
        for item in raw_results:
            try:
                formatted_item = {
                    'platform': 'mercari',
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'image_url': item.get('imageUrl', ''),
                    'price': int(item.get('price', 0)) if item.get('price') else 0,
                    'shipping_fee': int(item.get('shippingFee', 0)) if item.get('shippingFee') else 0,
                    'total_price': int(item.get('price', 0)) + int(item.get('shippingFee', 0)) if item.get('price') else 0,
                    'condition': item.get('condition', ''),
                    'store_name': item.get('seller', ''),
                    'location': item.get('location', ''),
                    'currency': 'JPY',
                    # 旧形式との互換性
                    'item_title': item.get('title', ''),
                    'item_url': item.get('url', ''),
                    'item_image_url': item.get('imageUrl', ''),
                    'base_price': int(item.get('price', 0)) if item.get('price') else 0,
                    'item_condition': item.get('condition', ''),
                    'seller_name': item.get('seller', '')
                }
                formatted_results.append(formatted_item)
            except Exception as e:
                print(f"アイテム変換エラー: {str(e)}", file=sys.stderr)
                continue
        
        print(f"Mercari Apify検索完了: {len(formatted_results)}件", file=sys.stderr)
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
        print(f"Apifyフォールバック: 直接スクレイピング開始", file=sys.stderr)
        
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
        
        response = requests.get(search_url, headers=headers, timeout=300)
        response.raise_for_status()
        
        print(f"Mercari検索レスポンス取得成功 (ステータス: {response.status_code})", file=sys.stderr)
        print(f"レスポンスサイズ: {len(response.text)} 文字", file=sys.stderr)
        
        # HTMLパースは複雑なため、現在は空の結果を返す
        # 実際の実装では、BeautifulSoupやSeleniumを使用してHTMLを解析
        results = []
        
        print(f"Mercariフォールバック検索完了: {len(results)}件の結果", file=sys.stderr)
        return results
        
    except Exception as e:
        print(f"Mercariフォールバック検索エラー: {str(e)}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_mercari_apify.py <keyword> [limit]", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    try:
        # まずApify APIを試行
        results = search_mercari_apify(keyword, limit)
        
        # Apify APIが失敗した場合はフォールバック
        if not results:
            print("Apify API失敗、フォールバックを実行", file=sys.stderr)
            results = search_mercari_fallback(keyword, limit)
        
        # JSON_STARTとJSON_ENDマーカーで囲んで出力
        print("JSON_START")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print("JSON_END")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
