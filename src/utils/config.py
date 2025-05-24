"""
設定管理モジュール
環境変数からの設定値読み込みを管理します。
"""

import os
from dotenv import load_dotenv
from typing import Optional

# .envファイルを読み込む
load_dotenv()

def get_config(key: str, default: Optional[str] = None, required: bool = True) -> str:
    """
    環境変数から設定値を取得します。
    
    Args:
        key: 環境変数のキー
        default: デフォルト値（省略可）
        required: 必須かどうか（デフォルト: True）
        
    Returns:
        str: 環境変数の値、または指定されたデフォルト値
        
    Raises:
        ValueError: 必須の設定値が見つからない場合
    """
    value = os.environ.get(key, default)
    if value is None and required:
        raise ValueError(f"必須の設定値 '{key}' が環境変数に見つかりません")
    
    if value is None:
        return ""
    
    # コメントが含まれている場合は除去
    if '#' in value:
        value = value.split('#')[0].strip()
    
    return value

def get_optional_config(key: str, default: str = "") -> str:
    """
    オプションの環境変数から設定値を取得します。
    
    Args:
        key: 環境変数のキー
        default: デフォルト値
        
    Returns:
        str: 環境変数の値、またはデフォルト値
    """
    return get_config(key, default, required=False)
