#!/usr/bin/env python3
"""
本番環境API深層デバッグスクリプト
個別APIエンドポイントの詳細テストと問題特定
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ProductionAPIDeepDebugger:
    def __init__(self, base_url: str, jan_code: str):
        self.base_url = base_url.rstrip('/')
        self.jan_code = jan_code
        self.results = {}
        
    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_individual_api(self, platform: str, endpoint: str) -> Dict[str, Any]:
        """個別APIエンドポイントのテスト"""
        self.log(f"🔍 {platform} API テスト開始: {endpoint}")
        
        url = f"{self.base_url}{endpoint}"
        params = {'query': self.jan_code, 'limit': 5}
        
        try:
            # リクエスト詳細をログ
            self.log(f"   URL: {url}")
            self.log(f"   パラメータ: {params}")
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            result = {
                'platform': platform,
                'endpoint': endpoint,
                'url': url,
                'params': params,
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content)
            }
            
            self.log(f"   ステータス: {response.status_code}")
            self.log(f"   レスポンス時間: {response_time:.2f}秒")
            self.log(f"   Content-Type: {result['content_type']}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                    result['data_type'] = 'json'
                    
                    # データ構造の分析
                    if isinstance(data, dict):
                        if 'success' in data:
                            result['api_success'] = data['success']
                            self.log(f"   API成功フラグ: {data['success']}")
                        
                        if 'results' in data:
                            results_count = len(data['results']) if isinstance(data['results'], list) else 0
                            result['results_count'] = results_count
                            self.log(f"   結果件数: {results_count}件")
                            
                            # サンプルデータの確認
                            if results_count > 0:
                                sample = data['results'][0]
                                result['sample_item'] = sample
                                self.log(f"   サンプル商品: {sample.get('title', 'タイトル不明')}")
                                self.log(f"   サンプル価格: ¥{sample.get('price', 0):,}")
                        
                        if 'error' in data:
                            result['api_error'] = data['error']
                            self.log(f"   APIエラー: {data['error']}")
                    
                    self.log(f"   ✅ {platform}: JSON解析成功")
                    
                except json.JSONDecodeError as e:
                    result['data'] = response.text[:500]
                    result['data_type'] = 'text'
                    result['json_error'] = str(e)
                    self.log(f"   ❌ {platform}: JSON解析失敗 - {str(e)}")
                    
            else:
                result['error'] = response.text[:500]
                self.log(f"   ❌ {platform}: HTTPエラー {response.status_code}")
                
                # エラーレスポンスの詳細
                try:
                    error_data = response.json()
                    result['error_data'] = error_data
                    self.log(f"   エラー詳細: {error_data}")
                except:
                    self.log(f"   エラー内容: {response.text[:200]}")
            
            return result
            
        except requests.exceptions.Timeout:
            result = {
                'platform': platform,
                'endpoint': endpoint,
                'error': 'Timeout',
                'error_type': 'timeout'
            }
            self.log(f"   ⏰ {platform}: タイムアウト")
            return result
            
        except requests.exceptions.ConnectionError as e:
            result = {
                'platform': platform,
                'endpoint': endpoint,
                'error': str(e),
                'error_type': 'connection_error'
            }
            self.log(f"   🔌 {platform}: 接続エラー - {str(e)}")
            return result
            
        except Exception as e:
            result = {
                'platform': platform,
                'endpoint': endpoint,
                'error': str(e),
                'error_type': 'unknown_error'
            }
            self.log(f"   💥 {platform}: 不明なエラー - {str(e)}")
            return result
    
    def test_unified_search(self) -> Dict[str, Any]:
        """統合検索APIのテスト"""
        self.log("🔍 統合検索API テスト開始")
        
        url = f"{self.base_url}/api/search/all"
        params = {'query': self.jan_code, 'limit': 5}
        
        try:
            self.log(f"   URL: {url}")
            self.log(f"   パラメータ: {params}")
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=60)  # 統合検索は時間がかかる可能性
            response_time = time.time() - start_time
            
            result = {
                'endpoint': '/api/search/all',
                'url': url,
                'params': params,
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content)
            }
            
            self.log(f"   ステータス: {response.status_code}")
            self.log(f"   レスポンス時間: {response_time:.2f}秒")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                    result['data_type'] = 'json'
                    
                    # 統合結果の分析
                    if isinstance(data, dict):
                        if 'platforms' in data:
                            platform_counts = {}
                            total_results = 0
                            
                            for platform, platform_data in data['platforms'].items():
                                count = len(platform_data) if isinstance(platform_data, list) else 0
                                platform_counts[platform] = count
                                total_results += count
                                self.log(f"   {platform}: {count}件")
                            
                            result['platform_counts'] = platform_counts
                            result['total_results'] = total_results
                            self.log(f"   総結果数: {total_results}件")
                        
                        if 'error' in data:
                            result['api_error'] = data['error']
                            self.log(f"   統合検索エラー: {data['error']}")
                    
                    self.log(f"   ✅ 統合検索: JSON解析成功")
                    
                except json.JSONDecodeError as e:
                    result['data'] = response.text[:500]
                    result['data_type'] = 'text'
                    result['json_error'] = str(e)
                    self.log(f"   ❌ 統合検索: JSON解析失敗 - {str(e)}")
            else:
                result['error'] = response.text[:500]
                self.log(f"   ❌ 統合検索: HTTPエラー {response.status_code}")
            
            return result
            
        except Exception as e:
            result = {
                'endpoint': '/api/search/all',
                'error': str(e),
                'error_type': 'exception'
            }
            self.log(f"   💥 統合検索: 例外 - {str(e)}")
            return result
    
    def test_environment_endpoints(self) -> Dict[str, Any]:
        """環境情報エンドポイントのテスト"""
        self.log("🔍 環境情報エンドポイント テスト")
        
        endpoints = [
            '/api/debug/env',
            '/api/search/test',
            '/api/items'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            
            try:
                response = requests.get(url, timeout=10)
                
                result = {
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'response_size': len(response.content)
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['data'] = data
                        result['data_type'] = 'json'
                    except:
                        result['data'] = response.text[:200]
                        result['data_type'] = 'text'
                else:
                    result['error'] = response.text[:200]
                
                results[endpoint] = result
                self.log(f"   {endpoint}: {response.status_code}")
                
            except Exception as e:
                results[endpoint] = {
                    'error': str(e),
                    'error_type': 'exception'
                }
                self.log(f"   {endpoint}: エラー - {str(e)}")
        
        return results
    
    def run_deep_debug(self) -> Dict[str, Any]:
        """深層デバッグの実行"""
        start_time = time.time()
        self.log("🚀 本番環境API深層デバッグ開始")
        self.log(f"   JANコード: {self.jan_code}")
        self.log(f"   URL: {self.base_url}")
        self.log("=" * 60)
        
        # 1. 個別APIテスト
        individual_apis = [
            ('Yahoo!ショッピング', '/api/search/yahoo'),
            ('eBay', '/api/search/ebay'),
            ('Mercari', '/api/search/mercari')
        ]
        
        api_results = {}
        for platform, endpoint in individual_apis:
            self.log("-" * 40)
            api_results[platform] = self.test_individual_api(platform, endpoint)
            time.sleep(1)  # API制限を考慮
        
        # 2. 統合検索テスト
        self.log("-" * 40)
        unified_result = self.test_unified_search()
        
        # 3. 環境情報テスト
        self.log("-" * 40)
        env_results = self.test_environment_endpoints()
        
        # 4. 総実行時間
        total_time = time.time() - start_time
        
        # 結果の集計
        self.results = {
            'debug_info': {
                'jan_code': self.jan_code,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2)
            },
            'individual_apis': api_results,
            'unified_search': unified_result,
            'environment_endpoints': env_results,
            'summary': self.generate_summary(api_results, unified_result, env_results)
        }
        
        self.log("=" * 60)
        self.log("📊 深層デバッグ結果サマリー")
        self.print_summary()
        
        return self.results
    
    def generate_summary(self, api_results: Dict, unified_result: Dict, env_results: Dict) -> Dict[str, Any]:
        """サマリーの生成"""
        summary = {
            'working_apis': [],
            'failing_apis': [],
            'api_errors': {},
            'unified_search_status': 'unknown',
            'total_results_found': 0,
            'main_issues': []
        }
        
        # 個別API結果の分析
        for platform, result in api_results.items():
            if result.get('status_code') == 200 and result.get('api_success', False):
                summary['working_apis'].append(platform)
                summary['total_results_found'] += result.get('results_count', 0)
            else:
                summary['failing_apis'].append(platform)
                if 'error' in result or 'api_error' in result:
                    summary['api_errors'][platform] = result.get('api_error', result.get('error', 'Unknown error'))
        
        # 統合検索結果の分析
        if unified_result.get('status_code') == 200:
            summary['unified_search_status'] = 'working'
            summary['total_results_found'] += unified_result.get('total_results', 0)
        else:
            summary['unified_search_status'] = 'failing'
        
        # 主要問題の特定
        if len(summary['failing_apis']) == 3:
            summary['main_issues'].append('全ての個別APIが失敗')
        elif len(summary['failing_apis']) > 0:
            summary['main_issues'].append(f'{len(summary["failing_apis"])}個のAPIが失敗')
        
        if summary['unified_search_status'] == 'failing':
            summary['main_issues'].append('統合検索が失敗')
        
        if summary['total_results_found'] == 0:
            summary['main_issues'].append('データ取得件数が0件')
        
        return summary
    
    def print_summary(self):
        """サマリーの表示"""
        summary = self.results['summary']
        
        self.log(f"動作中API: {len(summary['working_apis'])}個")
        for api in summary['working_apis']:
            self.log(f"   ✅ {api}")
        
        self.log(f"失敗API: {len(summary['failing_apis'])}個")
        for api in summary['failing_apis']:
            error = summary['api_errors'].get(api, 'Unknown error')
            self.log(f"   ❌ {api}: {error}")
        
        self.log(f"統合検索: {summary['unified_search_status']}")
        self.log(f"総取得件数: {summary['total_results_found']}件")
        
        if summary['main_issues']:
            self.log("\n🚨 主要問題:")
            for issue in summary['main_issues']:
                self.log(f"   - {issue}")
    
    def save_results(self, filename: str = None):
        """結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_api_deep_debug_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.log(f"💾 結果を {filename} に保存しました")
        return filename

def main():
    """メイン実行関数"""
    # テスト設定
    BASE_URL = "https://buy-records.vercel.app"
    JAN_CODE = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # デバッグ実行
    debugger = ProductionAPIDeepDebugger(BASE_URL, JAN_CODE)
    results = debugger.run_deep_debug()
    
    # 結果保存
    filename = debugger.save_results()
    
    print(f"\n🎯 深層デバッグ完了！結果は {filename} に保存されました。")
    
    return results

if __name__ == "__main__":
    main()
