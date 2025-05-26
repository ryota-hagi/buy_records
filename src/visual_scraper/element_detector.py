"""
コンピュータビジョンを使用した要素検出
"""
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import base64
from typing import List, Dict, Tuple, Optional

class VisualElementDetector:
    """画像から視覚的に要素を検出"""
    
    def __init__(self):
        self.min_contour_area = 1000  # 最小領域サイズ
    
    def base64_to_cv2(self, base64_string: str) -> np.ndarray:
        """Base64をOpenCV画像に変換"""
        img_data = base64.b64decode(base64_string)
        img = Image.open(BytesIO(img_data))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def detect_rectangles(self, image: np.ndarray) -> List[Dict[str, int]]:
        """矩形領域（商品カードなど）を検出"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                x, y, w, h = cv2.boundingRect(contour)
                rectangles.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area)
                })
        
        return sorted(rectangles, key=lambda r: r['area'], reverse=True)
    
    def detect_buttons(self, image: np.ndarray) -> List[Dict[str, any]]:
        """ボタンらしい要素を検出"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 一般的なボタンの色範囲
        button_colors = [
            # 青系ボタン
            {'lower': np.array([100, 50, 50]), 'upper': np.array([130, 255, 255]), 'name': 'blue'},
            # 緑系ボタン
            {'lower': np.array([40, 50, 50]), 'upper': np.array([80, 255, 255]), 'name': 'green'},
            # 赤系ボタン
            {'lower': np.array([0, 50, 50]), 'upper': np.array([10, 255, 255]), 'name': 'red'},
            # オレンジ系ボタン
            {'lower': np.array([10, 50, 50]), 'upper': np.array([25, 255, 255]), 'name': 'orange'},
        ]
        
        buttons = []
        for color in button_colors:
            mask = cv2.inRange(hsv, color['lower'], color['upper'])
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # ボタンの最小サイズ
                    x, y, w, h = cv2.boundingRect(contour)
                    # アスペクト比でボタンらしさを判定
                    aspect_ratio = w / h
                    if 1.5 < aspect_ratio < 6:  # 横長の形状
                        buttons.append({
                            'x': int(x),
                            'y': int(y),
                            'width': int(w),
                            'height': int(h),
                            'color': color['name'],
                            'confidence': min(area / 5000, 1.0)  # 信頼度
                        })
        
        return buttons
    
    def detect_price_regions(self, image: np.ndarray) -> List[Dict[str, any]]:
        """価格表示領域を検出（円マークや数字のパターン）"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # テンプレートマッチング（円マーク）
        # 実際の実装では円マークのテンプレート画像が必要
        price_regions = []
        
        # 数字が含まれそうな領域を検出
        # 閾値処理
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # 輪郭検出
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 価格表示のサイズ特性
            if 50 < w < 300 and 20 < h < 80:
                roi = gray[y:y+h, x:x+w]
                # 領域内のテキストらしさを評価（簡易版）
                text_score = np.std(roi) / np.mean(roi) if np.mean(roi) > 0 else 0
                
                if text_score > 0.3:
                    price_regions.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'confidence': float(text_score)
                    })
        
        return price_regions
    
    def detect_product_cards(self, image: np.ndarray) -> List[Dict[str, any]]:
        """商品カードを検出（画像+テキストの組み合わせ）"""
        rectangles = self.detect_rectangles(image)
        
        product_cards = []
        for rect in rectangles:
            # 矩形のアスペクト比で商品カードらしさを判定
            aspect_ratio = rect['width'] / rect['height']
            
            # 一般的な商品カードのアスペクト比
            if 0.7 < aspect_ratio < 1.5:
                # 領域内に画像とテキストが含まれているかチェック
                x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
                roi = image[y:y+h, x:x+w]
                
                # エッジ密度で画像の存在を推定
                edges = cv2.Canny(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 50, 150)
                edge_density = np.sum(edges > 0) / (w * h)
                
                if edge_density > 0.05:  # 適度なエッジがある
                    product_cards.append({
                        'bounds': rect,
                        'confidence': min(edge_density * 10, 1.0),
                        'type': 'product_card'
                    })
        
        return product_cards
    
    def detect_clickable_areas(self, base64_image: str) -> Dict[str, List[Dict[str, any]]]:
        """クリック可能な領域をすべて検出"""
        image = self.base64_to_cv2(base64_image)
        
        return {
            'product_cards': self.detect_product_cards(image),
            'buttons': self.detect_buttons(image),
            'price_regions': self.detect_price_regions(image),
            'rectangles': self.detect_rectangles(image)[:20]  # 上位20個
        }
    
    def highlight_elements(self, base64_image: str, elements: Dict[str, List[Dict[str, any]]]) -> str:
        """検出した要素をハイライトした画像を返す（デバッグ用）"""
        image = self.base64_to_cv2(base64_image)
        
        # 商品カードを赤で囲む
        for card in elements.get('product_cards', []):
            bounds = card['bounds']
            cv2.rectangle(image, 
                         (bounds['x'], bounds['y']), 
                         (bounds['x'] + bounds['width'], bounds['y'] + bounds['height']),
                         (0, 0, 255), 2)
        
        # ボタンを緑で囲む
        for button in elements.get('buttons', []):
            cv2.rectangle(image,
                         (button['x'], button['y']),
                         (button['x'] + button['width'], button['y'] + button['height']),
                         (0, 255, 0), 2)
        
        # 価格領域を青で囲む
        for price in elements.get('price_regions', []):
            cv2.rectangle(image,
                         (price['x'], price['y']),
                         (price['x'] + price['width'], price['y'] + price['height']),
                         (255, 0, 0), 2)
        
        # OpenCV画像をBase64に変換
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')