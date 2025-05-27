"""
画像処理ユーティリティ
OCRとOpenAI Vision APIを使用した商品情報抽出
"""

import base64
import json
import re
from typing import Dict, Optional, List, Any
from PIL import Image
import pytesseract
import cv2
import numpy as np
from openai import OpenAI
import os

class ImageProcessor:
    """画像から商品情報を抽出するプロセッサー"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        画像を処理して商品情報を抽出
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            抽出された商品情報
        """
        # 画像を読み込み
        image = cv2.imread(image_path)
        
        # OCRでテキスト抽出
        ocr_result = self._extract_text_ocr(image)
        
        # OpenAI Vision APIで商品認識
        vision_result = self._analyze_with_vision_api(image_path)
        
        # 結果を統合
        return self._merge_results(ocr_result, vision_result)
    
    def _extract_text_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """OCRでテキストを抽出"""
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # ノイズ除去
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 二値化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # OCR実行
        text = pytesseract.image_to_string(binary, lang='jpn+eng')
        
        # JANコードを抽出
        jan_codes = self._extract_jan_codes(text)
        
        # 商品名候補を抽出
        product_names = self._extract_product_names(text)
        
        return {
            'full_text': text,
            'jan_codes': jan_codes,
            'product_names': product_names
        }
    
    def _extract_jan_codes(self, text: str) -> List[str]:
        """テキストからJANコードを抽出"""
        # JANコードパターン（13桁または8桁）
        jan_pattern = r'\b(?:\d{13}|\d{8})\b'
        potential_jans = re.findall(jan_pattern, text)
        
        # チェックディジットで検証
        valid_jans = []
        for jan in potential_jans:
            if self._validate_jan_code(jan):
                valid_jans.append(jan)
        
        return valid_jans
    
    def _validate_jan_code(self, code: str) -> bool:
        """JANコードのチェックディジット検証"""
        if len(code) not in [8, 13]:
            return False
        
        try:
            digits = [int(d) for d in code[:-1]]
            check_digit = int(code[-1])
            
            if len(code) == 13:
                # 奇数桁と偶数桁で計算
                odd_sum = sum(digits[i] for i in range(0, len(digits), 2))
                even_sum = sum(digits[i] for i in range(1, len(digits), 2))
                total = odd_sum + even_sum * 3
            else:  # 8桁
                odd_sum = sum(digits[i] for i in range(1, len(digits), 2))
                even_sum = sum(digits[i] for i in range(0, len(digits), 2))
                total = odd_sum * 3 + even_sum
            
            calculated_check = (10 - (total % 10)) % 10
            return calculated_check == check_digit
            
        except (ValueError, IndexError):
            return False
    
    def _extract_product_names(self, text: str) -> List[str]:
        """テキストから商品名候補を抽出"""
        lines = text.strip().split('\n')
        product_candidates = []
        
        # 商品名らしい行を抽出（長さとパターンで判定）
        for line in lines:
            line = line.strip()
            if 5 <= len(line) <= 100:
                # 数字だけの行は除外
                if not re.match(r'^\d+$', line):
                    # 価格表記は除外
                    if not re.search(r'[¥￥]\s*\d+|^\d+円', line):
                        product_candidates.append(line)
        
        return product_candidates[:5]  # 上位5件
    
    def _analyze_with_vision_api(self, image_path: str) -> Dict[str, Any]:
        """OpenAI Vision APIで画像を解析"""
        # 画像をBase64エンコード
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは商品画像から情報を抽出する専門家です。JANコード、商品名、ブランド、カテゴリなどを正確に識別してください。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "この画像から以下の情報を抽出してJSON形式で返してください：\n1. JANコード（バーコードが見える場合）\n2. 商品名\n3. ブランド名\n4. カテゴリ（音楽CD、ゲーム、本など）\n5. その他の識別可能な情報"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # レスポンスからJSON部分を抽出
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'error': 'JSON extraction failed', 'raw_response': content}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _merge_results(self, ocr_result: Dict, vision_result: Dict) -> Dict[str, Any]:
        """OCRとVision APIの結果を統合"""
        merged = {
            'jan_codes': [],
            'product_name': None,
            'brand': None,
            'category': None,
            'confidence': 0.0,
            'raw_ocr_text': ocr_result.get('full_text', ''),
            'sources': []
        }
        
        # JANコードの統合
        jan_codes = set(ocr_result.get('jan_codes', []))
        if 'jan_code' in vision_result:
            jan_codes.add(vision_result['jan_code'])
        merged['jan_codes'] = list(jan_codes)
        
        # 商品名の決定
        if vision_result.get('product_name'):
            merged['product_name'] = vision_result['product_name']
            merged['sources'].append('vision_api')
        elif ocr_result.get('product_names'):
            merged['product_name'] = ocr_result['product_names'][0]
            merged['sources'].append('ocr')
        
        # その他の情報
        merged['brand'] = vision_result.get('brand')
        merged['category'] = vision_result.get('category')
        
        # 信頼度の計算
        if merged['jan_codes']:
            merged['confidence'] += 0.5
        if merged['product_name']:
            merged['confidence'] += 0.3
        if merged['brand']:
            merged['confidence'] += 0.2
        
        return merged