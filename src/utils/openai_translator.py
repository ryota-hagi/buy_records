"""
OpenAI API翻訳ユーティリティ
日本語商品名を英語に翻訳します。
"""

import os
import re
import logging
from typing import Optional, List
import openai

# ログ設定
logger = logging.getLogger(__name__)

class OpenAITranslator:
    """OpenAI API翻訳クラス"""
    
    def __init__(self):
        """翻訳クラスを初期化"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI APIクライアントを初期化しました")
        else:
            self.client = None
            logger.warning("OpenAI APIキーが設定されていません")
        
        self.translation_cache = {}  # 翻訳結果キャッシュ
    
    def translate_product_name(self, product_name: str, target_language: str = 'en') -> str:
        """
        商品名を指定言語に翻訳します。
        
        Args:
            product_name: 翻訳対象の商品名
            target_language: 翻訳先言語コード（デフォルト: 'en'）
            
        Returns:
            str: 翻訳された商品名（翻訳に失敗した場合は元の商品名）
        """
        if not product_name:
            return ""
        
        # キャッシュをチェック
        cache_key = f"{product_name}_{target_language}"
        if cache_key in self.translation_cache:
            logger.debug(f"キャッシュから翻訳結果を取得: {product_name}")
            return self.translation_cache[cache_key]
        
        # クライアントが初期化されていない場合は元のテキストを返す
        if not self.client:
            logger.warning("OpenAI APIクライアントが利用できません。元のテキストを返します。")
            return product_name
        
        try:
            # 商品名をクリーニング
            cleaned_name = self._clean_product_name(product_name)
            
            # 日本語テキストかチェック
            if not self.is_japanese_text(cleaned_name):
                logger.debug(f"日本語テキストではありません: {cleaned_name}")
                return cleaned_name
            
            # OpenAI APIで翻訳
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in product names. Translate Japanese product names to English accurately, preserving brand names and product specifications."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this Japanese product name to English: {cleaned_name}"
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # 翻訳品質をチェック
            if self._is_translation_valid(cleaned_name, translated_text):
                # キャッシュに保存
                self.translation_cache[cache_key] = translated_text
                logger.debug(f"翻訳完了: '{cleaned_name}' -> '{translated_text}'")
                return translated_text
            else:
                logger.warning(f"翻訳品質が低いため、元のテキストを返します: {translated_text}")
                return product_name
            
        except Exception as e:
            logger.error(f"翻訳エラー: {e}")
            # エラー時は元のテキストを返す
            return product_name
    
    def _is_translation_valid(self, original: str, translated: str) -> bool:
        """
        翻訳結果の品質をチェックします。
        
        Args:
            original: 元のテキスト
            translated: 翻訳されたテキスト
            
        Returns:
            bool: 翻訳が有効な場合True
        """
        if not translated or translated.strip() == "":
            return False
        
        # 翻訳結果が元のテキストと同じ場合は無効
        if original.strip() == translated.strip():
            return False
        
        # 翻訳結果が日本語を含んでいる場合は無効
        if self.is_japanese_text(translated):
            return False
        
        # 翻訳結果が短すぎる場合は無効（元のテキストの1/3以下）
        if len(translated) < len(original) / 3:
            return False
        
        return True
    
    def generate_multiple_queries(self, product_name: str) -> List[str]:
        """
        商品名から複数の英語検索クエリを生成します。
        
        Args:
            product_name: 商品名
            
        Returns:
            List[str]: 生成された検索クエリのリスト
        """
        queries = []
        
        try:
            # 基本翻訳
            basic_translation = self.translate_product_name(product_name)
            if basic_translation and basic_translation != product_name:
                queries.append(basic_translation)
            
            # OpenAI APIで複数のバリエーションを生成
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Generate multiple English search queries for the given Japanese product name. Include variations with brand focus, simplified terms, and common alternative names."
                        },
                        {
                            "role": "user",
                            "content": f"Generate 3 different English search queries for this product: {product_name}"
                        }
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                variations = response.choices[0].message.content.strip().split('\n')
                for variation in variations:
                    # 番号や記号を除去
                    clean_variation = re.sub(r'^\d+\.\s*', '', variation).strip()
                    clean_variation = re.sub(r'^[-•]\s*', '', clean_variation).strip()
                    
                    if clean_variation and clean_variation not in queries:
                        queries.append(clean_variation)
            
            # 重複を除去し、最大4つのクエリを返す
            logger.info(f"生成されたクエリ数: {len(queries)} for '{product_name}'")
            for i, query in enumerate(queries[:4], 1):
                logger.debug(f"  {i}. {query}")
            
            return queries[:4]
            
        except Exception as e:
            logger.error(f"複数クエリ生成エラー: {e}")
            # エラー時は基本翻訳のみ返す
            return [product_name]
    
    def _clean_product_name(self, product_name: str) -> str:
        """
        商品名をクリーニングします。
        
        Args:
            product_name: 商品名
            
        Returns:
            str: クリーニングされた商品名
        """
        # 不要な記号を除去
        cleaned = re.sub(r'[【】（）()［］\[\]「」『』〈〉《》]', ' ', product_name)
        cleaned = re.sub(r'[×・･]', ' ', cleaned)
        
        # 複数のスペースを単一のスペースに変換
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 前後のスペースを除去
        cleaned = cleaned.strip()
        
        return cleaned
    
    def is_japanese_text(self, text: str) -> bool:
        """
        テキストに日本語が含まれているかチェックします。
        
        Args:
            text: チェック対象のテキスト
            
        Returns:
            bool: 日本語が含まれている場合True
        """
        # ひらがな、カタカナ、漢字の範囲をチェック
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        return bool(japanese_pattern.search(text))
    
    def get_search_query_for_platform(self, product_name: str, platform: str) -> str:
        """
        プラットフォーム別の検索クエリを生成します。
        
        Args:
            product_name: 商品名
            platform: プラットフォーム名 ('ebay', 'discogs', 'mercari', 'yahoo_shopping')
            
        Returns:
            str: プラットフォーム用の検索クエリ
        """
        if not product_name:
            return ""
        
        # プラットフォーム別の処理
        if platform in ['ebay', 'discogs']:
            # eBayとDiscogsは英語翻訳
            if self.is_japanese_text(product_name):
                translated = self.translate_product_name(product_name)
                logger.info(f"{platform}: 英語翻訳 '{product_name}' -> '{translated}'")
                return translated
            else:
                return product_name
        elif platform in ['mercari', 'yahoo_shopping', 'rakuten', 'paypay', 'rakuma', 'yodobashi']:
            # 日本のプラットフォームは日本語のまま
            return product_name
        else:
            # その他のプラットフォームは日本語のまま
            return product_name


# グローバルインスタンス
translator = OpenAITranslator()

def translate_for_platform(product_name: str, platform: str) -> str:
    """
    プラットフォーム用の翻訳を行う便利関数
    
    Args:
        product_name: 商品名
        platform: プラットフォーム名
        
    Returns:
        str: 翻訳された商品名
    """
    return translator.get_search_query_for_platform(product_name, platform)