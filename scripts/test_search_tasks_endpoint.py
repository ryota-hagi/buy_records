#!/usr/bin/env python3
"""
本番環境の/api/search/tasksエンドポイント検証スクリプト
JANコード: 4902370536485
URL: https://buy-records.vercel.app/
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class SearchTasksTester:
    def __init__(self, base_url: str, jan_code: str):
        self.base_url = base_url.rstrip('/')
        self.jan_code = jan_code
        self.results = {}
        
    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_search_tasks_get(self) -> Dict[str, Any]:
        """GET /api/search/tasksのテスト"""
        self.log("🔍 GET /api/search/tasks のテスト...")
        
        url = f"{self.base_url}/api/search/tasks"
        
        try:
            response = requests.get(url, timeout=30)
            
            result = {
                'method': 'GET',
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content)
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                    result['data_type'] = 'json'
                    self.log(f"✅ GET成功: {response.status_code} - JSON形式")
                except:
                    result['data'] = response.text[:500]  # 最初の500文字のみ
                    result['data_type'] = 'text'
                    self.log(f"✅ GET成功: {response.status_code} - テキスト形式")
            else:
                result['error'] = response.text[:500]
                self.log(f"❌ GET失敗: {response.status_code}")
            
            return result
            
        except Exception as e:
            result = {
                'method': 'GET',
                'error': str(e)
            }
            self.log(f"💥 GET例外: {str(e)}")
            return result
    
    def test_search_tasks_post(self) -> Dict[str, Any]:
        """POST /api/search/tasksのテスト"""
        self.log("🔍 POST /api/search/tasks のテスト...")
        
        url = f"{self.base_url}/api/search/tasks"
        
        # 様々なパラメータパターンをテスト
        test_patterns = [
            {
                'name': 'jan_code_only',
                'data': {'jan_code': self.jan_code}
            },
            {
                'name': 'jan_code_with_limit',
                'data': {'jan_code': self.jan_code, 'limit': 20}
            },
            {
                'name': 'query_param',
                'data': {'query': self.jan_code}
            },
            {
                'name': 'product_name',
                'data': {'product_name': 'Nintendo Switch'}
            }
        ]
        
        results = {}
        
        for pattern in test_patterns:
            self.log(f"   テストパターン: {pattern['name']}")
            
            try:
                response = requests.post(url, json=pattern['data'], timeout=30)
                
                result = {
                    'pattern': pattern['name'],
                    'request_data': pattern['data'],
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('content-type', ''),
                    'response_size': len(response.content)
                }
                
                if response.status_code in [200, 201]:
                    try:
                        data = response.json()
                        result['data'] = data
                        result['data_type'] = 'json'
                        
                        # タスクIDがあるかチェック
                        if isinstance(data, dict) and 'task_id' in data:
                            result['task_id'] = data['task_id']
                            self.log(f"   ✅ {pattern['name']}: タスク作成成功 - ID: {data['task_id']}")
                        else:
                            self.log(f"   ✅ {pattern['name']}: 成功 - {response.status_code}")
                            
                    except:
                        result['data'] = response.text[:500]
                        result['data_type'] = 'text'
                        self.log(f"   ✅ {pattern['name']}: 成功 - {response.status_code} (テキスト)")
                else:
                    result['error'] = response.text[:500]
                    self.log(f"   ❌ {pattern['name']}: 失敗 - {response.status_code}")
                
                results[pattern['name']] = result
                time.sleep(1)  # API制限を考慮
                
            except Exception as e:
                results[pattern['name']] = {
                    'pattern': pattern['name'],
                    'request_data': pattern['data'],
                    'error': str(e)
                }
                self.log(f"   💥 {pattern['name']}: 例外 - {str(e)}")
        
        return results
    
    def test_task_status(self, task_id: str) -> Dict[str, Any]:
        """タスクステータスの確認"""
        self.log(f"🔍 タスクステータス確認: {task_id}")
        
        url = f"{self.base_url}/api/search/tasks/{task_id}"
        
        try:
            response = requests.get(url, timeout=30)
            
            result = {
                'task_id': task_id,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', '')
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                    result['data_type'] = 'json'
                    
                    # タスクの状態を確認
                    if isinstance(data, dict):
                        status = data.get('status', 'unknown')
                        result['task_status'] = status
                        self.log(f"   ✅ タスクステータス: {status}")
                        
                        # 結果があるかチェック
                        if 'results' in data or 'data' in data:
                            result['has_results'] = True
                            results_data = data.get('results', data.get('data', []))
                            if isinstance(results_data, list):
                                result['results_count'] = len(results_data)
                                self.log(f"   📊 結果件数: {len(results_data)}件")
                        else:
                            result['has_results'] = False
                    
                except:
                    result['data'] = response.text[:500]
                    result['data_type'] = 'text'
                    self.log(f"   ✅ レスポンス取得成功 (テキスト形式)")
            else:
                result['error'] = response.text[:500]
                self.log(f"   ❌ タスクステータス取得失敗: {response.status_code}")
            
            return result
            
        except Exception as e:
            result = {
                'task_id': task_id,
                'error': str(e)
            }
            self.log(f"   💥 タスクステータス確認例外: {str(e)}")
            return result
    
    def run_full_test(self) -> Dict[str, Any]:
        """完全なテストの実行"""
        start_time = time.time()
        self.log("🚀 /api/search/tasks エンドポイント検証開始")
        self.log(f"   JANコード: {self.jan_code}")
        self.log(f"   URL: {self.base_url}")
        self.log("=" * 60)
        
        # GET テスト
        get_result = self.test_search_tasks_get()
        
        self.log("-" * 60)
        
        # POST テスト
        post_results = self.test_search_tasks_post()
        
        # タスクIDが取得できた場合、ステータスを確認
        task_status_results = {}
        for pattern_name, post_result in post_results.items():
            if 'task_id' in post_result:
                task_id = post_result['task_id']
                self.log("-" * 60)
                task_status_results[task_id] = self.test_task_status(task_id)
                
                # 少し待ってから再度確認
                time.sleep(3)
                self.log(f"🔍 3秒後の再確認: {task_id}")
                task_status_results[f"{task_id}_retry"] = self.test_task_status(task_id)
        
        # 総実行時間
        total_time = time.time() - start_time
        
        # 結果の集計
        self.results = {
            'test_info': {
                'jan_code': self.jan_code,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2)
            },
            'get_test': get_result,
            'post_tests': post_results,
            'task_status_tests': task_status_results,
            'summary': self.generate_summary(get_result, post_results, task_status_results)
        }
        
        self.log("=" * 60)
        self.log("📊 テスト結果サマリー")
        self.print_summary()
        
        return self.results
    
    def generate_summary(self, get_result: Dict, post_results: Dict, task_status_results: Dict) -> Dict[str, Any]:
        """結果サマリーの生成"""
        summary = {
            'get_status': get_result.get('status_code', 'error'),
            'successful_post_patterns': [],
            'created_tasks': [],
            'completed_tasks': [],
            'total_results_found': 0
        }
        
        # POST結果の評価
        for pattern_name, result in post_results.items():
            if result.get('status_code') in [200, 201]:
                summary['successful_post_patterns'].append(pattern_name)
                if 'task_id' in result:
                    summary['created_tasks'].append(result['task_id'])
        
        # タスクステータス結果の評価
        for task_id, result in task_status_results.items():
            if result.get('task_status') == 'completed':
                summary['completed_tasks'].append(task_id)
            if result.get('results_count', 0) > 0:
                summary['total_results_found'] += result['results_count']
        
        return summary
    
    def print_summary(self):
        """サマリーの表示"""
        summary = self.results['summary']
        
        self.log(f"GET /api/search/tasks: {summary['get_status']}")
        self.log(f"成功したPOSTパターン: {len(summary['successful_post_patterns'])}")
        if summary['successful_post_patterns']:
            for pattern in summary['successful_post_patterns']:
                self.log(f"   - {pattern}")
        
        self.log(f"作成されたタスク数: {len(summary['created_tasks'])}")
        self.log(f"完了したタスク数: {len(summary['completed_tasks'])}")
        self.log(f"取得された結果総数: {summary['total_results_found']}件")
    
    def save_results(self, filename: str = None):
        """結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_tasks_test_{timestamp}.json"
        
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
    tester = SearchTasksTester(BASE_URL, JAN_CODE)
    results = tester.run_full_test()
    
    # 結果保存
    filename = tester.save_results()
    
    print(f"\n🎯 検証完了！結果は {filename} に保存されました。")
    
    return results

if __name__ == "__main__":
    main()
