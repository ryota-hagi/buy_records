#!/usr/bin/env python3
"""
統合テスト - 全プラットフォームの動作確認
"""
import requests
import json
import time
import sys
from datetime import datetime

# テスト用のJANコード
TEST_JAN_CODE = "4549292184129"  # Nintendo Switch Pro コントローラー

def test_platform(platform_name, endpoint, base_url="http://localhost:3000"):
    """個別プラットフォームのテスト"""
    print(f"\n{'='*50}")
    print(f"Testing {platform_name}")
    print(f"{'='*50}")
    
    try:
        url = f"{base_url}{endpoint}"
        params = {
            "jan_code": TEST_JAN_CODE,
            "limit": 5
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=60)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            data = response.json()
            
            # 成功/失敗の判定
            if data.get('success', False) and data.get('results'):
                results = data['results']
                print(f"✅ SUCCESS: {len(results)}件の結果を取得")
                
                # 最初の3件を表示
                for i, item in enumerate(results[:3]):
                    print(f"\n結果 {i+1}:")
                    print(f"  タイトル: {item.get('title', 'N/A')}")
                    print(f"  価格: ¥{item.get('price', 0):,}")
                    print(f"  URL: {item.get('url', 'N/A')[:50]}...")
                
                return True, len(results), elapsed_time
            else:
                error_msg = data.get('error', 'Unknown error')
                print(f"❌ FAILED: {error_msg}")
                return False, 0, elapsed_time
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text[:200]}")
            return False, 0, elapsed_time
            
    except requests.Timeout:
        print(f"❌ TIMEOUT: リクエストがタイムアウトしました")
        return False, 0, 60
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False, 0, 0

def test_unified_search(base_url="http://localhost:3000"):
    """統合検索のテスト"""
    print(f"\n{'='*50}")
    print("Testing Unified Search (All Platforms)")
    print(f"{'='*50}")
    
    try:
        url = f"{base_url}/api/search/all"
        params = {
            "jan_code": TEST_JAN_CODE,
            "limit": 50
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=300)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success', False):
                total_results = data.get('total_results', 0)
                platforms = data.get('platforms', {})
                errors = data.get('errors', [])
                
                print(f"\n✅ SUCCESS: 総計{total_results}件の結果を取得")
                print(f"Response Time: {elapsed_time:.2f}秒")
                
                # プラットフォーム別の結果
                print("\nプラットフォーム別結果:")
                for platform, results in platforms.items():
                    print(f"  - {platform}: {len(results)}件")
                
                # エラー情報
                if errors:
                    print("\n⚠️ エラーが発生したプラットフォーム:")
                    for error in errors:
                        print(f"  - {error}")
                
                return True, total_results, elapsed_time, platforms, errors
            else:
                print(f"❌ FAILED: {data.get('error', 'Unknown error')}")
                return False, 0, elapsed_time, {}, []
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            return False, 0, elapsed_time, {}, []
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False, 0, 0, {}, []

def main():
    """メインテスト実行"""
    print(f"\n{'#'*60}")
    print(f"# 統合検索エンジン - 全プラットフォームテスト")
    print(f"# 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# テストJANコード: {TEST_JAN_CODE}")
    print(f"{'#'*60}")
    
    # 環境の確認
    base_url = "http://localhost:3000"
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        base_url = "https://buy-records.vercel.app"
        print(f"\n🌍 Production環境でテスト実行")
    else:
        print(f"\n💻 Local環境でテスト実行")
    
    # 各プラットフォームのテスト
    platforms = [
        ("楽天市場", "/api/search/rakuten"),
        ("ヨドバシカメラ", "/api/search/yodobashi"),
        ("PayPayフリマ", "/api/search/paypay"),
        ("ラクマ", "/api/search/rakuma"),
        ("eBay", "/api/search/ebay"),
        ("メルカリ", "/api/search/mercari"),
        ("Yahoo!ショッピング", "/api/search/yahoo")
    ]
    
    results_summary = []
    
    for platform_name, endpoint in platforms:
        success, count, elapsed = test_platform(platform_name, endpoint, base_url)
        results_summary.append({
            "platform": platform_name,
            "success": success,
            "count": count,
            "elapsed": elapsed
        })
    
    # 統合検索のテスト
    print(f"\n{'='*60}")
    unified_success, total, elapsed, platform_results, errors = test_unified_search(base_url)
    
    # テスト結果サマリー
    print(f"\n{'#'*60}")
    print("# テスト結果サマリー")
    print(f"{'#'*60}")
    
    print("\n個別プラットフォームテスト結果:")
    success_count = 0
    for result in results_summary:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['platform']}: {result['count']}件 ({result['elapsed']:.2f}秒)")
        if result["success"]:
            success_count += 1
    
    print(f"\n成功率: {success_count}/{len(platforms)} ({success_count/len(platforms)*100:.1f}%)")
    
    print(f"\n統合検索テスト結果:")
    if unified_success:
        print(f"✅ 成功: 総計{total}件 ({elapsed:.2f}秒)")
    else:
        print(f"❌ 失敗")
    
    # 完了条件の確認
    print(f"\n{'='*60}")
    print("完了条件チェック:")
    
    # 各条件をチェック
    conditions = []
    
    # 楽天API
    rakuten = next((r for r in results_summary if r["platform"] == "楽天市場"), None)
    if rakuten and rakuten["success"] and rakuten["count"] >= 5:
        conditions.append("✅ 楽天API: 5件以上の結果を返却")
    else:
        conditions.append("❌ 楽天API: 5件以上の結果を返却できていません")
    
    # ヨドバシAPI
    yodobashi = next((r for r in results_summary if r["platform"] == "ヨドバシカメラ"), None)
    if yodobashi and yodobashi["success"]:
        conditions.append("✅ ヨドバシAPI: 正常動作")
    else:
        conditions.append("❌ ヨドバシAPI: エラーが発生しています")
    
    # PayPayスクレイパー
    paypay = next((r for r in results_summary if r["platform"] == "PayPayフリマ"), None)
    if paypay and paypay["success"] and paypay["count"] >= 1:
        conditions.append("✅ PayPayスクレイパー: 1件以上の結果を取得")
    else:
        conditions.append("❌ PayPayスクレイパー: 結果を取得できていません")
    
    # ラクマスクレイパー
    rakuma = next((r for r in results_summary if r["platform"] == "ラクマ"), None)
    if rakuma and rakuma["success"] and rakuma["elapsed"] < 30:
        conditions.append("✅ ラクマスクレイパー: 30秒以内に結果を返却")
    else:
        conditions.append("❌ ラクマスクレイパー: タイムアウトまたはエラー")
    
    # 統合テスト
    if unified_success:
        conditions.append("✅ 全プラットフォームの統合テストが成功")
    else:
        conditions.append("❌ 統合テストが失敗")
    
    for condition in conditions:
        print(condition)
    
    # 最終判定
    all_passed = all("✅" in c for c in conditions)
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 すべての完了条件を満たしています！")
        return 0
    else:
        print("⚠️  一部の完了条件を満たしていません。")
        return 1

if __name__ == "__main__":
    sys.exit(main())