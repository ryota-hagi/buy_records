#!/usr/bin/env python3
"""
ワークフロー問題の詳細診断 - 全プラットフォームで0件の原因調査
"""

import requests
import json
import time
from datetime import datetime

def diagnose_workflow_issue():
    """ワークフロー問題の詳細診断"""
    
    print("🔍 ワークフロー問題の詳細診断")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    base_url = "https://buy-records.vercel.app"
    jan_code = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # 1. 各プラットフォームの個別テスト
    print("\n1. 各プラットフォームの個別詳細テスト")
    print("-" * 50)
    
    platforms = [
        {"name": "Yahoo!ショッピング", "endpoint": "/api/search/yahoo"},
        {"name": "eBay", "endpoint": "/api/search/ebay"},
        {"name": "Mercari", "endpoint": "/api/search/mercari"}
    ]
    
    platform_results = {}
    
    for platform in platforms:
        print(f"\n🔍 {platform['name']} 詳細テスト")
        print("-" * 30)
        
        # パラメータなしテスト
        try:
            url = f"{base_url}{platform['endpoint']}"
            response = requests.get(url, timeout=20)
            print(f"   パラメータなし: {response.status_code}")
            
            if response.status_code == 400:
                data = response.json()
                print(f"   エラーメッセージ: {data.get('error', 'Unknown')}")
            
        except Exception as e:
            print(f"   パラメータなしエラー: {str(e)}")
        
        # JANコードテスト
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
                    sample = data['results'][0]
                    print(f"   サンプルタイトル: {sample.get('title', 'なし')[:50]}...")
                    print(f"   サンプル価格: {sample.get('price', 'なし')}")
                    platform_results[platform['name']] = 'success'
                elif data.get('success'):
                    print(f"   成功だが結果0件")
                    print(f"   レスポンス詳細: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                    platform_results[platform['name']] = 'success_no_results'
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"   APIエラー: {error}")
                    print(f"   詳細: {data.get('details', 'なし')}")
                    platform_results[platform['name']] = f'api_error: {error}'
            
            elif response.status_code == 500:
                try:
                    data = response.json()
                    error = data.get('error', 'Unknown server error')
                    print(f"   サーバーエラー: {error}")
                    print(f"   詳細: {data.get('details', 'なし')}")
                except:
                    print(f"   サーバーエラー: JSONパース不可")
                platform_results[platform['name']] = 'server_error'
            
            else:
                print(f"   予期しないステータス: {response.status_code}")
                try:
                    data = response.json()
                    print(f"   レスポンス: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
                except:
                    print(f"   レスポンス: {response.text[:300]}...")
                platform_results[platform['name']] = f'unexpected_status: {response.status_code}'
                
        except Exception as e:
            print(f"   例外エラー: {str(e)}")
            platform_results[platform['name']] = f'exception: {str(e)}'
        
        # キーワード検索テスト
        try:
            url = f"{base_url}{platform['endpoint']}"
            params = {'query': 'Nintendo Switch', 'limit': 3}
            
            print(f"   キーワード検索: Nintendo Switch")
            response = requests.get(url, params=params, timeout=30)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                print(f"   キーワード結果数: {results_count}")
                
                if results_count > 0:
                    print(f"   ✅ キーワード検索は動作中")
                else:
                    print(f"   ❌ キーワード検索も0件")
            
        except Exception as e:
            print(f"   キーワード検索エラー: {str(e)}")
    
    # 2. 統合検索の詳細テスト
    print(f"\n2. 統合検索の詳細テスト")
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
            
            # 統合検索の内部ログ確認
            print(f"\n統合検索レスポンス詳細:")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1000] + "...")
            
        else:
            print(f"統合検索エラー: {response.status_code}")
            try:
                data = response.json()
                print(f"エラー詳細: {json.dumps(data, ensure_ascii=False, indent=2)}")
            except:
                print(f"レスポンステキスト: {response.text[:500]}...")
                
    except Exception as e:
        print(f"統合検索例外: {str(e)}")
    
    # 3. 環境変数とAPIキーの確認
    print(f"\n3. 環境変数とAPIキーの確認")
    print("-" * 50)
    
    try:
        url = f"{base_url}/api/test-production"
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            env = data.get('environment', {})
            print(f"環境変数状況:")
            for key, value in env.items():
                print(f"  {key}: {value}")
        else:
            print(f"環境変数確認エラー: {response.status_code}")
            
    except Exception as e:
        print(f"環境変数確認例外: {str(e)}")
    
    # 4. 問題の分析と診断
    print(f"\n4. 問題の分析と診断")
    print("-" * 50)
    
    # 結果パターンの分析
    success_count = sum(1 for result in platform_results.values() if result == 'success')
    no_results_count = sum(1 for result in platform_results.values() if result == 'success_no_results')
    error_count = len(platform_results) - success_count - no_results_count
    
    print(f"結果パターン分析:")
    print(f"  成功（結果あり）: {success_count}件")
    print(f"  成功（結果なし）: {no_results_count}件")
    print(f"  エラー: {error_count}件")
    
    # 問題の特定
    if success_count == 0 and no_results_count > 0:
        print(f"\n🎯 問題特定: API実行成功だが全プラットフォームで結果0件")
        print(f"原因候補:")
        print(f"  1. JANコード検索ロジックの問題")
        print(f"  2. APIパラメータの形式問題")
        print(f"  3. 検索条件が厳しすぎる")
        print(f"  4. データベース/API側の商品データ不足")
        
    elif error_count > 0:
        print(f"\n🎯 問題特定: API実行エラー")
        print(f"原因候補:")
        print(f"  1. 環境変数の設定問題")
        print(f"  2. APIキーの認証問題")
        print(f"  3. APIエンドポイントの設定問題")
        
    else:
        print(f"\n🎯 問題特定: 予期しないパターン")
    
    # 5. 推奨解決策
    print(f"\n5. 推奨解決策")
    print("-" * 50)
    
    if no_results_count > 0:
        print(f"即座に試すべき解決策:")
        print(f"  1. より一般的なキーワードでテスト")
        print(f"  2. JANコード以外のパラメータでテスト")
        print(f"  3. 各APIの検索パラメータ形式を確認")
        print(f"  4. フォールバック機能の動作確認")
        
    print(f"\n技術的解決策:")
    print(f"  1. APIレスポンスのログ詳細化")
    print(f"  2. 検索パラメータの最適化")
    print(f"  3. フォールバック機能の強化")
    print(f"  4. エラーハンドリングの改善")
    
    return platform_results

if __name__ == "__main__":
    diagnose_workflow_issue()
