#!/usr/bin/env python3
"""
統合検索エンジンの実データ検証スクリプト
モックデータ禁止制約を遵守し、実在する商品データのみを取得
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.anti_mock_config import validate_search_results, get_environment_info

class UnifiedSearchTester:
    def __init__(self, base_url="http://localhost:3001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UnifiedSearchTester/1.0',
            'Content-Type': 'application/json'
        })
        
        # 環境情報を確認
        env_info = get_environment_info()
        print(f"環境情報: {env_info}")
        
        # 実在する商品のテストケース
        self.test_cases = [
            {
                "name": "Nintendo Switch（実在商品）",
                "query": "Nintendo Switch",
                "expected_platforms": ["yahoo_shopping", "ebay", "mercari"]
            },
            {
                "name": "iPhone 15（実在商品）", 
                "query": "iPhone 15",
                "expected_platforms": ["yahoo_shopping", "ebay", "mercari"]
            },
            {
                "name": "JANコード検索（コカ・コーラ）",
                "jan_code": "4902370548501",
                "expected_platforms": ["yahoo_shopping", "ebay", "mercari"]
            }
        ]
    
    def test_individual_apis(self):
        """個別APIエンドポイントの動作確認"""
        print("\n=== 個別APIエンドポイントテスト ===")
        
        apis = [
            {"name": "Yahoo!ショッピング", "endpoint": "/api/search/yahoo"},
            {"name": "eBay", "endpoint": "/api/search/ebay"},
            {"name": "Mercari", "endpoint": "/api/search/mercari"}
        ]
        
        test_query = "Nintendo Switch"
        results = {}
        
        for api in apis:
            print(f"\n{api['name']} API テスト...")
            try:
                url = f"{self.base_url}{api['endpoint']}"
                params = {"query": test_query, "limit": 5}
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('success') and data.get('results'):
                        # モックデータ検証
                        validated_results = validate_search_results(
                            data['results'], 
                            api['name'].lower().replace('!', '').replace(' ', '_')
                        )
                        
                        results[api['name']] = {
                            "status": "✅ 成功",
                            "count": len(validated_results),
                            "sample": validated_results[0] if validated_results else None
                        }
                        print(f"  ✅ {len(validated_results)}件の実データを取得")
                        
                        # データ品質チェック
                        self._validate_data_quality(validated_results, api['name'])
                        
                    else:
                        results[api['name']] = {
                            "status": "⚠️ データなし",
                            "error": data.get('error', 'Unknown error')
                        }
                        print(f"  ⚠️ データ取得失敗: {data.get('error', 'Unknown error')}")
                else:
                    results[api['name']] = {
                        "status": "❌ HTTPエラー",
                        "error": f"HTTP {response.status_code}"
                    }
                    print(f"  ❌ HTTPエラー: {response.status_code}")
                    
            except Exception as e:
                results[api['name']] = {
                    "status": "❌ 例外エラー",
                    "error": str(e)
                }
                print(f"  ❌ 例外エラー: {e}")
            
            time.sleep(1)  # API制限対策
        
        return results
    
    def test_unified_search(self):
        """統合検索エンドポイントの動作確認"""
        print("\n=== 統合検索エンドポイントテスト ===")
        
        results = {}
        
        for test_case in self.test_cases:
            print(f"\n{test_case['name']} テスト...")
            
            try:
                url = f"{self.base_url}/api/search/all"
                params = {"limit": 20}
                
                if "query" in test_case:
                    params["query"] = test_case["query"]
                elif "jan_code" in test_case:
                    params["jan_code"] = test_case["jan_code"]
                
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('success') and data.get('results'):
                        # モックデータ検証
                        validated_results = validate_search_results(
                            data['results'], 
                            "unified_search"
                        )
                        
                        # プラットフォーム別集計
                        platform_counts = {}
                        for result in validated_results:
                            platform = result.get('platform', 'unknown')
                            platform_counts[platform] = platform_counts.get(platform, 0) + 1
                        
                        results[test_case['name']] = {
                            "status": "✅ 成功",
                            "total_count": len(validated_results),
                            "platform_counts": platform_counts,
                            "platforms_found": list(platform_counts.keys())
                        }
                        
                        print(f"  ✅ 総計{len(validated_results)}件の実データを取得")
                        for platform, count in platform_counts.items():
                            print(f"    - {platform}: {count}件")
                        
                        # データ品質チェック
                        self._validate_data_quality(validated_results, "統合検索")
                        
                    else:
                        results[test_case['name']] = {
                            "status": "⚠️ データなし",
                            "error": data.get('error', 'Unknown error')
                        }
                        print(f"  ⚠️ データ取得失敗: {data.get('error', 'Unknown error')}")
                else:
                    results[test_case['name']] = {
                        "status": "❌ HTTPエラー",
                        "error": f"HTTP {response.status_code}"
                    }
                    print(f"  ❌ HTTPエラー: {response.status_code}")
                    
            except Exception as e:
                results[test_case['name']] = {
                    "status": "❌ 例外エラー",
                    "error": str(e)
                }
                print(f"  ❌ 例外エラー: {e}")
            
            time.sleep(2)  # API制限対策
        
        return results
    
    def _validate_data_quality(self, results, source):
        """データ品質の検証"""
        if not results:
            return
        
        sample = results[0]
        
        # 必須フィールドの確認
        required_fields = ['title', 'price', 'url', 'platform']
        missing_fields = [field for field in required_fields if not sample.get(field)]
        
        if missing_fields:
            print(f"    ⚠️ 必須フィールド不足: {missing_fields}")
        
        # URLの妥当性確認
        url = sample.get('url', '')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            print(f"    ⚠️ 無効なURL形式: {url}")
        
        # 価格の妥当性確認
        price = sample.get('price', 0)
        if not isinstance(price, (int, float)) or price <= 0:
            print(f"    ⚠️ 無効な価格: {price}")
        
        # モックデータ検出
        mock_indicators = ['test', 'sample', 'mock', 'dummy', 'example']
        title = sample.get('title', '').lower()
        if any(indicator in title for indicator in mock_indicators):
            print(f"    ❌ モックデータ検出: {sample.get('title')}")
        
        print(f"    ✅ データ品質チェック完了")
    
    def generate_report(self, individual_results, unified_results):
        """テスト結果レポートの生成"""
        print("\n" + "="*60)
        print("統合検索エンジン 実データ検証レポート")
        print("="*60)
        print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"テスト対象: {self.base_url}")
        
        # 個別API結果
        print("\n【個別APIテスト結果】")
        for api, result in individual_results.items():
            print(f"{api}: {result['status']}")
            if 'count' in result:
                print(f"  取得件数: {result['count']}件")
        
        # 統合検索結果
        print("\n【統合検索テスト結果】")
        for test_name, result in unified_results.items():
            print(f"{test_name}: {result['status']}")
            if 'total_count' in result:
                print(f"  総取得件数: {result['total_count']}件")
                print(f"  プラットフォーム: {', '.join(result['platforms_found'])}")
        
        # 総合評価
        print("\n【総合評価】")
        individual_success = sum(1 for r in individual_results.values() if '✅' in r['status'])
        unified_success = sum(1 for r in unified_results.values() if '✅' in r['status'])
        
        total_apis = len(individual_results)
        total_tests = len(unified_results)
        
        print(f"個別API成功率: {individual_success}/{total_apis} ({individual_success/total_apis*100:.1f}%)")
        print(f"統合検索成功率: {unified_success}/{total_tests} ({unified_success/total_tests*100:.1f}%)")
        
        if individual_success == total_apis and unified_success == total_tests:
            print("🎯 総合評価: A+ (完璧！)")
            print("✅ すべてのAPIが実データを正常に取得")
            print("✅ モックデータは検出されませんでした")
        elif individual_success >= total_apis * 0.8 and unified_success >= total_tests * 0.8:
            print("🎯 総合評価: A (良好)")
        else:
            print("🎯 総合評価: B (要改善)")
        
        return {
            "individual_success_rate": individual_success / total_apis,
            "unified_success_rate": unified_success / total_tests,
            "timestamp": datetime.now().isoformat()
        }

def main():
    print("統合検索エンジン 実データ検証開始")
    print("モックデータ禁止制約を遵守し、実在する商品データのみを検証します")
    
    tester = UnifiedSearchTester()
    
    # 個別APIテスト
    individual_results = tester.test_individual_apis()
    
    # 統合検索テスト
    unified_results = tester.test_unified_search()
    
    # レポート生成
    report = tester.generate_report(individual_results, unified_results)
    
    # 結果をファイルに保存
    result_data = {
        "individual_results": individual_results,
        "unified_results": unified_results,
        "report": report
    }
    
    with open('unified_search_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細結果を unified_search_test_results.json に保存しました")

if __name__ == "__main__":
    main()
