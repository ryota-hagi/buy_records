#!/usr/bin/env python3
"""
モックデータ削除の動作確認テスト
eBayとMercariのAPIエンドポイントをテストして、モックデータが返されないことを確認
"""

import requests
import json
import sys
import time

def test_ebay_api():
    """eBay APIのテスト"""
    print("=== eBay API テスト ===")
    
    # テスト用商品名（日本語）
    test_product = "Nintendo Switch"
    
    try:
        # eBay APIエンドポイントをテスト
        url = "http://localhost:3000/api/search/ebay"
        params = {
            "product_name": test_product,
            "limit": 5
        }
        
        print(f"リクエスト: {url}")
        print(f"パラメータ: {params}")
        
        response = requests.get(url, params=params, timeout=30)
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('total_results', 0)}件の結果")
            
            # モックデータチェック
            results = data.get('results', [])
            mock_detected = False
            
            for item in results:
                # モックデータの特徴をチェック
                if 'sample' in item.get('url', '').lower():
                    print(f"⚠️  モックデータ検出: {item.get('url')}")
                    mock_detected = True
                elif 'eBay商品' in item.get('title', ''):
                    print(f"⚠️  モックデータ検出: {item.get('title')}")
                    mock_detected = True
                elif item.get('price') in [3500, 4200]:  # 固定価格
                    print(f"⚠️  固定価格検出: {item.get('price')}円")
                    mock_detected = True
            
            if not mock_detected and results:
                print("✅ モックデータは検出されませんでした")
                print(f"サンプル結果: {results[0].get('title', 'N/A')}")
            elif not results:
                print("⚠️  結果が0件です（API制限の可能性）")
            
        else:
            print(f"エラー: {response.text}")
            
    except Exception as e:
        print(f"eBay APIテストエラー: {str(e)}")

def test_mercari_api():
    """Mercari APIのテスト"""
    print("\n=== Mercari API テスト ===")
    
    # テスト用商品名
    test_product = "Nintendo Switch"
    
    try:
        # Mercari APIエンドポイントをテスト
        url = "http://localhost:3000/api/search/mercari"
        params = {
            "product_name": test_product,
            "limit": 5
        }
        
        print(f"リクエスト: {url}")
        print(f"パラメータ: {params}")
        
        response = requests.get(url, params=params, timeout=60)  # Mercariは時間がかかる可能性
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('total_results', 0)}件の結果")
            
            # モックデータチェック
            results = data.get('results', [])
            mock_detected = False
            
            for item in results:
                # モックデータの特徴をチェック
                if 'sample' in item.get('url', '').lower():
                    print(f"⚠️  モックデータ検出: {item.get('url')}")
                    mock_detected = True
                elif 'メルカリ商品' in item.get('title', ''):
                    print(f"⚠️  モックデータ検出: {item.get('title')}")
                    mock_detected = True
                elif item.get('price') in [1500, 2800]:  # 固定価格
                    print(f"⚠️  固定価格検出: {item.get('price')}円")
                    mock_detected = True
            
            if not mock_detected and results:
                print("✅ モックデータは検出されませんでした")
                print(f"サンプル結果: {results[0].get('title', 'N/A')}")
            elif not results:
                print("⚠️  結果が0件です（Apify設定の可能性）")
            
        else:
            print(f"エラー: {response.text}")
            
    except Exception as e:
        print(f"Mercari APIテストエラー: {str(e)}")

def test_translation_script():
    """翻訳スクリプトのテスト"""
    print("\n=== 翻訳スクリプト テスト ===")
    
    import subprocess
    import os
    
    try:
        script_path = "scripts/translate_for_ebay.py"
        test_text = "Nintendo Switch"
        
        print(f"テスト: {test_text}")
        
        result = subprocess.run(
            ["python", script_path, test_text],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            translated = result.stdout.strip()
            print(f"翻訳結果: {translated}")
            
            if translated != test_text:
                print("✅ 翻訳が実行されました")
            else:
                print("⚠️  翻訳されていない可能性があります")
        else:
            print(f"翻訳エラー: {result.stderr}")
            
    except Exception as e:
        print(f"翻訳スクリプトテストエラー: {str(e)}")

def test_mercari_script():
    """Mercariスクリプトのテスト"""
    print("\n=== Mercariスクリプト テスト ===")
    
    import subprocess
    
    try:
        script_path = "scripts/search_mercari_apify.py"
        test_keyword = "Nintendo Switch"
        
        print(f"テスト: {test_keyword}")
        print("注意: Apify APIが設定されていない場合はエラーになります")
        
        result = subprocess.run(
            ["python", script_path, test_keyword, "3"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"✅ スクリプト実行成功: {len(data)}件取得")
                if data:
                    print(f"サンプル: {data[0].get('title', 'N/A')}")
            except json.JSONDecodeError:
                print(f"JSON解析エラー: {result.stdout}")
        else:
            print(f"スクリプトエラー: {result.stderr}")
            
    except Exception as e:
        print(f"Mercariスクリプトテストエラー: {str(e)}")

def main():
    print("モックデータ削除の動作確認テストを開始します...")
    print("注意: Next.jsサーバーが http://localhost:3000 で動作している必要があります")
    
    # 翻訳スクリプトテスト
    test_translation_script()
    
    # Mercariスクリプトテスト
    test_mercari_script()
    
    # APIエンドポイントテスト
    test_ebay_api()
    test_mercari_api()
    
    print("\n=== テスト完了 ===")
    print("モックデータが検出された場合は、該当箇所の修正が必要です。")

if __name__ == "__main__":
    main()
