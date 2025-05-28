#!/usr/bin/env python3
"""
環境変数読み込みのデバッグスクリプト
"""

import sys
import os
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def debug_env_loading():
    """環境変数の読み込み状況をデバッグします"""
    print("環境変数読み込みデバッグ")
    print("="*50)
    
    print(f"プロジェクトルート: {project_root}")
    print(f"現在の作業ディレクトリ: {os.getcwd()}")
    
    # .envファイルのパスを確認
    env_path = os.path.join(project_root, '.env')
    print(f".envファイルパス: {env_path}")
    print(f".envファイル存在: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        # ファイルサイズを確認
        file_size = os.path.getsize(env_path)
        print(f".envファイルサイズ: {file_size} bytes")
        
        # ファイルの最初の数行を読み込み
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]  # 最初の5行
                print(f".envファイルの最初の数行:")
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line.strip()}")
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
    
    # .envファイルを読み込み
    print(f"\n.env読み込み前の環境変数:")
    ebay_vars = ['EBAY_APP_ID', 'EBAY_USER_TOKEN', 'YAHOO_SHOPPING_APP_ID']
    for var in ebay_vars:
        value = os.environ.get(var)
        print(f"  {var}: {'設定済み' if value else '未設定'}")
    
    # .envファイルを明示的に読み込み
    load_result = load_dotenv(env_path)
    print(f"\n.env読み込み結果: {load_result}")
    
    print(f"\n.env読み込み後の環境変数:")
    for var in ebay_vars:
        value = os.environ.get(var)
        print(f"  {var}: {'設定済み' if value else '未設定'}")
        if value:
            print(f"    値: {value[:20]}...")
    
    # config.pyを使用した読み込みテスト
    print(f"\nconfig.pyを使用した読み込みテスト:")
    try:
        from src.utils.config import get_config
        for var in ebay_vars:
            try:
                value = get_config(var, required=False)
                print(f"  {var}: {'設定済み' if value else '未設定'}")
                if value:
                    print(f"    値: {value[:20]}...")
            except Exception as e:
                print(f"  {var}: エラー - {e}")
    except Exception as e:
        print(f"config.pyインポートエラー: {e}")

if __name__ == "__main__":
    debug_env_loading()
