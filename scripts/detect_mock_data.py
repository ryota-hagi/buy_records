#!/usr/bin/env python3
"""
モックデータ検出スクリプト
プロジェクト全体をスキャンしてモックデータやハードコーディングを検出します。
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class MockDataDetector:
    """モックデータ検出クラス"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.mock_indicators = [
            'mock', 'sample', 'test', 'dummy', 'fake', 'example',
            'localhost', '127.0.0.1', 'test.com', 'example.com',
            'hardcode', 'hardcoded'
        ]
        
        # 検出パターン
        self.patterns = {
            'mock_variables': re.compile(r'\b(mock|sample|test|dummy|fake)_?\w*\s*=', re.IGNORECASE),
            'mock_functions': re.compile(r'def\s+(mock|sample|test|dummy|fake|generate)\w*\(', re.IGNORECASE),
            'mock_urls': re.compile(r'https?://(localhost|127\.0\.0\.1|test\.com|example\.com)', re.IGNORECASE),
            'hardcoded_jan': re.compile(r'["\']4\d{12}["\']'),
            'hardcoded_prices': re.compile(r'price["\']?\s*[:=]\s*\d+'),
            'mock_data_structures': re.compile(r'\[(.*?)\]', re.DOTALL),
            'sample_files': re.compile(r'(sample|mock|test|dummy).*\.(json|sql|py|js|ts)$', re.IGNORECASE)
        }
        
        # 除外するディレクトリ
        self.exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.next', 'dist', 'build',
            '.vscode', '.idea', 'venv', 'env', 'memory-bank'
        }
        
        # 除外するファイル
        self.exclude_files = {
            'detect_mock_data.py',  # このスクリプト自体
            'anti_mock_config.py',  # モック検出システム
            'anti_mock_guidelines.md'  # ガイドライン
        }

    def scan_project(self) -> Dict[str, List[Dict]]:
        """プロジェクト全体をスキャン"""
        results = {
            'mock_files': [],
            'mock_code': [],
            'hardcoded_values': [],
            'suspicious_patterns': []
        }
        
        for file_path in self._get_files_to_scan():
            try:
                # ファイル名チェック
                if self._is_mock_filename(file_path):
                    results['mock_files'].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'reason': 'モックデータファイル名',
                        'severity': 'high'
                    })
                
                # ファイル内容チェック
                if file_path.suffix in ['.py', '.js', '.ts', '.json', '.sql']:
                    content_issues = self._scan_file_content(file_path)
                    for issue in content_issues:
                        category = issue['category']
                        if category not in results:
                            results[category] = []
                        results[category].append(issue)
                        
            except Exception as e:
                print(f"ファイルスキャンエラー {file_path}: {e}")
        
        return results

    def _get_files_to_scan(self) -> List[Path]:
        """スキャン対象ファイルを取得"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # 除外ディレクトリをスキップ
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                if filename in self.exclude_files:
                    continue
                    
                file_path = Path(root) / filename
                
                # 特定の拡張子のみをスキャン
                if file_path.suffix in ['.py', '.js', '.ts', '.json', '.sql', '.md']:
                    files.append(file_path)
        
        return files

    def _is_mock_filename(self, file_path: Path) -> bool:
        """ファイル名がモックデータを示すかチェック"""
        filename = file_path.name.lower()
        return any(indicator in filename for indicator in self.mock_indicators)

    def _scan_file_content(self, file_path: Path) -> List[Dict]:
        """ファイル内容をスキャン"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    line_issues = self._scan_line(line, line_num, file_path)
                    issues.extend(line_issues)
                    
        except UnicodeDecodeError:
            # バイナリファイルはスキップ
            pass
        except Exception as e:
            print(f"ファイル読み込みエラー {file_path}: {e}")
        
        return issues

    def _scan_line(self, line: str, line_num: int, file_path: Path) -> List[Dict]:
        """行をスキャンして問題を検出"""
        issues = []
        relative_path = str(file_path.relative_to(self.project_root))
        
        # モック変数の検出
        if self.patterns['mock_variables'].search(line):
            issues.append({
                'category': 'mock_code',
                'file': relative_path,
                'line': line_num,
                'content': line.strip(),
                'reason': 'モック変数の定義',
                'severity': 'high'
            })
        
        # モック関数の検出
        if self.patterns['mock_functions'].search(line):
            issues.append({
                'category': 'mock_code',
                'file': relative_path,
                'line': line_num,
                'content': line.strip(),
                'reason': 'モック関数の定義',
                'severity': 'high'
            })
        
        # モックURLの検出
        if self.patterns['mock_urls'].search(line):
            issues.append({
                'category': 'mock_code',
                'file': relative_path,
                'line': line_num,
                'content': line.strip(),
                'reason': 'モックURL',
                'severity': 'medium'
            })
        
        # ハードコーディングされたJANコードの検出
        if self.patterns['hardcoded_jan'].search(line):
            issues.append({
                'category': 'hardcoded_values',
                'file': relative_path,
                'line': line_num,
                'content': line.strip(),
                'reason': 'ハードコーディングされたJANコード',
                'severity': 'medium'
            })
        
        # 疑わしいパターンの検出
        line_lower = line.lower()
        for indicator in self.mock_indicators:
            if indicator in line_lower and ('=' in line or ':' in line):
                issues.append({
                    'category': 'suspicious_patterns',
                    'file': relative_path,
                    'line': line_num,
                    'content': line.strip(),
                    'reason': f'疑わしいパターン: {indicator}',
                    'severity': 'low'
                })
                break
        
        return issues

    def generate_report(self, results: Dict[str, List[Dict]]) -> str:
        """レポートを生成"""
        report = []
        report.append("=" * 60)
        report.append("モックデータ検出レポート")
        report.append("=" * 60)
        report.append("")
        
        total_issues = sum(len(issues) for issues in results.values())
        report.append(f"総検出数: {total_issues}件")
        report.append("")
        
        # カテゴリ別サマリー
        for category, issues in results.items():
            if not issues:
                continue
                
            category_name = {
                'mock_files': 'モックファイル',
                'mock_code': 'モックコード',
                'hardcoded_values': 'ハードコーディング',
                'suspicious_patterns': '疑わしいパターン'
            }.get(category, category)
            
            report.append(f"## {category_name} ({len(issues)}件)")
            report.append("")
            
            # 重要度別に分類
            high_severity = [i for i in issues if i.get('severity') == 'high']
            medium_severity = [i for i in issues if i.get('severity') == 'medium']
            low_severity = [i for i in issues if i.get('severity') == 'low']
            
            for severity, severity_issues in [('高', high_severity), ('中', medium_severity), ('低', low_severity)]:
                if not severity_issues:
                    continue
                    
                report.append(f"### 重要度: {severity} ({len(severity_issues)}件)")
                report.append("")
                
                for issue in severity_issues[:10]:  # 最大10件まで表示
                    if 'line' in issue:
                        report.append(f"- {issue['file']}:{issue['line']}")
                        report.append(f"  理由: {issue['reason']}")
                        report.append(f"  内容: {issue['content']}")
                    else:
                        report.append(f"- {issue['file']}")
                        report.append(f"  理由: {issue['reason']}")
                    report.append("")
                
                if len(severity_issues) > 10:
                    report.append(f"... 他{len(severity_issues) - 10}件")
                    report.append("")
            
            report.append("")
        
        # 推奨アクション
        report.append("## 推奨アクション")
        report.append("")
        
        if results['mock_files']:
            report.append("1. モックファイルの削除または名前変更")
            for issue in results['mock_files'][:5]:
                report.append(f"   - {issue['file']}")
            report.append("")
        
        if results['mock_code']:
            report.append("2. モックコードの実データ取得への変更")
            report.append("   - 実際のAPI呼び出しに置き換え")
            report.append("   - 環境変数による設定に変更")
            report.append("")
        
        if results['hardcoded_values']:
            report.append("3. ハードコーディングされた値の設定化")
            report.append("   - 環境変数への移行")
            report.append("   - 設定ファイルの使用")
            report.append("")
        
        report.append("詳細は docs/anti_mock_guidelines.md を参照してください。")
        
        return "\n".join(report)

def main():
    """メイン関数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("モックデータ検出を開始します...")
    print(f"プロジェクトルート: {project_root}")
    print()
    
    detector = MockDataDetector(project_root)
    results = detector.scan_project()
    
    # レポート生成
    report = detector.generate_report(results)
    print(report)
    
    # レポートファイルに保存
    report_file = os.path.join(project_root, 'mock_data_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nレポートを保存しました: {report_file}")
    
    # 重要な問題がある場合は終了コード1を返す
    high_severity_count = sum(
        len([i for i in issues if i.get('severity') == 'high'])
        for issues in results.values()
    )
    
    if high_severity_count > 0:
        print(f"\n⚠️  重要度「高」の問題が{high_severity_count}件見つかりました。")
        print("これらの問題は優先的に修正してください。")
        return 1
    else:
        print("\n✅ 重要度「高」の問題は見つかりませんでした。")
        return 0

if __name__ == "__main__":
    sys.exit(main())
