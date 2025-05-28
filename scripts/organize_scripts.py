#!/usr/bin/env python3
"""
スクリプトファイルをカテゴリ別に整理する
"""
import os
import shutil
from pathlib import Path

# カテゴリマッピング
CATEGORY_MAPPING = {
    'testing': ['test_'],
    'search': ['search_', 'fetch_'],
    'debug': ['debug_', 'diagnose_', 'analyze_', 'detect_', 'explain_'],
    'database': ['create_.*table', 'apply_.*table'],
    'utilities': ['check_', 'fix_', 'generate_', 'update_', 'verify_'],
    'deployment': ['deploy_', 'setup', 'force_'],
    'api': ['_api', 'apify_', '_scraper'],
    'runners': ['_runner', 'run_', 'start_', 'simple_', 'continuous_'],
}

# 特定のファイルの例外処理
SPECIAL_CASES = {
    'import_mercari_to_supabase.py': 'database',
    'translate_for_ebay.py': 'utilities',
    'get_exchange_rate.py': 'utilities',
    'list_search_tasks.py': 'database',
    'mcp_visual_scraper.js': 'api',
    'organize_scripts.py': None,  # 移動しない
    'README.md': None,  # 移動しない
}

def categorize_file(filename):
    """ファイルのカテゴリを判定"""
    # 特殊ケースを先にチェック
    if filename in SPECIAL_CASES:
        return SPECIAL_CASES[filename]
    
    # カテゴリマッピングでチェック
    for category, patterns in CATEGORY_MAPPING.items():
        for pattern in patterns:
            if pattern in filename.lower():
                return category
    
    # マッチしない場合は deprecated へ
    return 'deprecated'

def main():
    scripts_dir = Path(__file__).parent
    
    # 移動対象ファイルをリスト化
    files_to_move = []
    for file in scripts_dir.iterdir():
        if file.is_file() and file.suffix in ['.py', '.sh', '.js', '.sql']:
            category = categorize_file(file.name)
            if category:  # None でない場合のみ移動
                files_to_move.append((file, category))
    
    # 移動計画を表示
    print("📋 スクリプト整理計画:")
    print(f"総ファイル数: {len(files_to_move)}")
    print("\nカテゴリ別内訳:")
    
    category_counts = {}
    for _, category in files_to_move:
        category_counts[category] = category_counts.get(category, 0) + 1
    
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}ファイル")
    
    # 自動実行モード
    print("\n🚀 整理を開始します...")
    
    # ファイル移動実行
    moved_count = 0
    for file, category in files_to_move:
        dest_dir = scripts_dir / category
        dest_path = dest_dir / file.name
        
        try:
            # 既存ファイルがある場合は番号を付ける
            if dest_path.exists():
                i = 1
                while dest_path.with_stem(f"{file.stem}_{i}").exists():
                    i += 1
                dest_path = dest_path.with_stem(f"{file.stem}_{i}")
            
            shutil.move(str(file), str(dest_path))
            moved_count += 1
            print(f"✓ {file.name} → {category}/{dest_path.name}")
        except Exception as e:
            print(f"✗ {file.name}: {e}")
    
    print(f"\n✅ 完了: {moved_count}ファイルを移動しました")
    
    # 空のディレクトリを削除
    for category_dir in scripts_dir.iterdir():
        if category_dir.is_dir() and not any(category_dir.iterdir()):
            category_dir.rmdir()
            print(f"🗑️  空のディレクトリを削除: {category_dir.name}")

if __name__ == "__main__":
    main()