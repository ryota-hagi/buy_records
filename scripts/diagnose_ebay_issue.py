#!/usr/bin/env python3
"""
eBay検索問題の詳細診断スクリプト
現在の問題を特定し、解決策を提案します。
"""

import sys
import json
import requests
import time
import os
from urllib.parse import quote
import subprocess

def test_ebay_finding_api():
    """eBay Finding APIの直接テスト"""
    print("=== eBay Finding API テスト ===")
    
    app_id = os.getenv('EBAY_APP_ID', 'ariGaT-records-PRD-1a6ee1171-104bfaa4')
    api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
    
    # テスト用の検索キーワード
    test_keywords = [
        "Nintendo Switch",
        "iPhone",
        "Sony PlayStation",
        "サントリー 緑茶 伊右衛門"  # 日本語キーワード
    ]
    
    for keyword in test_keywords:
        print(f"\n--- キーワード: {keyword} ---")
        
        params = {
            'OPERATION-NAME': 'findItemsByKeywords',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': app_id,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'keywords': keyword,
            'paginationInput.entriesPerPage': 5,
            'sortOrder': 'PricePlusShipping'
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=15)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # レスポンス構造を確認
                if 'findItemsByKeywordsResponse' in data:
                    search_result = data['findItemsByKeywordsResponse'][0].get('searchResult', [{}])[0]
                    items = search_result.get('item', [])
                    count = search_result.get('@count', 0)
                    
                    print(f"検索結果数: {count}")
                    print(f"取得アイテム数: {len(items)}")
                    
                    if items:
                        # 最初のアイテムの詳細を表示
                        first_item = items[0]
                        title = first_item.get('title', [''])[0]
                        price = first_item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', 0)
                        print(f"最初のアイテム: {title}")
                        print(f"価格: ${price}")
                    else:
                        print("アイテムが見つかりませんでした")
                        
                    # エラーメッセージを確認
                    if 'errorMessage' in data.get('findItemsByKeywordsResponse', [{}])[0]:
                        error = data['findItemsByKeywordsResponse'][0]['errorMessage']
                        print(f"APIエラー: {error}")
                        
                else:
                    print("予期しないレスポンス構造")
                    print(json.dumps(data, indent=2)[:500])
            else:
                print(f"HTTPエラー: {response.text[:200]}")
                
        except Exception as e:
            print(f"例外発生: {str(e)}")

def test_ebay_web_scraping():
    """eBay Webスクレイピングのテスト"""
    print("\n=== eBay Webスクレイピング テスト ===")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    test_keywords = ["Nintendo Switch", "iPhone"]
    
    for keyword in test_keywords:
        print(f"\n--- キーワード: {keyword} ---")
        
        try:
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}&_sacat=0&_sop=15"
            print(f"URL: {search_url}")
            
            response = requests.get(search_url, headers=headers, timeout=15)
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンスサイズ: {len(response.text)} 文字")
            
            if response.status_code == 200:
                # 基本的なHTML構造を確認
                html = response.text
                
                # 商品タイトルの存在確認
                if 's-item__title' in html:
                    print("✓ 商品タイトル要素が見つかりました")
                else:
                    print("✗ 商品タイトル要素が見つかりません")
                
                # 価格要素の存在確認
                if 's-item__price' in html:
                    print("✓ 価格要素が見つかりました")
                else:
                    print("✗ 価格要素が見つかりません")
                
                # ボット検出の確認
                if 'robot' in html.lower() or 'captcha' in html.lower():
                    print("⚠ ボット検出の可能性があります")
                
                # 検索結果数の確認
                if 'results' in html.lower():
                    print("✓ 検索結果ページのようです")
                else:
                    print("✗ 検索結果ページではない可能性があります")
                    
            else:
                print(f"HTTPエラー: {response.status_code}")
                
        except Exception as e:
            print(f"例外発生: {str(e)}")

def test_translation_service():
    """翻訳サービスのテスト"""
    print("\n=== 翻訳サービス テスト ===")
    
    try:
        # Google翻訳APIの設定確認
        credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON')
        if credentials_json:
            print("✓ Google Cloud認証情報が設定されています")
            
            # 簡単な翻訳テスト
            japanese_text = "サントリー 緑茶 伊右衛門 600ml"
            print(f"翻訳テスト: {japanese_text}")
            
            # 翻訳スクリプトを実行
            result = subprocess.run([
                'python', 'scripts/translate_for_ebay.py', japanese_text
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                translated = result.stdout.strip()
                print(f"翻訳結果: {translated}")
            else:
                print(f"翻訳エラー: {result.stderr}")
                
        else:
            print("✗ Google Cloud認証情報が設定されていません")
            
    except Exception as e:
        print(f"翻訳テスト例外: {str(e)}")

def test_exchange_rate_service():
    """為替レートサービスのテスト"""
    print("\n=== 為替レートサービス テスト ===")
    
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        if response.status_code == 200:
            data = response.json()
            jpy_rate = data.get('rates', {}).get('JPY', 0)
            print(f"✓ 為替レート取得成功: 1 USD = {jpy_rate} JPY")
        else:
            print(f"✗ 為替レート取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"為替レート例外: {str(e)}")

def test_current_ebay_script():
    """現在のeBay検索スクリプトのテスト"""
    print("\n=== 現在のeBay検索スクリプト テスト ===")
    
    test_keywords = ["Nintendo Switch", "iPhone"]
    
    for keyword in test_keywords:
        print(f"\n--- キーワード: {keyword} ---")
        
        try:
            result = subprocess.run([
                'python', 'scripts/search_ebay_real_only.py', keyword, '5'
            ], capture_output=True, text=True, timeout=60)
            
            print(f"終了コード: {result.returncode}")
            print(f"標準エラー出力:")
            print(result.stderr)
            
            if result.returncode == 0:
                # JSON結果を解析
                output = result.stdout
                json_start = output.find('JSON_START')
                json_end = output.find('JSON_END')
                
                if json_start != -1 and json_end != -1:
                    json_str = output[json_start + len('JSON_START'):json_end].strip()
                    try:
                        results = json.loads(json_str)
                        print(f"✓ 検索成功: {len(results)}件取得")
                        
                        if results:
                            first_item = results[0]
                            print(f"最初のアイテム: {first_item.get('title', 'N/A')}")
                            print(f"価格: {first_item.get('price', 0)} JPY")
                        
                    except json.JSONDecodeError as e:
                        print(f"✗ JSON解析エラー: {str(e)}")
                        print(f"JSON文字列: {json_str[:200]}")
                else:
                    print("✗ JSONマーカーが見つかりません")
                    print(f"出力: {output[:200]}")
            else:
                print(f"✗ スクリプト実行失敗")
                
        except subprocess.TimeoutExpired:
            print("✗ スクリプト実行タイムアウト")
        except Exception as e:
            print(f"✗ スクリプト実行例外: {str(e)}")

def main():
    print("eBay検索問題の詳細診断を開始します...")
    print("=" * 50)
    
    # 環境変数の確認
    print("=== 環境変数確認 ===")
    ebay_app_id = os.getenv('EBAY_APP_ID')
    if ebay_app_id:
        print(f"✓ EBAY_APP_ID: {ebay_app_id}")
    else:
        print("✗ EBAY_APP_IDが設定されていません")
    
    # 各テストを実行
    test_ebay_finding_api()
    test_ebay_web_scraping()
    test_translation_service()
    test_exchange_rate_service()
    test_current_ebay_script()
    
    print("\n" + "=" * 50)
    print("診断完了")

if __name__ == "__main__":
    main()
