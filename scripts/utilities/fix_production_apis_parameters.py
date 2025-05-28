#!/usr/bin/env python3
"""
本番環境API修正スクリプト
正しいパラメータでAPIをテストし、動作確認
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ProductionAPIFixer:
    def __init__(self, base_url: str, jan_code: str):
        self.base_url = base_url.rstrip('/')
        self.jan_code = jan_code
        self.results = {}
        
    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_yahoo_api_fixed(self) -> Dict[str, Any]:
        """Yahoo!ショッピングAPI修正版テスト"""
        self.log("🔧 Yahoo!ショッピングAPI修正版テスト")
        
        url = f"{self.base_url}/api/search/yahoo"
        
        # 複数のパラメータパターンをテスト
        test_patterns = [
            {'jan_code': self.jan_code},
            {'jan_code': self.jan_code, 'limit': 5},
            {'product_name': 'マリオカート8 デラックス'},
            {'product_name': 'マリオカート8 デラックス', 'limit': 5}
        ]
        
        results = {}
        
        for i, params in enumerate(test_patterns, 1):
            self.log(f"   パターン{i}: {params}")
            
            try:
                response = requests.get(url, params=params, timeout=30)
                
                result = {
                    'pattern': i,
                    'params': params,
                    'status_code': response.status_code,
                    'response_time': 0,
                    'content_type': response.headers.get('content-type', '')
                }
                
                self.log(f"   ステータス: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['data'] = data
                        result['success'] = data.get('success', False)
                        
                        if 'results' in data:
                            count = len(data['results']) if isinstance(data['results'], list) else 0
                            result['results_count'] = count
                            self.log(f"   ✅ 成功: {count}件取得")
                            
                            if count > 0:
                                sample = data['results'][0]
                                self.log(f"   サンプル: {sample.get('title', 'タイトル不明')}")
                                self.log(f"   価格: ¥{sample.get('price', 0):,}")
                        else:
                            self.log(f"   ✅ 成功: レスポンス取得")
                            
                    except json.JSONDecodeError:
                        result['data'] = response.text[:200]
                        self.log(f"   ⚠️  JSON解析失敗")
                        
                else:
                    try:
                        error_data = response.json()
                        result['error'] = error_data
                        self.log(f"   ❌ エラー: {error_data}")
                    except:
                        result['error'] = response.text[:200]
                        self.log(f"   ❌ エラー: {response.status_code}")
                
                results[f'pattern_{i}'] = result
                time.sleep(1)
                
            except Exception as e:
                results[f'pattern_{i}'] = {
                    'pattern': i,
                    'params': params,
                    'error': str(e)
                }
                self.log(f"   💥 例外: {str(e)}")
        
        return results
    
    def test_ebay_api_fixed(self) -> Dict[str, Any]:
        """eBayAPI修正版テスト"""
        self.log("🔧 eBayAPI修正版テスト")
        
        url = f"{self.base_url}/api/search/ebay"
        
        # 複数のパラメータパターンをテスト
        test_patterns = [
            {'jan_code': self.jan_code},
            {'jan_code': self.jan_code, 'limit': 5},
            {'product_name': 'Mario Kart 8 Deluxe'},
            {'product_name': 'Nintendo Switch Mario Kart', 'limit': 5}
        ]
        
        results = {}
        
        for i, params in enumerate(test_patterns, 1):
            self.log(f"   パターン{i}: {params}")
            
            try:
                response = requests.get(url, params=params, timeout=30)
                
                result = {
                    'pattern': i,
                    'params': params,
                    'status_code': response.status_code,
                    'response_time': 0,
                    'content_type': response.headers.get('content-type', '')
                }
                
                self.log(f"   ステータス: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['data'] = data
                        result['success'] = data.get('success', False)
                        
                        if 'results' in data:
                            count = len(data['results']) if isinstance(data['results'], list) else 0
                            result['results_count'] = count
                            self.log(f"   ✅ 成功: {count}件取得")
                            
                            if count > 0:
                                sample = data['results'][0]
                                self.log(f"   サンプル: {sample.get('title', 'タイトル不明')}")
                                self.log(f"   価格: ${sample.get('price', 0)}")
                        else:
                            self.log(f"   ✅ 成功: レスポンス取得")
                            
                    except json.JSONDecodeError:
                        result['data'] = response.text[:200]
                        self.log(f"   ⚠️  JSON解析失敗")
                        
                else:
                    try:
                        error_data = response.json()
                        result['error'] = error_data
                        self.log(f"   ❌ エラー: {error_data}")
                    except:
                        result['error'] = response.text[:200]
                        self.log(f"   ❌ エラー: {response.status_code}")
                
                results[f'pattern_{i}'] = result
                time.sleep(1)
                
            except Exception as e:
                results[f'pattern_{i}'] = {
                    'pattern': i,
                    'params': params,
                    'error': str(e)
                }
                self.log(f"   💥 例外: {str(e)}")
        
        return results
    
    def test_task_based_search(self) -> Dict[str, Any]:
        """タスクベース検索の再テスト"""
        self.log("🔧 タスクベース検索再テスト")
        
        # タスク作成
        create_url = f"{self.base_url}/api/search/tasks"
        create_data = {'jan_code': self.jan_code}
        
        try:
            self.log(f"   タスク作成: {create_data}")
            create_response = requests.post(create_url, json=create_data, timeout=30)
            
            if create_response.status_code == 200:
                create_result = create_response.json()
                
                if create_result.get('success') and 'task' in create_result:
                    task_id = create_result['task']['id']
                    self.log(f"   ✅ タスク作成成功: {task_id}")
                    
                    # タスク完了待機
                    status_url = f"{self.base_url}/api/search/tasks/{task_id}"
                    
                    for attempt in range(20):  # 最大60秒待機
                        time.sleep(3)
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            
                            self.log(f"   ステータス確認 {attempt+1}: {status}")
                            
                            if status == 'completed':
                                # 結果の詳細分析
                                result = status_data.get('result', {})
                                platform_results = result.get('platform_results', {})
                                
                                total_results = 0
                                platform_counts = {}
                                
                                for platform, items in platform_results.items():
                                    count = len(items) if isinstance(items, list) else 0
                                    platform_counts[platform] = count
                                    total_results += count
                                    self.log(f"   {platform}: {count}件")
                                
                                return {
                                    'success': True,
                                    'task_id': task_id,
                                    'status': status,
                                    'platform_counts': platform_counts,
                                    'total_results': total_results,
                                    'full_data': status_data
                                }
                            elif status == 'failed':
                                self.log(f"   ❌ タスク失敗")
                                return {
                                    'success': False,
                                    'task_id': task_id,
                                    'status': status,
                                    'error': 'Task failed',
                                    'full_data': status_data
                                }
                        else:
                            self.log(f"   ⚠️  ステータス取得失敗: {status_response.status_code}")
                    
                    self.log(f"   ⏰ タイムアウト")
                    return {
                        'success': False,
                        'task_id': task_id,
                        'error': 'Timeout waiting for completion'
                    }
                else:
                    self.log(f"   ❌ タスク作成レスポンス異常")
                    return {
                        'success': False,
                        'error': 'Invalid task creation response',
                        'response': create_result
                    }
            else:
                self.log(f"   ❌ タスク作成失敗: {create_response.status_code}")
                return {
                    'success': False,
                    'error': f'Task creation failed: {create_response.status_code}',
                    'response': create_response.text[:200]
                }
                
        except Exception as e:
            self.log(f"   💥 例外: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_fix_test(self) -> Dict[str, Any]:
        """修正テストの実行"""
        start_time = time.time()
        self.log("🚀 本番環境API修正テスト開始")
        self.log(f"   JANコード: {self.jan_code}")
        self.log(f"   URL: {self.base_url}")
        self.log("=" * 60)
        
        # 1. Yahoo!ショッピングAPI修正テスト
        yahoo_results = self.test_yahoo_api_fixed()
        
        self.log("-" * 40)
        
        # 2. eBayAPI修正テスト
        ebay_results = self.test_ebay_api_fixed()
        
        self.log("-" * 40)
        
        # 3. タスクベース検索テスト
        task_results = self.test_task_based_search()
        
        # 4. 総実行時間
        total_time = time.time() - start_time
        
        # 結果の集計
        self.results = {
            'fix_test_info': {
                'jan_code': self.jan_code,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2)
            },
            'yahoo_results': yahoo_results,
            'ebay_results': ebay_results,
            'task_results': task_results,
            'summary': self.generate_summary(yahoo_results, ebay_results, task_results)
        }
        
        self.log("=" * 60)
        self.log("📊 修正テスト結果サマリー")
        self.print_summary()
        
        return self.results
    
    def generate_summary(self, yahoo_results: Dict, ebay_results: Dict, task_results: Dict) -> Dict[str, Any]:
        """サマリーの生成"""
        summary = {
            'yahoo_working_patterns': [],
            'ebay_working_patterns': [],
            'task_search_status': 'unknown',
            'total_results_found': 0,
            'working_apis': [],
            'main_findings': []
        }
        
        # Yahoo結果の分析
        for pattern_name, result in yahoo_results.items():
            if result.get('status_code') == 200 and result.get('success', False):
                summary['yahoo_working_patterns'].append(pattern_name)
                summary['total_results_found'] += result.get('results_count', 0)
        
        if summary['yahoo_working_patterns']:
            summary['working_apis'].append('Yahoo!ショッピング')
        
        # eBay結果の分析
        for pattern_name, result in ebay_results.items():
            if result.get('status_code') == 200 and result.get('success', False):
                summary['ebay_working_patterns'].append(pattern_name)
                summary['total_results_found'] += result.get('results_count', 0)
        
        if summary['ebay_working_patterns']:
            summary['working_apis'].append('eBay')
        
        # タスク検索結果の分析
        if task_results.get('success'):
            summary['task_search_status'] = 'working'
            summary['total_results_found'] += task_results.get('total_results', 0)
            summary['working_apis'].append('タスクベース検索')
        else:
            summary['task_search_status'] = 'failing'
        
        # 主要発見事項
        if len(summary['working_apis']) > 0:
            summary['main_findings'].append(f'{len(summary["working_apis"])}個のAPIが正常動作')
        
        if summary['total_results_found'] > 0:
            summary['main_findings'].append(f'総計{summary["total_results_found"]}件のデータ取得成功')
        else:
            summary['main_findings'].append('データ取得件数は依然として0件')
        
        return summary
    
    def print_summary(self):
        """サマリーの表示"""
        summary = self.results['summary']
        
        self.log(f"動作確認済みAPI: {len(summary['working_apis'])}個")
        for api in summary['working_apis']:
            self.log(f"   ✅ {api}")
        
        self.log(f"Yahoo!動作パターン: {len(summary['yahoo_working_patterns'])}個")
        for pattern in summary['yahoo_working_patterns']:
            self.log(f"   ✅ {pattern}")
        
        self.log(f"eBay動作パターン: {len(summary['ebay_working_patterns'])}個")
        for pattern in summary['ebay_working_patterns']:
            self.log(f"   ✅ {pattern}")
        
        self.log(f"タスクベース検索: {summary['task_search_status']}")
        self.log(f"総取得件数: {summary['total_results_found']}件")
        
        if summary['main_findings']:
            self.log("\n🔍 主要発見事項:")
            for finding in summary['main_findings']:
                self.log(f"   - {finding}")
    
    def save_results(self, filename: str = None):
        """結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_api_fix_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.log(f"💾 結果を {filename} に保存しました")
        return filename

def main():
    """メイン実行関数"""
    # テスト設定
    BASE_URL = "https://buy-records.vercel.app"
    JAN_CODE = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # 修正テスト実行
    fixer = ProductionAPIFixer(BASE_URL, JAN_CODE)
    results = fixer.run_fix_test()
    
    # 結果保存
    filename = fixer.save_results()
    
    print(f"\n🎯 修正テスト完了！結果は {filename} に保存されました。")
    
    return results

if __name__ == "__main__":
    main()
