#!/usr/bin/env python3
"""
統合検索でeBayの結果が含まれない問題をデバッグするスクリプト
"""

import requests
import json
import time

def test_individual_apis():
    """個別APIの動作確認"""
    base_url = "http://localhost:3001"
    query = "Nintendo Switch"
    
    print("=== 個別API動作確認 ===")
    
    apis = [
        ("Yahoo!ショッピング", "/api/search/yahoo"),
        ("eBay", "/api/search/ebay"),
        ("Mercari", "/api/search/mercari")
    ]
    
    results = {}
    
    for name, endpoint in apis:
        try:
            print(f"\n{name} API テスト中...")
            response = requests.get(f"{base_url}{endpoint}?query={query}&limit=5", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('results'):
                    results[name] = {
                        'success': True,
                        'count': len(data['results']),
                        'results': data['results'][:2]  # 最初の2件のみ表示
                    }
                    print(f"✅ {name}: {len(data['results'])}件取得成功")
                    for i, item in enumerate(data['results'][:2]):
                        print(f"  {i+1}. {item.get('title', 'タイトル不明')} - ¥{item.get('price', 0):,}")
                else:
                    results[name] = {'success': False, 'error': data.get('error', 'Unknown error')}
                    print(f"❌ {name}: {data.get('error', 'Unknown error')}")
            else:
                results[name] = {'success': False, 'error': f'HTTP {response.status_code}'}
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            results[name] = {'success': False, 'error': str(e)}
            print(f"❌ {name}: {str(e)}")
    
    return results

def test_unified_search():
    """統合検索の動作確認"""
    base_url = "http://localhost:3001"
    query = "Nintendo Switch"
    
    print("\n=== 統合検索動作確認 ===")
    
    try:
        print("統合検索 API テスト中...")
        response = requests.get(f"{base_url}/api/search/all?query={query}&limit=20", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('results'):
                print(f"✅ 統合検索: {len(data['results'])}件取得成功")
                
                # プラットフォーム別の集計
                platform_counts = {}
                for item in data['results']:
                    platform = item.get('platform', 'unknown')
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                print("プラットフォーム別結果数:")
                for platform, count in platform_counts.items():
                    print(f"  {platform}: {count}件")
                
                # 各プラットフォームの結果例を表示
                print("\n結果例:")
                for platform in ['yahoo', 'ebay', 'mercari']:
                    platform_items = [item for item in data['results'] if item.get('platform') == platform]
                    if platform_items:
                        print(f"\n{platform.upper()}:")
                        for i, item in enumerate(platform_items[:2]):
                            print(f"  {i+1}. {item.get('title', 'タイトル不明')} - ¥{item.get('price', 0):,}")
                    else:
                        print(f"\n{platform.upper()}: 結果なし ❌")
                
                return {
                    'success': True,
                    'total_count': len(data['results']),
                    'platform_counts': platform_counts,
                    'results': data['results']
                }
            else:
                print(f"❌ 統合検索: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error', 'Unknown error')}
        else:
            print(f"❌ 統合検索: HTTP {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ 統合検索: {str(e)}")
        return {'success': False, 'error': str(e)}

def analyze_issue(individual_results, unified_result):
    """問題の分析"""
    print("\n=== 問題分析 ===")
    
    # 個別APIの成功状況
    individual_success = {name: result['success'] for name, result in individual_results.items()}
    print("個別API成功状況:")
    for name, success in individual_success.items():
        status = "✅" if success else "❌"
        print(f"  {name}: {status}")
    
    # 統合検索の成功状況
    unified_success = unified_result.get('success', False)
    print(f"\n統合検索成功状況: {'✅' if unified_success else '❌'}")
    
    if unified_success:
        platform_counts = unified_result.get('platform_counts', {})
        
        # eBayが含まれているかチェック
        ebay_in_unified = 'ebay' in platform_counts and platform_counts['ebay'] > 0
        ebay_individual_success = individual_results.get('eBay', {}).get('success', False)
        
        print(f"\neBay結果の状況:")
        print(f"  個別eBay API: {'✅' if ebay_individual_success else '❌'}")
        print(f"  統合検索にeBay含まれる: {'✅' if ebay_in_unified else '❌'}")
        
        if ebay_individual_success and not ebay_in_unified:
            print("\n🔍 問題特定: eBay個別APIは動作するが、統合検索に含まれていない")
            print("考えられる原因:")
            print("  1. 統合検索のfetch処理でeBay APIへのリクエストが失敗している")
            print("  2. eBay APIのレスポンス形式が統合検索で期待される形式と異なる")
            print("  3. 統合検索のPromise.allSettled処理でeBayの結果が正しく処理されていない")
            print("  4. タイムアウトやネットワークエラーでeBayのみ失敗している")
            
        elif not ebay_individual_success:
            print("\n🔍 問題特定: eBay個別API自体が失敗している")
            
        else:
            print("\n✅ eBayは正常に統合検索に含まれています")

def main():
    print("統合検索eBay問題デバッグスクリプト開始")
    print("=" * 50)
    
    # 個別APIテスト
    individual_results = test_individual_apis()
    
    # 少し待機
    time.sleep(2)
    
    # 統合検索テスト
    unified_result = test_unified_search()
    
    # 問題分析
    analyze_issue(individual_results, unified_result)
    
    print("\n" + "=" * 50)
    print("デバッグ完了")

if __name__ == "__main__":
    main()
