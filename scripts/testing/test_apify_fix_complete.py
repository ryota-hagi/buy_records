#!/usr/bin/env python3
"""
Apify統合問題の完全解決テスト
修正されたMercari検索機能の動作確認
"""

import requests
import json
import sys
import time

def test_all_apis():
    """全APIの動作確認"""
    print("=== 修正後のAPI統合テスト ===")
    
    base_url = "http://localhost:3000"
    test_product = "Nintendo Switch"
    
    results = {}
    
    # eBay APIテスト
    print("\n1. eBay API テスト")
    try:
        response = requests.get(f"{base_url}/api/search/ebay", 
                              params={"product_name": test_product, "limit": 5}, 
                              timeout=30)
        if response.status_code == 200:
            data = response.json()
            results['ebay'] = {
                'status': 'success',
                'count': data.get('total_results', 0),
                'data_source': data.get('data_source', 'unknown')
            }
            print(f"✅ eBay: {data.get('total_results', 0)}件取得")
        else:
            results['ebay'] = {'status': 'error', 'message': response.text}
            print(f"❌ eBay: エラー {response.status_code}")
    except Exception as e:
        results['ebay'] = {'status': 'error', 'message': str(e)}
        print(f"❌ eBay: 例外 {str(e)}")
    
    # Mercari APIテスト（修正版）
    print("\n2. Mercari API テスト（修正版）")
    try:
        response = requests.get(f"{base_url}/api/search/mercari", 
                              params={"product_name": test_product, "limit": 5}, 
                              timeout=60)
        if response.status_code == 200:
            data = response.json()
            results['mercari'] = {
                'status': 'success',
                'count': data.get('total_results', 0),
                'data_source': data.get('data_source', 'unknown')
            }
            print(f"✅ Mercari: {data.get('total_results', 0)}件取得")
            print(f"   データソース: {data.get('data_source', 'unknown')}")
        else:
            results['mercari'] = {'status': 'error', 'message': response.text}
            print(f"❌ Mercari: エラー {response.status_code}")
    except Exception as e:
        results['mercari'] = {'status': 'error', 'message': str(e)}
        print(f"❌ Mercari: 例外 {str(e)}")
    
    # Yahoo Shopping APIテスト
    print("\n3. Yahoo Shopping API テスト")
    try:
        response = requests.get(f"{base_url}/api/search/yahoo", 
                              params={"product_name": test_product, "limit": 5}, 
                              timeout=30)
        if response.status_code == 200:
            data = response.json()
            results['yahoo'] = {
                'status': 'success',
                'count': data.get('total_results', 0),
                'data_source': data.get('data_source', 'unknown')
            }
            print(f"✅ Yahoo: {data.get('total_results', 0)}件取得")
        else:
            results['yahoo'] = {'status': 'error', 'message': response.text}
            print(f"❌ Yahoo: エラー {response.status_code}")
    except Exception as e:
        results['yahoo'] = {'status': 'error', 'message': str(e)}
        print(f"❌ Yahoo: 例外 {str(e)}")
    
    # 統合検索APIテスト
    print("\n4. 統合検索 API テスト")
    try:
        response = requests.get(f"{base_url}/api/search/all", 
                              params={"product_name": test_product, "limit": 5}, 
                              timeout=90)
        if response.status_code == 200:
            data = response.json()
            total_results = sum(platform.get('total_results', 0) for platform in data.get('results', {}).values())
            results['unified'] = {
                'status': 'success',
                'total_count': total_results,
                'platforms': list(data.get('results', {}).keys())
            }
            print(f"✅ 統合検索: 合計{total_results}件取得")
            for platform, platform_data in data.get('results', {}).items():
                print(f"   {platform}: {platform_data.get('total_results', 0)}件")
        else:
            results['unified'] = {'status': 'error', 'message': response.text}
            print(f"❌ 統合検索: エラー {response.status_code}")
    except Exception as e:
        results['unified'] = {'status': 'error', 'message': str(e)}
        print(f"❌ 統合検索: 例外 {str(e)}")
    
    return results

def evaluate_results(results):
    """結果の評価"""
    print("\n=== 結果評価 ===")
    
    success_count = 0
    total_count = 0
    
    for platform, result in results.items():
        total_count += 1
        if result.get('status') == 'success':
            success_count += 1
            if platform == 'mercari':
                count = result.get('count', 0)
                if count > 0:
                    print(f"✅ {platform}: 成功 ({count}件) - Apify問題解決！")
                else:
                    print(f"⚠️  {platform}: 成功だが0件 - さらなる改善が必要")
            else:
                print(f"✅ {platform}: 成功 ({result.get('count', 0)}件)")
        else:
            print(f"❌ {platform}: 失敗 - {result.get('message', '不明なエラー')}")
    
    success_rate = (success_count / total_count) * 100
    print(f"\n成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    if success_rate >= 75:
        print("🎉 総合評価: A+ (優秀)")
    elif success_rate >= 50:
        print("👍 総合評価: B (良好)")
    else:
        print("⚠️  総合評価: C (要改善)")
    
    # Mercari特別評価
    mercari_result = results.get('mercari', {})
    if mercari_result.get('status') == 'success' and mercari_result.get('count', 0) > 0:
        print("\n🔧 Apify統合問題: 解決済み ✅")
    else:
        print("\n🔧 Apify統合問題: 未解決 ❌")

def main():
    print("Apify統合問題の完全解決テストを開始します...")
    print("注意: Next.jsサーバーが http://localhost:3000 で動作している必要があります")
    
    try:
        results = test_all_apis()
        evaluate_results(results)
        
        # 結果をJSONファイルに保存
        with open('apify_fix_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n詳細結果を apify_fix_test_results.json に保存しました")
        
    except Exception as e:
        print(f"テスト実行エラー: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
