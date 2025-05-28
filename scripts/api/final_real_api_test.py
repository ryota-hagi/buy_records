#!/usr/bin/env python3
"""
すべてのAPIが実際のAPIで動作することを確認する最終テストスクリプト
"""

import requests
import json
import time

def test_all_apis():
    """すべてのAPIをテスト"""
    base_url = "http://localhost:3000"
    query = "Nintendo Switch"
    
    print("🚀 全API実装テスト開始")
    print("=" * 60)
    
    apis = [
        ("Yahoo!ショッピング", "/api/search/yahoo"),
        ("eBay", "/api/search/ebay"),
        ("Mercari", "/api/search/mercari")
    ]
    
    results = {}
    
    for name, endpoint in apis:
        print(f"\n🔍 {name} API テスト中...")
        try:
            response = requests.get(f"{base_url}{endpoint}?query={query}&limit=5", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('results'):
                    results[name] = {
                        'success': True,
                        'count': len(data['results']),
                        'is_real_api': not data.get('note', '').startswith('フォールバック'),
                        'results': data['results'][:2]
                    }
                    
                    api_type = "実API" if results[name]['is_real_api'] else "フォールバック"
                    print(f"  ✅ {name}: {len(data['results'])}件取得成功 ({api_type})")
                    
                    for i, item in enumerate(data['results'][:2]):
                        print(f"    {i+1}. {item.get('title', 'タイトル不明')} - ¥{item.get('price', 0):,}")
                        
                    if not results[name]['is_real_api']:
                        print(f"  ⚠️  {name}: フォールバック実装を使用中")
                else:
                    results[name] = {'success': False, 'error': data.get('error', 'Unknown error')}
                    print(f"  ❌ {name}: {data.get('error', 'Unknown error')}")
            else:
                results[name] = {'success': False, 'error': f'HTTP {response.status_code}'}
                print(f"  ❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            results[name] = {'success': False, 'error': str(e)}
            print(f"  ❌ {name}: {str(e)}")
    
    return results

def test_unified_search():
    """統合検索をテスト"""
    base_url = "http://localhost:3000"
    query = "Nintendo Switch"
    
    print(f"\n🔄 統合検索テスト中...")
    
    try:
        response = requests.get(f"{base_url}/api/search/all?query={query}&limit=20", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('results'):
                # プラットフォーム別集計
                platform_counts = {}
                for item in data['results']:
                    platform = item.get('platform', 'unknown')
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                total_results = len(data['results'])
                print(f"  ✅ 統合検索: {total_results}件取得成功")
                
                for platform, count in platform_counts.items():
                    platform_name = {
                        'yahoo_shopping': 'Yahoo!ショッピング',
                        'ebay': 'eBay',
                        'mercari': 'Mercari'
                    }.get(platform, platform)
                    print(f"    - {platform_name}: {count}件")
                
                return {
                    'success': True,
                    'total_results': total_results,
                    'platform_counts': platform_counts
                }
            else:
                print(f"  ❌ 統合検索: {data.get('error', 'Unknown error')}")
                return {'success': False, 'error': data.get('error', 'Unknown error')}
        else:
            print(f"  ❌ 統合検索: HTTP {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"  ❌ 統合検索: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    print("🎯 Yahoo!ショッピング・eBay・Mercari API")
    print("   実API実装最終確認テスト")
    print("=" * 60)
    
    # 個別APIテスト
    individual_results = test_all_apis()
    
    # 少し待機
    time.sleep(2)
    
    # 統合検索テスト
    unified_result = test_unified_search()
    
    print("\n" + "=" * 60)
    print("📋 最終結果")
    print("=" * 60)
    
    # 個別API結果
    print("個別API結果:")
    real_api_count = 0
    fallback_count = 0
    error_count = 0
    
    for name, result in individual_results.items():
        if result.get('success'):
            if result.get('is_real_api'):
                print(f"  ✅ {name}: 実API動作中 ({result['count']}件)")
                real_api_count += 1
            else:
                print(f"  ⚠️  {name}: フォールバック動作中 ({result['count']}件)")
                fallback_count += 1
        else:
            print(f"  ❌ {name}: エラー ({result.get('error', 'Unknown')})")
            error_count += 1
    
    # 統合検索結果
    if unified_result.get('success'):
        total = unified_result.get('total_results', 0)
        platforms = len(unified_result.get('platform_counts', {}))
        print(f"\n統合検索結果:")
        print(f"  ✅ 正常動作: {total}件 ({platforms}プラットフォーム)")
    else:
        print(f"\n統合検索結果:")
        print(f"  ❌ エラー: {unified_result.get('error', 'Unknown')}")
    
    # 総合評価
    print(f"\n" + "=" * 60)
    print("🎯 総合評価")
    print("=" * 60)
    
    if real_api_count == 3:
        print("🎉 完璧！すべてのAPIが実APIで動作しています")
        grade = "A+"
    elif real_api_count >= 2:
        print("✅ 良好！大部分のAPIが実APIで動作しています")
        grade = "A"
    elif real_api_count >= 1:
        print("⚠️  改善の余地あり。一部のAPIが実APIで動作しています")
        grade = "B"
    else:
        print("❌ 要改善。すべてのAPIがフォールバックまたはエラーです")
        grade = "C"
    
    print(f"評価: {grade}")
    print(f"実API動作: {real_api_count}/3")
    print(f"フォールバック: {fallback_count}/3")
    print(f"エラー: {error_count}/3")
    
    if unified_result.get('success'):
        print("統合検索: ✅ 正常動作")
    else:
        print("統合検索: ❌ エラー")
    
    print("\n" + "=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    main()
