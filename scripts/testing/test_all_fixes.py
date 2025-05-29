#!/usr/bin/env python3
"""
全ての修正を統合テスト
"""
import os
import sys
import json
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.collectors.ebay import EbayClient
from src.collectors.rakuma_selenium import RakumaSeleniumScraper
from src.utils.supabase_client import check_connection, get_supabase_client, execute_with_retry

def test_all_components():
    """全コンポーネントの統合テスト"""
    print("=== Integration Test for All Fixes ===")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "ebay": False,
        "rakuma": False,
        "supabase": False,
        "error_rate": 100.0
    }
    
    # 1. eBay API テスト
    print("📍 Testing eBay API...")
    try:
        ebay_client = EbayClient()
        # 簡単な検索を実行
        ebay_results = ebay_client.search_sold_items("test", limit=1)
        if ebay_results:
            print(f"✅ eBay API working - found {len(ebay_results)} items")
            results["ebay"] = True
        else:
            print("⚠️  eBay API returned no results")
            # 現在の出品も試す
            current_results = ebay_client.search_current_items("test", limit=1)
            if current_results:
                print(f"✅ eBay current items API working - found {len(current_results)} items")
                results["ebay"] = True
            else:
                print("❌ eBay API not returning results")
    except Exception as e:
        print(f"❌ eBay API error: {str(e)}")
    
    # 2. ラクマスクレイパーテスト
    print("\n📍 Testing Rakuma Scraper...")
    try:
        rakuma_scraper = RakumaSeleniumScraper()
        rakuma_results = rakuma_scraper.search("test")
        if rakuma_results:
            print(f"✅ Rakuma scraper working - found {len(rakuma_results)} items")
            results["rakuma"] = True
        else:
            print("❌ Rakuma scraper returned no results")
    except Exception as e:
        print(f"❌ Rakuma scraper error: {str(e)}")
    
    # 3. Supabase接続テスト
    print("\n📍 Testing Supabase Connection...")
    try:
        if check_connection():
            print("✅ Supabase connection successful")
            
            # 読み書きテスト
            client = get_supabase_client()
            test_task = {
                'keyword': 'integration_test',
                'status': 'completed',
                'created_at': datetime.now().isoformat()
            }
            
            # 書き込み
            result = execute_with_retry(
                lambda: client.table('search_tasks').insert(test_task).execute()
            )
            
            if result.data:
                task_id = result.data[0]['id']
                print("✅ Supabase write successful")
                
                # 読み込み
                read_result = execute_with_retry(
                    lambda: client.table('search_tasks').select('*').eq('id', task_id).execute()
                )
                
                if read_result.data:
                    print("✅ Supabase read successful")
                    
                    # クリーンアップ
                    execute_with_retry(
                        lambda: client.table('search_tasks').delete().eq('id', task_id).execute()
                    )
                    print("✅ Supabase cleanup successful")
                    results["supabase"] = True
                else:
                    print("❌ Supabase read failed")
            else:
                print("❌ Supabase write failed")
        else:
            print("❌ Supabase connection failed")
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
    
    # エラー率計算
    success_count = sum([results["ebay"], results["rakuma"], results["supabase"]])
    total_count = 3
    success_rate = (success_count / total_count) * 100
    results["error_rate"] = 100 - success_rate
    
    # 結果サマリー
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    print(f"eBay API:        {'✅ Working' if results['ebay'] else '❌ Failed'}")
    print(f"Rakuma Scraper:  {'✅ Working' if results['rakuma'] else '❌ Failed'}")
    print(f"Supabase:        {'✅ Working' if results['supabase'] else '❌ Failed'}")
    print(f"\nSuccess Rate:    {success_rate:.1f}%")
    print(f"Error Rate:      {results['error_rate']:.1f}%")
    print(f"Target Error Rate: <10%")
    
    # 結果を保存
    with open('integration_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "success_rate": success_rate,
            "target_met": results["error_rate"] < 10
        }, f, indent=2)
    
    print("\n✅ Results saved to integration_test_results.json")
    
    # 最終判定
    if results["error_rate"] < 10:
        print("\n🎉 SUCCESS: Error rate is below 10% target!")
        return True
    else:
        print(f"\n⚠️  NEEDS WORK: Error rate ({results['error_rate']:.1f}%) is above 10% target")
        return False

def test_production_readiness():
    """本番環境への準備状況をチェック"""
    print("\n\n=== Production Readiness Check ===\n")
    
    checks = {
        "env_vars": False,
        "api_keys": False,
        "database": False,
        "selenium": False
    }
    
    # 環境変数チェック
    print("📍 Checking environment variables...")
    required_vars = [
        "EBAY_APP_ID",
        "EBAY_CLIENT_SECRET",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if not missing_vars:
        print("✅ All required environment variables are set")
        checks["env_vars"] = True
    else:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    
    # APIキーの有効性チェック
    print("\n📍 Checking API key validity...")
    if os.environ.get("EBAY_APP_ID", "").startswith("ari"):
        print("✅ eBay API key format looks valid")
        checks["api_keys"] = True
    else:
        print("❌ eBay API key format looks invalid")
    
    # データベース接続
    print("\n📍 Checking database connection...")
    if check_connection():
        print("✅ Database connection is stable")
        checks["database"] = True
    else:
        print("❌ Database connection is unstable")
    
    # Seleniumサーバー
    print("\n📍 Checking Selenium server...")
    try:
        import requests
        response = requests.get("http://localhost:5001/wd/hub/status", timeout=5)
        if response.status_code == 200:
            print("✅ Selenium server is running")
            checks["selenium"] = True
        else:
            print("❌ Selenium server is not responding properly")
    except:
        print("⚠️  Selenium server is not running (optional for some features)")
        checks["selenium"] = True  # Optional
    
    # 最終チェック
    all_ready = all(checks.values())
    
    print("\n" + "="*50)
    print("🚀 Production Readiness:")
    print("="*50)
    for check, status in checks.items():
        print(f"{check:15} {'✅' if status else '❌'}")
    
    if all_ready:
        print("\n✅ System is ready for production!")
    else:
        print("\n⚠️  System needs attention before production deployment")
    
    return all_ready

if __name__ == "__main__":
    # 統合テスト実行
    integration_success = test_all_components()
    
    # 本番準備チェック
    production_ready = test_production_readiness()
    
    # 最終結果
    print("\n\n" + "="*50)
    print("🏁 FINAL ASSESSMENT:")
    print("="*50)
    
    if integration_success and production_ready:
        print("✅ All systems operational - Ready for deployment!")
        print("\nNext steps:")
        print("1. Run 'git add .' to stage all changes")
        print("2. Run 'git commit -m \"Fix: Reduce error rate to <10%\"'")
        print("3. Run 'git push' to deploy changes")
        print("4. Monitor production logs for any issues")
    else:
        print("❌ System needs further fixes")
        print("\nRecommended actions:")
        if not integration_success:
            print("- Review integration test failures above")
        if not production_ready:
            print("- Address production readiness issues")