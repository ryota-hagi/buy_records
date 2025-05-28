#!/usr/bin/env python3
"""
修正後の統合検索APIテスト
"""

import requests
import json
import time
from datetime import datetime

def test_unified_search():
    """統合検索APIのテスト"""
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    print("🚀 統合検索API修正後テスト開始")
    print(f"   JANコード: {jan_code}")
    print(f"   URL: {base_url}")
    print("=" * 60)
    
    # 統合検索APIテスト
    url = f"{base_url}/api/search/all"
    params = {'jan_code': jan_code, 'limit': 5}
    
    try:
        print(f"🔍 統合検索APIテスト")
        print(f"   URL: {url}")
        print(f"   パラメータ: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=60)
        response_time = time.time() - start_time
        
        print(f"   ステータス: {response.status_code}")
        print(f"   レスポンス時間: {response_time:.2f}秒")
        print(f"   Content-Type: {response.headers.get('content-type', '')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ JSON解析成功")
                
                # 結果の詳細分析
                if data.get('success'):
                    print(f"   API成功: {data['success']}")
                    print(f"   総結果数: {data.get('total_results', 0)}件")
                    print(f"   検索プラットフォーム数: {data.get('platforms_searched', 0)}個")
                    
                    # プラットフォーム別結果
                    if 'platforms' in data:
                        print(f"   プラットフォーム別結果:")
                        for platform, items in data['platforms'].items():
                            count = len(items) if isinstance(items, list) else 0
                            print(f"     {platform}: {count}件")
                            
                            # サンプル商品表示
                            if count > 0:
                                sample = items[0]
                                print(f"       サンプル: {sample.get('title', 'タイトル不明')}")
                                print(f"       価格: ¥{sample.get('price', 0):,}")
                    
                    # エラー情報
                    if 'errors' in data and data['errors']:
                        print(f"   ⚠️  プラットフォームエラー:")
                        for error in data['errors']:
                            print(f"     - {error}")
                    
                    # 結果サマリー
                    results = data.get('results', [])
                    if results:
                        print(f"   📊 結果サマリー:")
                        print(f"     最安値: ¥{min(r.get('total_price', r.get('price', 0)) for r in results):,}")
                        print(f"     最高値: ¥{max(r.get('total_price', r.get('price', 0)) for r in results):,}")
                        
                        # プラットフォーム分布
                        platform_dist = {}
                        for result in results:
                            platform = result.get('platform', 'unknown')
                            platform_dist[platform] = platform_dist.get(platform, 0) + 1
                        
                        print(f"     プラットフォーム分布: {platform_dist}")
                    
                    return {
                        'success': True,
                        'total_results': data.get('total_results', 0),
                        'platforms': data.get('platforms', {}),
                        'errors': data.get('errors', [])
                    }
                else:
                    print(f"   ❌ API失敗: {data.get('error', 'Unknown error')}")
                    return {
                        'success': False,
                        'error': data.get('error', 'Unknown error')
                    }
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析失敗: {str(e)}")
                print(f"   レスポンス内容: {response.text[:500]}")
                return {
                    'success': False,
                    'error': f'JSON decode error: {str(e)}'
                }
        else:
            print(f"   ❌ HTTPエラー: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   エラー詳細: {error_data}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {error_data}'
                }
            except:
                print(f"   エラー内容: {response.text[:200]}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:200]}'
                }
                
    except requests.exceptions.Timeout:
        print(f"   ⏰ タイムアウト")
        return {
            'success': False,
            'error': 'Timeout'
        }
        
    except requests.exceptions.ConnectionError as e:
        print(f"   🔌 接続エラー: {str(e)}")
        return {
            'success': False,
            'error': f'Connection error: {str(e)}'
        }
        
    except Exception as e:
        print(f"   💥 不明なエラー: {str(e)}")
        return {
            'success': False,
            'error': f'Unknown error: {str(e)}'
        }

def main():
    """メイン実行関数"""
    result = test_unified_search()
    
    print("=" * 60)
    print("📊 統合検索テスト結果")
    
    if result['success']:
        total_results = result.get('total_results', 0)
        platforms = result.get('platforms', {})
        errors = result.get('errors', [])
        
        print(f"✅ 統合検索成功")
        print(f"   総結果数: {total_results}件")
        print(f"   動作プラットフォーム: {len([p for p, items in platforms.items() if len(items) > 0])}個")
        
        if errors:
            print(f"   エラーあり: {len(errors)}個")
            for error in errors:
                print(f"     - {error}")
        
        if total_results > 0:
            print(f"🎯 結論: 統合検索は動作中（{total_results}件取得）")
        else:
            print(f"⚠️  結論: 統合検索は動作するが、データ取得0件")
    else:
        print(f"❌ 統合検索失敗")
        print(f"   エラー: {result.get('error', 'Unknown error')}")
        print(f"🚨 結論: 統合検索に問題あり")
    
    return result

if __name__ == "__main__":
    main()
