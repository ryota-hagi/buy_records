#!/usr/bin/env python3
"""
エラー監視スクリプト
24時間体制でAPIエラーを監視し、アラートを生成
"""
import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

class ErrorMonitor:
    def __init__(self, base_url: str = "https://buy-records.vercel.app"):
        self.base_url = base_url
        self.error_threshold = 0.05  # 5%のエラー率
        self.platforms = [
            "rakuten", "yodobashi", "paypay", 
            "rakuma", "ebay", "mercari", "yahoo"
        ]
        self.results_log = []
        self.start_time = datetime.now()
        
    def test_platform(self, platform: str) -> Tuple[bool, float, str]:
        """個別プラットフォームのテスト"""
        try:
            start = time.time()
            response = requests.get(
                f"{self.base_url}/api/search/{platform}",
                params={"jan_code": "4549292184129", "limit": 5},
                timeout=60
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('results'):
                    return True, elapsed, "Success"
                else:
                    return False, elapsed, data.get('error', 'No results')
            else:
                return False, elapsed, f"HTTP {response.status_code}"
                
        except requests.Timeout:
            return False, 60.0, "Timeout"
        except Exception as e:
            return False, 0.0, str(e)
    
    def run_health_check(self) -> Dict:
        """全プラットフォームのヘルスチェック"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "platforms": {},
            "summary": {
                "total": len(self.platforms),
                "success": 0,
                "failed": 0,
                "error_rate": 0.0
            }
        }
        
        for platform in self.platforms:
            success, elapsed, message = self.test_platform(platform)
            results["platforms"][platform] = {
                "success": success,
                "response_time": elapsed,
                "message": message
            }
            
            if success:
                results["summary"]["success"] += 1
            else:
                results["summary"]["failed"] += 1
        
        results["summary"]["error_rate"] = results["summary"]["failed"] / results["summary"]["total"]
        return results
    
    def check_alerts(self, results: Dict) -> List[str]:
        """アラート条件をチェック"""
        alerts = []
        
        # エラー率チェック
        if results["summary"]["error_rate"] > self.error_threshold:
            alerts.append(
                f"⚠️ エラー率が閾値を超えています: {results['summary']['error_rate']:.1%} > {self.error_threshold:.1%}"
            )
        
        # 個別プラットフォームチェック
        for platform, data in results["platforms"].items():
            if not data["success"]:
                alerts.append(f"❌ {platform}: {data['message']}")
            elif data["response_time"] > 30:
                alerts.append(f"⏱️ {platform}: レスポンスタイムが遅い ({data['response_time']:.1f}秒)")
        
        return alerts
    
    def save_results(self, results: Dict, alerts: List[str]):
        """結果をログファイルに保存"""
        log_dir = "logs/monitoring"
        os.makedirs(log_dir, exist_ok=True)
        
        # 日付ごとのログファイル
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"monitor_{date_str}.json")
        
        # 既存のログを読み込み
        existing_logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    existing_logs = json.load(f)
            except:
                existing_logs = []
        
        # 新しい結果を追加
        log_entry = {
            "timestamp": results["timestamp"],
            "results": results,
            "alerts": alerts
        }
        existing_logs.append(log_entry)
        
        # 保存
        with open(log_file, 'w') as f:
            json.dump(existing_logs, f, indent=2, ensure_ascii=False)
    
    def generate_report(self) -> str:
        """監視レポートを生成"""
        # 過去24時間のログを集計
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        total_checks = 0
        platform_stats = {p: {"success": 0, "failed": 0} for p in self.platforms}
        
        # ログファイルから統計を収集
        log_dir = "logs/monitoring"
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.startswith("monitor_") and filename.endswith(".json"):
                    filepath = os.path.join(log_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            logs = json.load(f)
                            for log in logs:
                                log_time = datetime.fromisoformat(log["timestamp"])
                                if start_time <= log_time <= end_time:
                                    total_checks += 1
                                    for platform, data in log["results"]["platforms"].items():
                                        if data["success"]:
                                            platform_stats[platform]["success"] += 1
                                        else:
                                            platform_stats[platform]["failed"] += 1
                    except:
                        continue
        
        # レポート生成
        report = f"""# エラー監視レポート
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
監視期間: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}

## サマリー
- 総チェック回数: {total_checks}
- 監視間隔: 5分

## プラットフォーム別統計
"""
        
        for platform in self.platforms:
            stats = platform_stats[platform]
            total = stats["success"] + stats["failed"]
            if total > 0:
                success_rate = stats["success"] / total * 100
                error_rate = stats["failed"] / total * 100
                report += f"\n### {platform}"
                report += f"\n- 成功: {stats['success']}回"
                report += f"\n- 失敗: {stats['failed']}回"
                report += f"\n- 成功率: {success_rate:.1f}%"
                report += f"\n- エラー率: {error_rate:.1f}%"
                report += "\n"
        
        return report
    
    def monitor_loop(self, interval_minutes: int = 5):
        """監視ループ"""
        print(f"エラー監視を開始します（{interval_minutes}分間隔）")
        print(f"監視URL: {self.base_url}")
        print("Ctrl+Cで停止")
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ヘルスチェック実行中...")
                
                # ヘルスチェック実行
                results = self.run_health_check()
                
                # アラートチェック
                alerts = self.check_alerts(results)
                
                # 結果を保存
                self.save_results(results, alerts)
                
                # コンソール出力
                print(f"成功: {results['summary']['success']}/{results['summary']['total']}")
                print(f"エラー率: {results['summary']['error_rate']:.1%}")
                
                if alerts:
                    print("\n🚨 アラート:")
                    for alert in alerts:
                        print(f"  {alert}")
                else:
                    print("✅ すべて正常")
                
                # 次回まで待機
                print(f"\n次回チェック: {(datetime.now() + timedelta(minutes=interval_minutes)).strftime('%H:%M:%S')}")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n監視を停止しました")
            
            # 最終レポート生成
            print("\n最終レポートを生成中...")
            report = self.generate_report()
            
            # レポートを保存
            report_file = f"logs/monitoring/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"レポートを保存しました: {report_file}")

def main():
    """メイン実行"""
    # コマンドライン引数でURLを指定可能
    base_url = "https://buy-records.vercel.app"
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            base_url = "http://localhost:3000"
    
    # 監視開始
    monitor = ErrorMonitor(base_url)
    
    # 単発チェックモード
    if len(sys.argv) > 2 and sys.argv[2] == "once":
        print("単発ヘルスチェックを実行します...")
        results = monitor.run_health_check()
        alerts = monitor.check_alerts(results)
        
        print(json.dumps(results, indent=2, ensure_ascii=False))
        if alerts:
            print("\nアラート:")
            for alert in alerts:
                print(f"  {alert}")
    else:
        # 継続監視モード
        monitor.monitor_loop(interval_minutes=5)

if __name__ == "__main__":
    main()