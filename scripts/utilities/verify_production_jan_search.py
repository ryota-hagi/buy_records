#!/usr/bin/env python3
"""
本番環境JANコード検索検証スクリプト
JANコード: 4902370536485 (任天堂　マリオカート８ デラックス)
URL: https://buy-records.vercel.app/

モックデータ禁止ルールに従い、実際のデータ抽出件数を確認
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ProductionJANSearchVerifier:
    def __init__(self, base_url: str, jan_code: str):
        self.base_url = base_url.rstrip('/')
        self.jan_code = jan_code
        self.results = {}
        
    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def create_search_task(self) -> Dict[str, Any]:
        """検索タスクの作成"""
        self.log(f"🔍 JANコード {self.jan_code} の検索タスクを作成中...")
        
        url = f"{self.base_url}/api/search/tasks"
        data = {'jan_code': self.jan_code}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'task' in result:
                    task_id = result['task']['id']
                    task_name = result['task']['name']
                    self.log(f"✅ タスク作成成功: {task_id}")
                    self.log(f"   商品名: {task_name}")
                    return {
                        'success': True,
                        'task_id': task_id,
                        'task_name': task_name,
                        'raw_response': result
                    }
                else:
                    self.log(f"❌ タスク作成失敗: レスポンス形式エラー")
                    return {
                        'success': False,
                        'error': 'Invalid response format',
                        'raw_response': result
                    }
            else:
                self.log(f"❌ タスク作成失敗: {response.status_code}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            self.log(f"💥 タスク作成例外: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def wait_for_task_completion(self, task_id: str, max_wait_time: int = 60) -> Dict[str, Any]:
        """タスク完了まで待機"""
        self.log(f"⏳ タスク {task_id} の完了を待機中...")
        
        url = f"{self.base_url}/api/search/tasks/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    self.log(f"   ステータス: {status}")
                    
                    if status == 'completed':
                        self.log(f"✅ タスク完了")
                        return {
                            'success': True,
                            'status': status,
                            'data': data
                        }
                    elif status == 'failed':
                        self.log(f"❌ タスク失敗")
                        return {
                            'success': False,
                            'status': status,
                            'data': data
                        }
                    elif status in ['pending', 'running']:
                        # 継続して待機
                        time.sleep(3)
                        continue
                    else:
                        self.log(f"⚠️  不明なステータス: {status}")
                        time.sleep(3)
                        continue
                else:
                    self.log(f"❌ ステータス取得失敗: {response.status_code}")
                    return {
                        'success': False,
                        'error': f"HTTP {response.status_code}: {response.text}"
                    }
                    
            except Exception as e:
                self.log(f"💥 ステータス確認例外: {str(e)}")
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # タイムアウト
        self.log(f"⏰ タイムアウト: {max_wait_time}秒経過")
        return {
            'success': False,
            'error': f'Timeout after {max_wait_time} seconds'
        }
    
    def analyze_search_results(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """検索結果の分析"""
        self.log("📊 検索結果を分析中...")
        
        analysis = {
            'task_id': task_data.get('id', ''),
            'task_name': task_data.get('name', ''),
            'status': task_data.get('status', ''),
            'platforms_searched': [],
            'platform_counts': {},
            'total_results': 0,
            'has_mock_data': False,
            'mock_data_indicators': [],
            'real_data_indicators': [],
            'sample_results': {}
        }
        
        # 検索パラメータの確認
        search_params = task_data.get('search_params', {})
        analysis['platforms_searched'] = search_params.get('platforms', [])
        
        # 結果の分析
        result = task_data.get('result', {})
        if result:
            # プラットフォーム別件数
            platform_results = result.get('platform_results', {})
            for platform, items in platform_results.items():
                count = len(items) if isinstance(items, list) else 0
                analysis['platform_counts'][platform] = count
                analysis['total_results'] += count
                
                # サンプルデータの保存
                if items and isinstance(items, list):
                    analysis['sample_results'][platform] = items[:2]  # 最初の2件
                    
                    # モックデータの検出
                    for item in items:
                        if self.detect_mock_data(item, platform):
                            analysis['has_mock_data'] = True
                            analysis['mock_data_indicators'].append(f"{platform}: {item.get('item_title', 'Unknown')}")
                        else:
                            analysis['real_data_indicators'].append(f"{platform}: {item.get('item_title', 'Unknown')}")
            
            # サマリー情報
            summary = result.get('summary', {})
            analysis['summary'] = {
                'total_found': summary.get('totalFound', 0),
                'final_count': summary.get('finalCount', 0),
                'cheapest_price': summary.get('cheapest', {}).get('price') if summary.get('cheapest') else None,
                'most_expensive_price': summary.get('mostExpensive', {}).get('price') if summary.get('mostExpensive') else None
            }
        
        return analysis
    
    def detect_mock_data(self, item: Dict[str, Any], platform: str) -> bool:
        """モックデータの検出"""
        mock_indicators = [
            # 一般的なモックデータパターン
            'mock', 'test', 'sample', 'dummy', 'fake',
            'example', 'placeholder', 'template',
            
            # プラットフォーム固有のモックパターン
            'mercari_seller_1', 'mercari_seller_2',
            'yahoo_seller_1', 'ebay_seller_1',
            'm12345678901', 'm12345678902',
            
            # 固定価格パターン（明らかに人工的）
            'static.mercdn.net/item/detail/orig/photos/m12345678901',
            'static.mercdn.net/item/detail/orig/photos/m12345678902'
        ]
        
        # アイテムの各フィールドをチェック
        item_str = json.dumps(item, ensure_ascii=False).lower()
        
        for indicator in mock_indicators:
            if indicator.lower() in item_str:
                return True
        
        # 価格が明らかに人工的なパターン
        price = item.get('price', 0)
        if price in [2500, 3200, 1000, 2000, 3000, 5000]:  # よくあるテスト価格
            seller = item.get('seller', '')
            if 'seller_' in seller or seller.startswith('test_'):
                return True
        
        return False
    
    def run_verification(self) -> Dict[str, Any]:
        """検証の実行"""
        start_time = time.time()
        self.log("🚀 本番環境JANコード検索検証開始")
        self.log(f"   JANコード: {self.jan_code}")
        self.log(f"   URL: {self.base_url}")
        self.log("=" * 60)
        
        # 1. タスク作成
        task_creation = self.create_search_task()
        if not task_creation.get('success'):
            return {
                'success': False,
                'error': 'Task creation failed',
                'details': task_creation
            }
        
        task_id = task_creation['task_id']
        
        # 2. タスク完了待機
        task_completion = self.wait_for_task_completion(task_id)
        if not task_completion.get('success'):
            return {
                'success': False,
                'error': 'Task completion failed',
                'task_id': task_id,
                'details': task_completion
            }
        
        # 3. 結果分析
        analysis = self.analyze_search_results(task_completion['data'])
        
        # 4. 総実行時間
        total_time = time.time() - start_time
        
        # 結果の集計
        self.results = {
            'verification_info': {
                'jan_code': self.jan_code,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': round(total_time, 2)
            },
            'task_creation': task_creation,
            'task_completion': task_completion,
            'analysis': analysis,
            'summary': self.generate_summary(analysis)
        }
        
        self.log("=" * 60)
        self.log("📊 検証結果サマリー")
        self.print_summary()
        
        return self.results
    
    def generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """サマリーの生成"""
        return {
            'success': analysis['status'] == 'completed',
            'platforms_tested': len(analysis['platforms_searched']),
            'platforms_with_data': len([p for p, c in analysis['platform_counts'].items() if c > 0]),
            'total_results_found': analysis['total_results'],
            'platform_breakdown': analysis['platform_counts'],
            'has_mock_data': analysis['has_mock_data'],
            'mock_data_count': len(analysis['mock_data_indicators']),
            'real_data_count': len(analysis['real_data_indicators'])
        }
    
    def print_summary(self):
        """サマリーの表示"""
        summary = self.results['summary']
        analysis = self.results['analysis']
        
        self.log(f"検証成功: {summary['success']}")
        self.log(f"テスト対象プラットフォーム: {summary['platforms_tested']}個")
        self.log(f"データ取得成功プラットフォーム: {summary['platforms_with_data']}個")
        self.log(f"総取得件数: {summary['total_results_found']}件")
        
        self.log("\n📋 プラットフォーム別データ抽出件数:")
        for platform, count in summary['platform_breakdown'].items():
            status_icon = "✅" if count > 0 else "❌"
            self.log(f"   {status_icon} {platform}: {count}件")
        
        # モックデータの検出結果
        if summary['has_mock_data']:
            self.log(f"\n⚠️  モックデータ検出: {summary['mock_data_count']}件")
            for indicator in analysis['mock_data_indicators']:
                self.log(f"   - {indicator}")
        else:
            self.log(f"\n✅ モックデータなし: すべて実データ")
        
        # 価格情報
        if 'summary' in analysis and analysis['summary']:
            price_info = analysis['summary']
            if price_info.get('cheapest_price'):
                self.log(f"\n💰 価格情報:")
                self.log(f"   最安値: ¥{price_info['cheapest_price']:,}")
                if price_info.get('most_expensive_price'):
                    self.log(f"   最高値: ¥{price_info['most_expensive_price']:,}")
    
    def save_results(self, filename: str = None):
        """結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_jan_search_verification_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.log(f"💾 結果を {filename} に保存しました")
        return filename

def main():
    """メイン実行関数"""
    # テスト設定
    BASE_URL = "https://buy-records.vercel.app"
    JAN_CODE = "4902370536485"  # 任天堂　マリオカート８ デラックス
    
    # 検証実行
    verifier = ProductionJANSearchVerifier(BASE_URL, JAN_CODE)
    results = verifier.run_verification()
    
    # 結果保存
    filename = verifier.save_results()
    
    print(f"\n🎯 検証完了！結果は {filename} に保存されました。")
    
    return results

if __name__ == "__main__":
    main()
