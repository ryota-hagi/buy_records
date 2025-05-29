#!/usr/bin/env python3
"""
デプロイ後検証スクリプト
本番環境が正しくデプロイされたことを確認
"""
import requests
import time
import sys
from datetime import datetime

def wait_for_deployment(max_wait_minutes=10):
    """デプロイ完了を待機"""
    print(f"デプロイ完了を待機中（最大{max_wait_minutes}分）...")
    
    base_url = "https://buy-records.vercel.app"
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        try:
            # ヘルスチェック
            response = requests.get(f"{base_url}/api/health", timeout=10)
            if response.status_code == 200:
                print("✅ デプロイが完了しました！")
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(10)
    
    print("\n❌ タイムアウト: デプロイが完了しませんでした")
    return False

def verify_endpoints():
    """エンドポイントの動作確認"""
    base_url = "https://buy-records.vercel.app"
    
    endpoints = [
        ("/", "GET", None),
        ("/api/health", "GET", None),
        ("/api/search/rakuten", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/yodobashi", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/paypay", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/rakuma", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/ebay", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/mercari", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/yahoo", "GET", {"jan_code": "4549292184129", "limit": "5"}),
        ("/api/search/all", "GET", {"jan_code": "4549292184129", "limit": "20"})
    ]
    
    results = []
    
    print("\nエンドポイント検証:")
    print("-" * 60)
    
    for endpoint, method, params in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=60)
            else:
                response = requests.post(url, json=params, timeout=60)
            
            status = "✅" if response.status_code == 200 else "❌"
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
            
            print(f"{status} {endpoint}: {response.status_code}")
            
            # APIエンドポイントの場合、結果も確認
            if endpoint.startswith("/api/search/") and response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        result_count = len(data.get("results", []))
                        print(f"   └─ 結果: {result_count}件")
                    else:
                        print(f"   └─ エラー: {data.get('error', 'Unknown')}")
                except:
                    pass
                    
        except requests.Timeout:
            print(f"⏱️ {endpoint}: タイムアウト")
            results.append({
                "endpoint": endpoint,
                "status_code": 0,
                "success": False
            })
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")
            results.append({
                "endpoint": endpoint,
                "status_code": 0,
                "success": False
            })
    
    return results

def run_integration_test():
    """統合テストの実行"""
    print("\n統合テスト実行中...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/testing/test_all_platforms_integration.py", "production"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        # 成功条件を確認
        if "すべての完了条件を満たしています" in result.stdout:
            return True
        else:
            return False
    except Exception as e:
        print(f"統合テストエラー: {e}")
        return False

def generate_deployment_report(results, test_success):
    """デプロイレポートの生成"""
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success
    success_rate = (success / total * 100) if total > 0 else 0
    
    report = f"""# デプロイ完了レポート

実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
デプロイID: RM-2025-05-29-002

## デプロイ結果

### エンドポイント検証
- 総エンドポイント: {total}
- 成功: {success}
- 失敗: {failed}
- 成功率: {success_rate:.1f}%

### 詳細結果
"""
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        report += f"- {status} {result['endpoint']}: {result['status_code']}\n"
    
    report += f"\n### 統合テスト\n"
    if test_success:
        report += "✅ 統合テスト成功\n"
    else:
        report += "❌ 統合テスト失敗\n"
    
    report += f"\n## 判定\n"
    if success_rate >= 90 and test_success:
        report += "✅ **デプロイ成功**: 本番環境が正常に稼働しています\n"
    else:
        report += "❌ **デプロイ失敗**: ロールバックを検討してください\n"
    
    return report

def main():
    print("=" * 60)
    print("デプロイ後検証を開始します")
    print("=" * 60)
    
    # デプロイ完了待機
    if not wait_for_deployment():
        print("デプロイが完了しませんでした")
        sys.exit(1)
    
    # エンドポイント検証
    results = verify_endpoints()
    
    # 統合テスト
    test_success = run_integration_test()
    
    # レポート生成
    report = generate_deployment_report(results, test_success)
    
    # レポート保存
    report_file = f"deploy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)
    print(f"\nレポートを保存しました: {report_file}")
    
    # 成功判定
    success_count = sum(1 for r in results if r["success"])
    if success_count >= len(results) * 0.9 and test_success:
        print("\n✅ デプロイが正常に完了しました！")
        return 0
    else:
        print("\n❌ デプロイに問題があります。ロールバックを検討してください。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)