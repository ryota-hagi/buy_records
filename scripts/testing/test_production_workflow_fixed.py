#!/usr/bin/env python3
"""
本番環境統合ワークフロー検証スクリプト（修正版）
JANコード: 4902370536485
URL: https://buy-records.vercel.app/
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ProductionWorkflowTesterFixed:
    def __init__(self, base_url: str, jan_code: str):
        self.base_url = base_url.rstrip('/')
        self.jan_code = jan_code
        self.results = {}
        self.start_time = None
        
    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_individual_platform(self, platform: str, limit: int = 20) -> Dict[str, Any]:
        """個別プラットフォームのテスト（修正版）"""
        self.log(f"🔍 {platform}プラットフォームのテスト開始...")
        
        url = f"{self.base_url}/api/search/{platform}"
        
        # 正しいパラメータ名を使用
        params = {
            'jan_code': self.jan_code,  # queryではなくjan_codeを使用
            'limit': limit
        }
        
        start_time = time.time()
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'response_time': round(response_time, 2),
                    'data_count': len(data.get('data', [])),
                    'total': data.get('total', 0),
                    'platform': data.get('platform', platform),
                    'jan_code': data.get('jan_code', ''),
                    'limit': data.get('limit', 0),
                    'sample_data': data.get('data', [])[:3] if data.get('data') else [],
                    'raw_response': data
                }
                
                self.log(f"✅ {platform}: {result['data_count']}件取得 ({response_time:.2f}秒)")
                return result
                
            else:
                result = {
                    'status': 'error',
                    'status_code': response.status_code,
                    'response_time': round(response_time, 2),
                    'error': response.text,
                    'data_count': 0
                }
                
                self.log(f"❌ {platform}: エラー {response.status_code}")
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                'status': 'exception',
                'response_time': round(response_time, 2),
                'error': str(e),
                'data_count': 0
            }
            
            self.log(f"💥 {platform}: 例外発生 - {str(e)}")
            return result
    
    def test_unified_search(self, limit: int = 20) -> Dict[str, Any]:
        """統合検索のテスト（修正版）"""
        self.log("🔍 統合検索のテスト開始...")
        
        url = f"{self.base_url}/api/search/all"
        
        # 正しいパラメータ名を使用
        params = {
            'jan_code': self.jan_code,  # queryではなくjan_codeを使用
            'limit': limit
        }
        
        start_time = time.time()
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # プラットフォーム別の件数を集計
                platform_counts = {}
                if 'results' in data:
                    for item in data['results']:
                        platform = item.get('platform', 'unknown')
                        platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                result = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'response_time': round(response_time, 2),
                    'total_results': len(data.get('results', [])),
                    'platforms': data.get('platforms', []),
                    'platform_counts': platform_counts,
                    'jan_code': data.get('jan_code', ''),
                    'timestamp': data.get('timestamp', ''),
                    'errors': data.get('errors', {}),
                    'sample_data': data.get('results', [])[:5] if data.get('results') else [],
                    'raw_response': data
                }
                
                self.log(f"✅ 統合検索: {result['total_results']}件取得 ({response_time:.2f}秒)")
                self.log(f"   プラットフォーム別: {platform_counts}")
                return result
                
            else:
                result = {
                    'status': 'error',
                    'status_code': response.status_code,
                    'response_time': round(response_time, 2),
                    'error': response.text,
                    'total_results': 0
                }
                
                self.log(f"❌ 統合検索: エラー {response.status_code}")
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                'status': 'exception',
                'response_time': round(response_time, 2),
                'error': str(e),
                'total_results': 0
            }
            
            self.log(f"💥 統合検索: 例外発生 - {str(e)}")
            return result
    
    def test_alternative_endpoints(self) -> Dict[str, Any]:
        """代替エンドポイントのテスト"""
        self.log("🔍 代替エンドポイントの探索...")
        
        # 可能性のあるエンドポイントをテスト
        alternative_endpoints = [
            '/api/search/tasks',
            '/api/items',
            '/api/search/test',
            '/api/debug/env'
        ]
        
        results = {}
        
        for endpoint in alternative_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                results[endpoint] = {
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'response_size': len(response.content)
                }
                self.log(f"   {endpoint}: {response.status_code}")
            except Exception as e:
                results[endpoint] = {
                    'error': str(e)
                }
                self.log(f"   {endpoint}: エラー - {str(e)}")
        
        return results
    
    def run_full_test(self) -> Dict[str, Any]:
        """完全なテストの実行（修正版）"""
        self.start_time = time.time()
        self.log("🚀 本番環境統合ワークフロー検証開始（修正版）")
        self.log(f"   JANコード: {self.jan_code}")
        self.log(f"   URL: {self.base_url}")
        self.log("=" * 60)
        
        # 代替エンドポイントの探索
        alternative_results = self.test_alternative_endpoints()
        
        self.log("-" * 60)
        
        # 個別プラットフォームテスト
        platforms = ['yahoo', 'ebay', 'mercari']
        platform_results = {}
        
        for platform in platforms:
            platform_results[platform] = self.test_individual_platform(platform)
            time.sleep(1)  # API制限を考慮した間隔
        
        self.log("-" * 60)
        
        # 統合検索テスト
        unified_result = self.test_unified_search()
        
        # 総実行時間
        total_time = time.time() - self.start_time
        
        # 結果の集計
        self.results = {
            'test_info': {
                'jan_code': self.jan_code,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2)
            },
            'alternative_endpoints': alternative_results,
            'individual_platforms': platform_results,
            'unified_search': unified_result,
            'summary': self.generate_summary(platform_results, unified_result)
        }
        
        self.log("=" * 60)
        self.log("📊 テスト結果サマリー")
        self.print_summary()
        
        return self.results
    
    def generate_summary(self, platform_results: Dict, unified_result: Dict) -> Dict[str, Any]:
        """結果サマリーの生成"""
        summary = {
            'overall_status': 'success',
            'platform_success_count': 0,
            'platform_total_count': len(platform_results),
            'unified_search_status': unified_result.get('status', 'unknown'),
            'total_data_retrieved': 0,
            'average_response_time': 0,
            'issues': []
        }
        
        response_times = []
        
        # 個別プラットフォームの評価
        for platform, result in platform_results.items():
            if result.get('status') == 'success':
                summary['platform_success_count'] += 1
                summary['total_data_retrieved'] += result.get('data_count', 0)
            else:
                summary['issues'].append(f"{platform}プラットフォームでエラー: {result.get('error', 'Unknown error')}")
            
            if 'response_time' in result:
                response_times.append(result['response_time'])
        
        # 統合検索の評価
        if unified_result.get('status') == 'success':
            summary['unified_search_data_count'] = unified_result.get('total_results', 0)
        else:
            summary['issues'].append(f"統合検索でエラー: {unified_result.get('error', 'Unknown error')}")
            summary['overall_status'] = 'partial_failure'
        
        # 統合検索のレスポンス時間も追加
        if 'response_time' in unified_result:
            response_times.append(unified_result['response_time'])
        
        # 平均レスポンス時間
        if response_times:
            summary['average_response_time'] = round(sum(response_times) / len(response_times), 2)
        
        # 全体ステータスの判定
        if summary['platform_success_count'] == 0:
            summary['overall_status'] = 'failure'
        elif summary['platform_success_count'] < summary['platform_total_count']:
            summary['overall_status'] = 'partial_success'
        
        return summary
    
    def print_summary(self):
        """サマリーの表示"""
        summary = self.results['summary']
        
        self.log(f"全体ステータス: {summary['overall_status']}")
        self.log(f"成功プラットフォーム: {summary['platform_success_count']}/{summary['platform_total_count']}")
        self.log(f"統合検索ステータス: {summary['unified_search_status']}")
        self.log(f"取得データ総数: {summary['total_data_retrieved']}件")
        self.log(f"平均レスポンス時間: {summary['average_response_time']}秒")
        
        if summary['issues']:
            self.log("⚠️  検出された問題:")
            for issue in summary['issues']:
                self.log(f"   - {issue}")
        
        # 詳細結果
        self.log("\n📋 詳細結果:")
        for platform, result in self.results['individual_platforms'].items():
            status_icon = "✅" if result.get('status') == 'success' else "❌"
            self.log(f"   {status_icon} {platform}: {result.get('data_count', 0)}件 ({result.get('response_time', 0)}秒)")
        
        unified = self.results['unified_search']
        status_icon = "✅" if unified.get('status') == 'success' else "❌"
        self.log(f"   {status_icon} 統合検索: {unified.get('total_results', 0)}件 ({unified.get('response_time', 0)}秒)")
        
        # 代替エンドポイント結果
        self.log("\n🔍 代替エンドポイント:")
        for endpoint, result in self.results['alternative_endpoints'].items():
            if 'status_code' in result:
                self.log(f"   {endpoint}: {result['status_code']}")
            else:
                self.log(f"   {endpoint}: エラー")
    
    def save_results(self, filename: str = None):
        """結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_workflow_test_fixed_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.log(f"💾 結果を {filename} に保存しました")
        return filename

def main():
    """メイン実行関数"""
    # テスト設定
    BASE_URL = "https://buy-records.vercel.app"
    JAN_CODE = "4902370536485"
    
    # テスト実行
    tester = ProductionWorkflowTesterFixed(BASE_URL, JAN_CODE)
    results = tester.run_full_test()
    
    # 結果保存
    filename = tester.save_results()
    
    print(f"\n🎯 検証完了！結果は {filename} に保存されました。")
    
    return results

if __name__ == "__main__":
    main()
