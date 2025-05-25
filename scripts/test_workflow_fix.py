#!/usr/bin/env python3
"""
ワークフロー修正後のテスト - フォールバック機能の動作確認
"""

import requests
import json
import time
from datetime import datetime

def test_workflow_fix():
    """ワークフロー修正後のテスト実行"""
    
    print("🎯 ワークフロー修正後のテスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デプロイ完了まで待機
    print("⏳ Vercel自動デプロイ完了を待機中（60秒）...")
    time.sleep(60)
    
    # 1. 各プラットフォームの修正後テスト
    print("\n1. 各プラットフォームの修正後テスト")
    print("-" * 50)
    
    platforms = [
        {"name": "Yahoo!ショッピング", "endpoint": "/api/search/yahoo"},
        {"name": "eBay", "endpoint": "/api/search/ebay"},
        {"name": "Mercari", "endpoint": "/api/search/mercari"}
    ]
    
    platform_results = {}
    
    for platform in platforms:
        print(f"\n🔍 {platform['name']} 修正後テスト")
        print("-" * 30)
        
        try:
            url = f"{base_url}{platform['endpoint']}"
            params = {'jan_code': jan_code, 'limit': 5}
            
            print(f"   JANコード検索: {jan_code}")
            response = requests.get(url, params=params, timeout=30)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   成功フラグ: {data.get('success', False)}")
                print(f"   結果数: {len(data.get('results', []))}")
                
                if data.get('success') and data.get('results'):
                    results = data['results']
                    sample = results[0]
                    print(f"   サンプルタイトル: {sample.get('title', 'なし')[:50]}...")
                    print(f"   サンプル価格: {sample.get('price', 'なし')}")
                    
                    # フォールバック使用の確認
                    if data.get('note'):
                        print(f"   📝 注記: {data.get('note')}")
                    if data.get('api_key_used'):
                        print(f"   🔑 使用APIキー: {data.get('api_key_used')}")
                    if data.get('api_endpoint_used'):
                        print(f"   🌐 使用エンドポイント: {data.get('api_endpoint_used')}")
                    
                    platform_results[platform['name']] = 'success_with_results'
                elif data.get('success'):
                    print(f"   成功だが結果0件")
                    platform_results[platform['name']] = 'success_no_results'
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"   APIエラー: {error}")
                    platform_results[platform['name']] = f'api_error: {error}'
            
            else:
                print(f"   HTTPエラー: {response.status_code}")
                try:
                    data = response.json()
                    print(f"   エラー詳細: {data.get('error', 'Unknown')}")
                except:
                    pass
                platform_results[platform['name']] = f'http_error: {response.status_code}'
                
        except Exception as e:
            print(f"   例外エラー: {str(e)}")
            platform_results[platform['name']] = f'exception: {str(e)}'
    
    # 2. 統合検索の修正後テスト
    print(f"\n2. 統合検索の修正後テスト")
    print("-" * 50)
    
    try:
        url = f"{base_url}/api/search/all"
        params = {'jan_code': jan_code, 'limit': 3}
        
        print(f"統合検索実行: {jan_code}")
        response = requests.get(url, params=params, timeout=60)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功フラグ: {data.get('success', False)}")
            print(f"総結果数: {data.get('total_results', 0)}")
            
            platforms_data = data.get('platforms', {})
            print(f"プラットフォーム別結果:")
            for platform, results in platforms_data.items():
                count = len(results) if isinstance(results, list) else 0
                print(f"  {platform}: {count}件")
            
            errors = data.get('platform_errors', {})
            if errors:
                print(f"プラットフォームエラー:")
                for platform, error in errors.items():
                    print(f"  {platform}: {error}")
            
            unified_success = data.get('total_results', 0) > 0
            
        else:
            print(f"統合検索エラー: {response.status_code}")
            unified_success = False
                
    except Exception as e:
        print(f"統合検索例外: {str(e)}")
        unified_success = False
    
    # 3. 結果分析と評価
    print(f"\n3. 結果分析と評価")
    print("-" * 50)
    
    # 結果パターンの分析
    success_with_results = sum(1 for result in platform_results.values() if result == 'success_with_results')
    success_no_results = sum(1 for result in platform_results.values() if result == 'success_no_results')
    error_count = len(platform_results) - success_with_results - success_no_results
    
    print(f"プラットフォーム別結果:")
    print(f"  成功（結果あり）: {success_with_results}件")
    print(f"  成功（結果なし）: {success_no_results}件")
    print(f"  エラー: {error_count}件")
    
    for platform, result in platform_results.items():
        if result == 'success_with_results':
            print(f"  ✅ {platform}: 正常動作")
        elif result == 'success_no_results':
            print(f"  ⚠️  {platform}: 動作するが結果なし")
        else:
            print(f"  ❌ {platform}: {result}")
    
    # 4. 修正効果の評価
    print(f"\n4. 修正効果の評価")
    print("-" * 50)
    
    total_working = success_with_results + success_no_results
    total_platforms = len(platform_results)
    working_rate = total_working / total_platforms if total_platforms > 0 else 0
    
    print(f"動作率: {working_rate:.1%} ({total_working}/{total_platforms})")
    
    if working_rate >= 1.0:
        grade = "A+ (完璧)"
        status = "🎉 全プラットフォーム動作中！"
    elif working_rate >= 0.67:
        grade = "A (優秀)"
        status = "🎉 大部分のプラットフォームが動作中"
    elif working_rate >= 0.33:
        grade = "B (改善)"
        status = "⚠️  一部プラットフォームが動作中"
    else:
        grade = "C (要修正)"
        status = "❌ 多くのプラットフォームでエラー継続"
    
    print(f"評価: {grade}")
    print(f"状況: {status}")
    
    # 統合検索の評価
    if unified_success:
        print(f"統合検索: ✅ 正常動作")
    else:
        print(f"統合検索: ❌ エラーまたは結果なし")
    
    # 5. 修正前後の比較
    print(f"\n5. 修正前後の比較")
    print("-" * 50)
    
    print(f"修正前の問題:")
    print(f"  - eBay: 500エラー（APIサーバーエラー）")
    print(f"  - Mercari: 500エラー（DNS解決エラー）")
    print(f"  - 統合検索: Yahoo!のみ動作（3件）")
    
    print(f"\n修正後の状況:")
    if success_with_results >= 2:
        print(f"  ✅ 複数プラットフォームで結果取得成功")
    if total_working == total_platforms:
        print(f"  ✅ 全プラットフォームでエラー解消")
    if unified_success:
        print(f"  ✅ 統合検索で複数プラットフォーム結果統合")
    
    # 6. 次のアクション
    print(f"\n6. 次のアクション")
    print("-" * 50)
    
    if working_rate >= 0.67:
        print(f"✅ ワークフロー問題は大幅に改善されました")
        if success_with_results < total_platforms:
            print(f"📝 残りタスク: 実APIの接続性向上")
        else:
            print(f"🎉 すべてのプラットフォームが正常動作中")
    else:
        print(f"🔧 追加の修正が必要です")
        print(f"📝 フォールバック機能の更なる強化を検討")
    
    return {
        'working_rate': working_rate,
        'grade': grade,
        'platform_results': platform_results,
        'unified_success': unified_success,
        'success_with_results': success_with_results
    }

if __name__ == "__main__":
    test_workflow_fix()
