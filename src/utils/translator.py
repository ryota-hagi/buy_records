"""
Google Cloud Translation API翻訳ユーティリティ
日本語商品名を英語に翻訳します。
"""

import os
import json
import re
import logging
import time
from typing import Optional, List, Dict
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

# ログ設定
logger = logging.getLogger(__name__)

class GoogleTranslator:
    """Google Cloud Translation API翻訳クラス"""
    
    def __init__(self):
        """翻訳クラスを初期化"""
        self.client = None
        self.translation_cache = {}  # 翻訳結果キャッシュ
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Cloud Translation APIクライアントを初期化"""
        try:
            # まず環境変数からGoogle Cloud認証情報を取得を試行
            credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON')
            credentials = None
            
            if credentials_json:
                try:
                    # JSON文字列をパース
                    credentials_dict = json.loads(credentials_json)
                    # サービスアカウント認証情報を作成
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=['https://www.googleapis.com/auth/cloud-platform']
                    )
                    logger.info("環境変数からGoogle Cloud認証情報を読み込みました")
                except Exception as env_error:
                    logger.warning(f"環境変数からの認証情報読み込みに失敗: {env_error}")
                    credentials = None
            
            # 環境変数が失敗した場合、ファイルから読み込み
            if not credentials:
                credentials_file = "google-credentials.json"
                if os.path.exists(credentials_file):
                    try:
                        credentials = service_account.Credentials.from_service_account_file(
                            credentials_file,
                            scopes=['https://www.googleapis.com/auth/cloud-platform']
                        )
                        logger.info("ファイルからGoogle Cloud認証情報を読み込みました")
                    except Exception as file_error:
                        logger.warning(f"ファイルからの認証情報読み込みに失敗: {file_error}")
                        credentials = None
                else:
                    logger.warning(f"認証ファイルが見つかりません: {credentials_file}")
            
            if not credentials:
                logger.error("Google Cloud認証情報を取得できませんでした")
                return
            
            # Translation APIクライアントを初期化
            self.client = translate.Client(credentials=credentials)
            logger.info("Google Cloud Translation APIクライアントを初期化しました")
            
        except Exception as e:
            logger.error(f"Google Cloud Translation APIクライアントの初期化に失敗しました: {e}")
            self.client = None
    
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
            logger.warning("Translation APIクライアントが利用できません。元のテキストを返します。")
            return product_name
        
        try:
            # 商品名をクリーニング
            cleaned_name = self._clean_product_name(product_name)
            
            # 日本語テキストかチェック
            if not self.is_japanese_text(cleaned_name):
                logger.debug(f"日本語テキストではありません: {cleaned_name}")
                return cleaned_name
            
            # リトライ機能付きで翻訳実行
            translated_text = self._translate_with_retry(cleaned_name, target_language)
            
            # 翻訳品質をチェック
            if self._is_translation_valid(cleaned_name, translated_text):
                # キャッシュに保存
                self.translation_cache[cache_key] = translated_text
                logger.debug(f"翻訳完了: '{cleaned_name}' -> '{translated_text}'")
                return translated_text
            else:
                logger.warning(f"翻訳品質が低いため、代替翻訳を試行: {translated_text}")
                # 代替翻訳を試行
                alternative_translation = self._get_alternative_translation(cleaned_name)
                self.translation_cache[cache_key] = alternative_translation
                return alternative_translation
            
        except Exception as e:
            logger.error(f"翻訳エラー: {e}")
            # エラー時は元のテキストを返す
            return product_name
    
    def _translate_with_retry(self, text: str, target_language: str, max_retries: int = 3) -> str:
        """
        リトライ機能付きで翻訳を実行します。
        
        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語
            max_retries: 最大リトライ回数
            
        Returns:
            str: 翻訳結果
        """
        for attempt in range(max_retries):
            try:
                result = self.client.translate(
                    text,
                    target_language=target_language,
                    source_language='ja'
                )
                return result['translatedText']
                
            except Exception as e:
                logger.warning(f"翻訳試行 {attempt + 1}/{max_retries} 失敗: {e}")
                if attempt < max_retries - 1:
                    # 指数バックオフで待機
                    wait_time = (2 ** attempt) * 1.0
                    logger.info(f"{wait_time}秒待機してリトライします")
                    time.sleep(wait_time)
                else:
                    raise e
    
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
    
    def _get_alternative_translation(self, product_name: str) -> str:
        """
        代替翻訳戦略を実行します。
        
        Args:
            product_name: 商品名
            
        Returns:
            str: 代替翻訳結果
        """
        try:
            # 商品名を分解して重要な部分を抽出
            components = self._extract_product_components(product_name)
            
            # 各コンポーネントを個別に翻訳
            translated_components = []
            for component in components:
                if component and self.is_japanese_text(component):
                    try:
                        translated = self._translate_with_retry(component, 'en', max_retries=2)
                        if translated and not self.is_japanese_text(translated):
                            translated_components.append(translated)
                    except:
                        # 個別翻訳に失敗した場合はスキップ
                        continue
                elif component:
                    # 日本語でない場合はそのまま追加
                    translated_components.append(component)
            
            if translated_components:
                result = ' '.join(translated_components)
                logger.info(f"代替翻訳成功: '{product_name}' -> '{result}'")
                return result
            else:
                logger.warning(f"代替翻訳も失敗、元のテキストを返します: {product_name}")
                return product_name
                
        except Exception as e:
            logger.error(f"代替翻訳エラー: {e}")
            return product_name
    
    def _extract_product_components(self, product_name: str) -> List[str]:
        """
        商品名から重要なコンポーネントを抽出します。
        
        Args:
            product_name: 商品名
            
        Returns:
            List[str]: 抽出されたコンポーネント
        """
        # 商品名をクリーニング
        cleaned = self._clean_product_name(product_name)
        
        # スペースで分割
        components = cleaned.split()
        
        # 数字+単位のパターンを保持（例: 600ml, 24本）
        unit_pattern = re.compile(r'\d+(?:ml|l|g|kg|本|個|枚|袋|箱|缶|ペット|pet)', re.IGNORECASE)
        
        # ブランド名の可能性が高い単語（カタカナ）を優先
        brand_pattern = re.compile(r'[\u30A0-\u30FF]+')
        
        result = []
        for component in components:
            # 単位付き数字は重要
            if unit_pattern.search(component):
                result.append(component)
            # ブランド名（カタカナ）は重要
            elif brand_pattern.search(component):
                result.append(component)
            # その他の日本語
            elif self.is_japanese_text(component):
                result.append(component)
            # 英数字はそのまま
            else:
                result.append(component)
        
        return result[:5]  # 最大5つのコンポーネントに制限
    
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
            # 1. 完全翻訳
            full_translation = self.translate_product_name(product_name)
            if full_translation and full_translation != product_name:
                queries.append(full_translation)
            
            # 2. コンポーネント別翻訳
            components = self._extract_product_components(product_name)
            if len(components) > 1:
                translated_components = []
                for component in components:
                    if self.is_japanese_text(component):
                        translated = self.translate_product_name(component)
                        if translated and translated != component:
                            translated_components.append(translated)
                    else:
                        translated_components.append(component)
                
                if translated_components:
                    component_query = ' '.join(translated_components)
                    if component_query not in queries:
                        queries.append(component_query)
            
            # 3. ブランド名重視クエリ
            brand_query = self._generate_brand_focused_query(product_name)
            if brand_query and brand_query not in queries:
                queries.append(brand_query)
            
            # 4. 簡略化クエリ
            simplified_query = self._generate_simplified_query(product_name)
            if simplified_query and simplified_query not in queries:
                queries.append(simplified_query)
            
            # 重複を除去し、最大4つのクエリを返す
            unique_queries = []
            for query in queries:
                if query and query not in unique_queries:
                    unique_queries.append(query)
            
            logger.info(f"生成されたクエリ数: {len(unique_queries)} for '{product_name}'")
            for i, query in enumerate(unique_queries, 1):
                logger.debug(f"  {i}. {query}")
            
            return unique_queries[:4]
            
        except Exception as e:
            logger.error(f"複数クエリ生成エラー: {e}")
            # エラー時は基本翻訳のみ返す
            basic_translation = self.translate_product_name(product_name)
            return [basic_translation] if basic_translation else [product_name]
    
    def _generate_brand_focused_query(self, product_name: str) -> Optional[str]:
        """
        ブランド名重視のクエリを生成します。
        
        Args:
            product_name: 商品名
            
        Returns:
            Optional[str]: ブランド重視クエリ
        """
        try:
            # カタカナ部分（ブランド名の可能性）を抽出
            katakana_pattern = re.compile(r'[\u30A0-\u30FF]+')
            katakana_parts = katakana_pattern.findall(product_name)
            
            if katakana_parts:
                # 最も長いカタカナ部分をブランド名とみなす
                brand_name = max(katakana_parts, key=len)
                brand_translated = self.translate_product_name(brand_name)
                
                # 商品カテゴリを推定
                category = self._guess_product_category(product_name)
                
                if brand_translated and category:
                    return f"{brand_translated} {category}"
                elif brand_translated:
                    return brand_translated
            
            return None
            
        except Exception as e:
            logger.error(f"ブランド重視クエリ生成エラー: {e}")
            return None
    
    def _generate_simplified_query(self, product_name: str) -> Optional[str]:
        """
        簡略化クエリを生成します。
        
        Args:
            product_name: 商品名
            
        Returns:
            Optional[str]: 簡略化クエリ
        """
        try:
            # 商品カテゴリのみを抽出
            category = self._guess_product_category(product_name)
            if category:
                return category
            
            # カテゴリが推定できない場合は、最初の重要な単語を使用
            components = self._extract_product_components(product_name)
            if components:
                first_component = components[0]
                if self.is_japanese_text(first_component):
                    return self.translate_product_name(first_component)
                else:
                    return first_component
            
            return None
            
        except Exception as e:
            logger.error(f"簡略化クエリ生成エラー: {e}")
            return None
    
    def _guess_product_category(self, product_name: str) -> Optional[str]:
        """
        商品名からカテゴリを推定します。
        
        Args:
            product_name: 商品名
            
        Returns:
            Optional[str]: 推定されたカテゴリ
        """
        # カテゴリマッピング
        category_keywords = {
            'tea': ['茶', 'ティー', '緑茶', '紅茶', 'お茶'],
            'coffee': ['コーヒー', 'カフェ'],
            'juice': ['ジュース', '果汁'],
            'water': ['水', 'ウォーター'],
            'soda': ['ソーダ', 'コーラ', '炭酸'],
            'beer': ['ビール', 'beer'],
            'sake': ['酒', '日本酒', 'sake'],
            'snack': ['スナック', 'お菓子', 'クッキー'],
            'game': ['ゲーム', 'switch', 'プレステ'],
            'book': ['本', 'ブック', '書籍'],
            'cd': ['cd', 'アルバム', '音楽'],
            'dvd': ['dvd', 'ブルーレイ', '映画']
        }
        
        product_lower = product_name.lower()
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return category
        
        return None
    
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
        elif platform in ['mercari', 'yahoo_shopping']:
            # メルカリとYahoo!ショッピングは日本語のまま
            return product_name
        else:
            # その他のプラットフォームは日本語のまま
            return product_name


# OpenAI翻訳を優先的に使用
try:
    from .openai_translator import translator as openai_translator
    translator = openai_translator
    logger.info("OpenAI翻訳を使用します")
except ImportError:
    # OpenAI翻訳が利用できない場合はGoogle翻訳を使用
    translator = GoogleTranslator()
    logger.info("Google Cloud翻訳を使用します")

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
