"""
為替レート取得モジュール
ExchangeRate-APIからリアルタイムの為替レートを取得し、キャッシュ機能を提供します。
"""

import json
import os
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import requests

from .config import get_config

logger = logging.getLogger(__name__)


class ExchangeRateClient:
    """為替レート取得クライアント"""
    
    def __init__(self):
        """
        ExchangeRateClientを初期化します。
        """
        self.api_key = get_config("EXCHANGE_RATE_API_KEY", "")
        self.cache_duration_hours = int(get_config("EXCHANGE_RATE_CACHE_HOURS", "24"))
        self.cache_file = "exchange_rate_cache.json"
        self.fallback_rate = 150.0  # API障害時のフォールバックレート
        
        # APIエンドポイント（無料版と有料版に対応）
        if self.api_key:
            self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
        else:
            # 無料版（制限あり）
            self.api_url = "https://api.exchangerate-api.com/v4/latest/USD"
    
    def get_usd_to_jpy_rate(self) -> float:
        """
        USD to JPYの為替レートを取得します。
        キャッシュがある場合はキャッシュから、ない場合はAPIから取得します。
        
        Returns:
            float: USD to JPYの為替レート
        """
        # キャッシュから取得を試行
        cached_rate = self._get_cached_rate()
        if cached_rate is not None:
            logger.info(f"キャッシュから為替レートを取得: {cached_rate}")
            return cached_rate
        
        # APIから取得
        api_rate = self._fetch_rate_from_api()
        if api_rate is not None:
            # キャッシュに保存
            self._save_to_cache(api_rate)
            logger.info(f"APIから為替レートを取得: {api_rate}")
            return api_rate
        
        # フォールバック
        logger.warning(f"API取得に失敗、フォールバックレートを使用: {self.fallback_rate}")
        return self.fallback_rate
    
    def _get_cached_rate(self) -> Optional[float]:
        """
        キャッシュファイルから為替レートを取得します。
        
        Returns:
            Optional[float]: キャッシュされた為替レート（期限切れまたは存在しない場合はNone）
        """
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # キャッシュの有効期限をチェック
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.cache_duration_hours)
            
            if datetime.now() < expiry_time:
                return float(cache_data['usd_to_jpy_rate'])
            else:
                logger.info("キャッシュが期限切れです")
                return None
                
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"キャッシュ読み込みエラー: {e}")
            return None
    
    def _fetch_rate_from_api(self) -> Optional[float]:
        """
        ExchangeRate-APIから為替レートを取得します。
        
        Returns:
            Optional[float]: USD to JPYの為替レート（取得失敗時はNone）
        """
        try:
            logger.info(f"ExchangeRate-APIから為替レートを取得中: {self.api_url}")
            
            headers = {
                'User-Agent': 'JANSearchSystem/1.0'
            }
            
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # APIレスポンスの形式をチェック
            if 'rates' in data and 'JPY' in data['rates']:
                jpy_rate = float(data['rates']['JPY'])
                logger.info(f"API取得成功: 1 USD = {jpy_rate} JPY")
                return jpy_rate
            else:
                logger.error(f"APIレスポンスに期待されるデータが含まれていません: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API リクエストエラー: {e}")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"APIレスポンス解析エラー: {e}")
            return None
    
    def _save_to_cache(self, rate: float) -> None:
        """
        為替レートをキャッシュファイルに保存します。
        
        Args:
            rate: 保存する為替レート
        """
        try:
            cache_data = {
                'usd_to_jpy_rate': rate,
                'timestamp': datetime.now().isoformat(),
                'source': 'ExchangeRate-API'
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"為替レートをキャッシュに保存: {rate}")
            
        except OSError as e:
            logger.warning(f"キャッシュ保存エラー: {e}")
    
    def clear_cache(self) -> None:
        """
        キャッシュファイルを削除します。
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("キャッシュファイルを削除しました")
        except OSError as e:
            logger.warning(f"キャッシュ削除エラー: {e}")
    
    def get_cache_info(self) -> Dict[str, any]:
        """
        キャッシュの情報を取得します。
        
        Returns:
            Dict[str, any]: キャッシュ情報
        """
        try:
            if not os.path.exists(self.cache_file):
                return {'exists': False}
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.cache_duration_hours)
            is_valid = datetime.now() < expiry_time
            
            return {
                'exists': True,
                'rate': cache_data['usd_to_jpy_rate'],
                'timestamp': cache_data['timestamp'],
                'source': cache_data.get('source', 'unknown'),
                'is_valid': is_valid,
                'expires_at': expiry_time.isoformat()
            }
            
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"キャッシュ情報取得エラー: {e}")
            return {'exists': False, 'error': str(e)}


# グローバルインスタンス
_exchange_rate_client = None


def get_exchange_rate_client() -> ExchangeRateClient:
    """
    ExchangeRateClientのシングルトンインスタンスを取得します。
    
    Returns:
        ExchangeRateClient: 為替レートクライアント
    """
    global _exchange_rate_client
    if _exchange_rate_client is None:
        _exchange_rate_client = ExchangeRateClient()
    return _exchange_rate_client


def get_usd_to_jpy_rate() -> float:
    """
    USD to JPYの為替レートを取得します（便利関数）。
    
    Returns:
        float: USD to JPYの為替レート
    """
    client = get_exchange_rate_client()
    return client.get_usd_to_jpy_rate()
