#!/usr/bin/env python3
"""
更新されたeBayトークンのテスト
EBAY_USER_TOKEN: v^1.1#i^1#p^3#r^1#I^3#f^0#t^Ul4xMF85Ojc2ODYxQ0ZGOUI5OTMyNTU3QzAxM0Q5MDRGRkNGM0NDXzFfMSNFXjI2MA==
"""

import requests
import json
import time
from datetime import datetime

def test_updated_apis():
    """更新後のAPIをテスト"""
    
    print("🚀 更新されたeBayトークンのテスト開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # 1. 個別APIテスト
    apis_to_test = [
        {
            "name": "Yahoo!ショッピング",
            "endpoint": "/api/search/yahoo",
            "expected": "環境変数問題により400エラーの可能性"
        },
        {
            "name": "eBay（更新後）",
            "endpoint": "/api/search/ebay", 
            "expected": "新しいトークンで改善の可能性"
        },
        {
            "name": "Mercari",
            "endpoint": "/api/search/mercari",
            "expected": "IP制限により拒否の可能性"
        }
    ]
    
    results = {}
    
    for api in apis_to_test:
        print(f"🔍 {api['name']} APIテスト")
        print(f"   エンドポイント: {api['endpoint']}")
        print(f"   期待値: {api['expected']}")
        
        try:
            url = f"{base_url}{api['endpoint']}"
            params = {'jan_code': jan_code, 'limit': 5}
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            print(f"   ステータス: {response.status_code}")
            print(f"   レスポンス時間: {response_time:.2f}秒")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get('success'):
                        result_count = len(data.get('results', []))
                        print(f"   ✅ 成功: {result_count}件取得")
                        
                        if result_count > 0:
                            sample = data['results'][0]
                            print(f"   サンプル: {sample.get('title', 'タイトル不明')[:50]}...")
                            print(f"   価格: ¥{sample.get('price', 0):,}")
                        
                        results[api['name']] = {
                            'status': 'success',
                            'count': result_count,
                            'response_time': response_time
                        }
                    else:
                        error_msg = data.get('error', 'Unknown error')
                        print(f"   ❌ API失敗: {error_msg}")
                        results[api['name']] = {
                            'status': 'api_error',
                            'error': error_msg,
                            'response_time': response_time
                        }
                        
                except json.JSONDecodeError:
                    print(f"   ❌ JSON解析失敗")
                    results[api['name']] = {
                        'status': 'json_error',
                        'response_time': response_time
                    }
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   エラー詳細: {error_data.get('error', 'Unknown')}")
                except:
                    print(f"   エラー内容: {response.text[:100]}")
                
                results[api['name']] = {
                    'status': 'http_error',
                    'status_code': response.status_code,
                    'response_time': response_time
                }
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ タイムアウト")
            results[api['name']] = {'status': 'timeout'}
            
        except Exception as e:
            print(f"   💥 エラー: {str(e)}")
            results[api['name']] = {'status': 'error', 'message': str(e)}
        
        print("-" * 50)
    
    # 2. 統合検索APIテスト
    print(f"🔍 統合検索APIテスト")
    
    try:
        url = f"{base_url}/api/search/all"
        params = {'jan_code': jan_code, 'limit': 5}
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=60)
        response_time = time.time() - start_time
        
        print(f"   ステータス: {response.status_code}")
        print(f"   レスポンス時間: {response_time:.2f}秒")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if data.get('success'):
                    total_results = data.get('total_results', 0)
                    platforms = data.get('platforms', {})
                    
                    print(f"   ✅ 統合検索成功: {total_results}件")
                    
                    for platform, items in platforms.items():
                        count = len(items) if isinstance(items, list) else 0
                        print(f"     {platform}: {count}件")
                    
                    results['統合検索'] = {
                        'status': 'success',
                        'total_count': total_results,
                        'platforms': {p: len(items) for p, items in platforms.items()},
                        'response_time': response_time
                    }
                else:
                    error_msg = data.get('error', 'Unknown error')
                    print(f"   ❌ 統合検索失敗: {error_msg}")
                    results['統合検索'] = {
                        'status': 'api_error',
                        'error': error_msg,
                        'response_time': response_time
                    }
                    
            except json.JSONDecodeError:
                print(f"   ❌ JSON解析失敗")
                results['統合検索'] = {
                    'status': 'json_error',
                    'response_time': response_time
                }
        else:
            print(f"   ❌ HTTPエラー: {response.status_code}")
            results['統合検索'] = {
                'status': 'http_error',
                'status_code': response.status_code,
                'response_time': response_time
            }
            
    except Exception as e:
        print(f"   💥 統合検索エラー: {str(e)}")
        results['統合検索'] = {'status': 'error', 'message': str(e)}
    
    print("-" * 50)
    
    # 3. 結果サマリー
    print(f"📊 テスト結果サマリー")
    print("=" * 70)
    
    success_count = 0
    total_items = 0
    
    for api_name, result in results.items():
        status = result.get('status', 'unknown')
        
        if status == 'success':
            count = result.get('count', result.get('total_count', 0))
            print(f"✅ {api_name}: 成功 ({count}件)")
            success_count += 1
            total_items += count
        elif status == 'api_error':
            error = result.get('error', 'Unknown')
            print(f"❌ {api_name}: APIエラー ({error})")
        elif status == 'http_error':
            status_code = result.get('status_code', 'Unknown')
            print(f"❌ {api_name}: HTTPエラー ({status_code})")
        else:
            print(f"❌ {api_name}: {status}")
    
    print(f"\n🎯 総合評価")
    print("-" * 30)
    print(f"成功API数: {success_count}/{len(results)}")
    print(f"総取得件数: {total_items}件")
    
    if success_count == len(results):
        grade = "A+ (完璧！)"
    elif success_count >= len(results) * 0.75:
        grade = "A (良好)"
    elif success_count >= len(results) * 0.5:
        grade = "B (改善必要)"
    else:
        grade = "C (要修正)"
    
    print(f"評価: {grade}")
    
    # 4. 改善点の提案
    print(f"\n💡 改善提案")
    print("-" * 30)
    
    if success_count == 0:
        print("   1. 環境変数（APIキー）の確認・更新")
        print("   2. Vercelでの再デプロイ実行")
        print("   3. IP制限対策の検討")
    elif success_count < len(results):
        print("   1. 失敗したAPIの環境変数確認")
        print("   2. IP制限対策の検討")
        print("   3. 代替APIサービスの検討")
    else:
        print("   🎉 すべてのAPIが正常動作中！")
        print("   継続的な監視とパフォーマンス最適化を推奨")
    
    return results

if __name__ == "__main__":
    test_updated_apis()
