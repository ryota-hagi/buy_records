#!/usr/bin/env python3
"""
モックデータ防止設定
本番環境でのモックデータ使用を防ぐための設定とチェック機能
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AntiMockConfig:
    """モックデータ防止設定クラス"""
    
    def __init__(self):
        self.environment = os.environ.get('NODE_ENV', 'development')
        self.is_production = self.environment == 'production'
        self.is_test = self.environment == 'test'
        
        # 本番環境ではモックデータを完全に禁止
        self.allow_mock_data = not self.is_production
        
        # 環境変数での明示的な制御
        mock_override = os.environ.get('ALLOW_MOCK_DATA', '').lower()
        if mock_override in ['false', '0', 'no']:
            self.allow_mock_data = False
        elif mock_override in ['true', '1', 'yes'] and not self.is_production:
            self.allow_mock_data = True
    
    def validate_data_source(self, data_source: str, data: Any) -> bool:
        """データソースの妥当性を検証"""
        if not self.allow_mock_data:
            # 本番環境ではモックデータを検出したらエラー
            if self._is_mock_data(data_source, data):
                raise ValueError(f"本番環境でモックデータが検出されました: {data_source}")
        
        return True
    
    def _is_mock_data(self, data_source: str, data: Any) -> bool:
        """モックデータかどうかを判定"""
        mock_indicators = [
            'mock', 'sample', 'test', 'dummy', 'fake', 'example',
            'localhost', '127.0.0.1', 'test.com', 'example.com'
        ]
        
        # データソース名をチェック
        data_source_lower = data_source.lower()
        if any(indicator in data_source_lower for indicator in mock_indicators):
            return True
        
        # データ内容をチェック
        if isinstance(data, dict):
            return self._check_dict_for_mock_data(data, mock_indicators)
        elif isinstance(data, list):
            return any(self._check_dict_for_mock_data(item, mock_indicators) 
                      for item in data if isinstance(item, dict))
        elif isinstance(data, str):
            return any(indicator in data.lower() for indicator in mock_indicators)
        
        return False
    
    def _check_dict_for_mock_data(self, data: Dict[str, Any], mock_indicators: list) -> bool:
        """辞書データ内のモックデータをチェック"""
        for key, value in data.items():
            key_lower = key.lower()
            
            # キー名をチェック
            if any(indicator in key_lower for indicator in mock_indicators):
                return True
            
            # 値をチェック
            if isinstance(value, str):
                value_lower = value.lower()
                if any(indicator in value_lower for indicator in mock_indicators):
                    return True
            elif isinstance(value, dict):
                if self._check_dict_for_mock_data(value, mock_indicators):
                    return True
        
        return False
    
    def log_data_usage(self, data_source: str, data_type: str, count: int):
        """データ使用状況をログに記録"""
        logger.info(f"データ使用: {data_source} ({data_type}) - {count}件")
        
        if self.is_production:
            # 本番環境では詳細なログを記録
            logger.info(f"本番環境データ使用確認: {data_source}")

# グローバル設定インスタンス
anti_mock_config = AntiMockConfig()

def validate_search_results(results: list, platform: str) -> list:
    """検索結果の妥当性を検証"""
    if not results:
        return results
    
    # データソースを検証
    anti_mock_config.validate_data_source(f"{platform}_search_results", results)
    
    # 使用状況をログに記録
    anti_mock_config.log_data_usage(platform, "search_results", len(results))
    
    return results

def validate_product_data(product_data: dict, source: str) -> dict:
    """商品データの妥当性を検証"""
    anti_mock_config.validate_data_source(f"{source}_product_data", product_data)
    anti_mock_config.log_data_usage(source, "product_data", 1)
    
    return product_data

def is_mock_data_allowed() -> bool:
    """モックデータの使用が許可されているかチェック"""
    return anti_mock_config.allow_mock_data

def get_environment_info() -> dict:
    """環境情報を取得"""
    return {
        'environment': anti_mock_config.environment,
        'is_production': anti_mock_config.is_production,
        'is_test': anti_mock_config.is_test,
        'allow_mock_data': anti_mock_config.allow_mock_data
    }
