"""
複数のAI Vision APIに対応した画像解析モジュール
"""
import base64
import json
import os
import sys
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

class BaseVisionAnalyzer(ABC):
    """Vision API基底クラス"""
    
    @abstractmethod
    def analyze_image(self, image_base64: str, prompt: str) -> Optional[str]:
        """画像を解析してテキスト結果を返す"""
        pass
    
    @abstractmethod
    def extract_elements(self, image_base64: str) -> List[Dict[str, Any]]:
        """画像から要素（商品、ボタンなど）を抽出"""
        pass

class OpenAIVisionAnalyzer(BaseVisionAnalyzer):
    """OpenAI GPT-4 Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
    
    def analyze_image(self, image_base64: str, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            # GPT-4o-miniを使用（最も安価で高速）
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # 2024年5月時点で最も安価なVisionモデル
                messages=[{
                    "role": "system",
                    "content": "あなたは画像から商品情報を正確に抽出するエキスパートです。JSON形式で結果を返してください。"
                }, {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "low"  # 低解像度設定でコスト削減
                            }
                        }
                    ]
                }],
                max_tokens=2000,  # 十分な出力長
                temperature=0.1,   # 一貫性のある結果
                response_format={"type": "json_object"}  # JSON形式を強制
            )
            
            result_text = response.choices[0].message.content
            
            # JSONとして解析を試みる
            try:
                # JSONブロックを抽出
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # テキスト全体をJSONとして解析
                    return json.loads(result_text)
            except json.JSONDecodeError:
                # JSON解析に失敗した場合はテキストをそのまま返す
                return {"raw_text": result_text}
                
        except Exception as e:
            print(f"OpenAI Vision APIエラー: {e}", file=sys.stderr)
            return None
    
    def extract_elements(self, image_base64: str) -> List[Dict[str, Any]]:
        prompt = """
        画像から以下の要素を検出してJSON形式で返してください：
        1. 商品カード（タイトル、価格、画像位置）
        2. ボタン（次へ、検索など）
        3. 入力フィールド
        
        形式:
        {
            "products": [{"title": "", "price": "", "bounds": {"x": 0, "y": 0, "width": 0, "height": 0}}],
            "buttons": [{"text": "", "bounds": {"x": 0, "y": 0, "width": 0, "height": 0}}],
            "inputs": [{"type": "", "bounds": {"x": 0, "y": 0, "width": 0, "height": 0}}]
        }
        """
        
        result = self.analyze_image(image_base64, prompt)
        if result:
            try:
                return json.loads(result)
            except:
                return []
        return []

class AnthropicVisionAnalyzer(BaseVisionAnalyzer):
    """Anthropic Claude Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    
    def analyze_image(self, image_base64: str, prompt: str) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            import anthropic
            client = anthropic.Client(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_base64}}
                    ]
                }]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic Vision APIエラー: {e}", file=sys.stderr)
            return None
    
    def extract_elements(self, image_base64: str) -> List[Dict[str, Any]]:
        # OpenAIと同様の実装
        pass

class GoogleVisionAnalyzer(BaseVisionAnalyzer):
    """Google Cloud Vision API"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    def analyze_image(self, image_base64: str, prompt: str) -> Optional[str]:
        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            
            image = vision.Image(content=base64.b64decode(image_base64))
            
            # テキスト検出
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            # オブジェクト検出
            objects = client.object_localization(image=image).localized_object_annotations
            
            # Web検出（商品情報）
            web_detection = client.web_detection(image=image).web_detection
            
            # 結果を統合
            result = {
                "text": texts[0].description if texts else "",
                "objects": [{"name": obj.name, "score": obj.score} for obj in objects],
                "web_entities": [{"description": entity.description} for entity in web_detection.web_entities]
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            print(f"Google Vision APIエラー: {e}", file=sys.stderr)
            return None
    
    def extract_elements(self, image_base64: str) -> List[Dict[str, Any]]:
        # Google Vision特有の実装
        pass

class OCRAnalyzer:
    """Tesseract OCRによるテキスト抽出（フォールバック）"""
    
    def __init__(self):
        try:
            import pytesseract
            self.tesseract_available = True
        except ImportError:
            self.tesseract_available = False
    
    def extract_text(self, image_base64: str, lang='jpn+eng') -> str:
        if not self.tesseract_available:
            return ""
        
        try:
            import pytesseract
            from PIL import Image
            from io import BytesIO
            
            # Base64をPIL Imageに変換
            img = Image.open(BytesIO(base64.b64decode(image_base64)))
            
            # OCR実行
            text = pytesseract.image_to_string(img, lang=lang)
            
            # 価格パターンを抽出
            import re
            prices = re.findall(r'[¥￥]?\s*(\d{1,3}(?:,\d{3})*)', text)
            
            return {"text": text, "prices": prices}
            
        except Exception as e:
            print(f"OCRエラー: {e}", file=sys.stderr)
            return {"text": "", "prices": []}