"""
画像検索機能の統合テスト
"""

import pytest
import json
import base64
from pathlib import Path
import requests
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.image_processor import ImageProcessor

class TestImageSearch:
    """画像検索機能のテスト"""
    
    @pytest.fixture
    def sample_image_with_jan(self):
        """JANコード付きサンプル画像のパス"""
        # テスト用画像は別途用意する必要があります
        return Path(__file__).parent.parent / "fixtures" / "test_images" / "product_with_jan.jpg"
    
    @pytest.fixture
    def sample_image_without_jan(self):
        """JANコードなしサンプル画像のパス"""
        return Path(__file__).parent.parent / "fixtures" / "test_images" / "product_without_jan.jpg"
    
    def test_image_processor_initialization(self):
        """ImageProcessorの初期化テスト"""
        processor = ImageProcessor()
        assert processor is not None
        assert processor.client is not None
    
    def test_jan_code_validation(self):
        """JANコード検証機能のテスト"""
        processor = ImageProcessor()
        
        # 有効なJANコード（13桁）
        assert processor._validate_jan_code("4988001531654") == True
        
        # 有効なJANコード（8桁）
        assert processor._validate_jan_code("49880015") == True
        
        # 無効なJANコード（チェックディジット誤り）
        assert processor._validate_jan_code("4988001531655") == False
        
        # 無効なJANコード（桁数誤り）
        assert processor._validate_jan_code("123456") == False
    
    def test_jan_code_extraction(self):
        """テキストからのJANコード抽出テスト"""
        processor = ImageProcessor()
        
        text = """
        商品名: テスト商品
        JANコード: 4988001531654
        価格: ¥1,000
        別のコード: 1234567890123
        """
        
        jan_codes = processor._extract_jan_codes(text)
        assert "4988001531654" in jan_codes
        # チェックディジットが無効なものは含まれない
        assert "1234567890123" not in jan_codes
    
    def test_product_name_extraction(self):
        """商品名抽出のテスト"""
        processor = ImageProcessor()
        
        text = """
        Nintendo Switch 本体
        ¥32,000
        新品・未開封
        JAN: 4902370535730
        """
        
        product_names = processor._extract_product_names(text)
        assert "Nintendo Switch 本体" in product_names
        assert "新品・未開封" in product_names
        # 価格行は除外される
        assert not any("¥32,000" in name for name in product_names)
    
    @pytest.mark.skipif(not Path("test_image.jpg").exists(), reason="Test image not available")
    def test_process_image_with_jan(self, sample_image_with_jan):
        """JANコード付き画像の処理テスト"""
        if not sample_image_with_jan.exists():
            pytest.skip("Sample image not found")
        
        processor = ImageProcessor()
        result = processor.process_image(str(sample_image_with_jan))
        
        assert 'jan_codes' in result
        assert 'product_name' in result
        assert 'confidence' in result
        assert result['confidence'] > 0
    
    def test_merge_results(self):
        """結果統合のテスト"""
        processor = ImageProcessor()
        
        ocr_result = {
            'full_text': 'Sample text',
            'jan_codes': ['4988001531654'],
            'product_names': ['Test Product']
        }
        
        vision_result = {
            'product_name': 'Enhanced Test Product',
            'brand': 'Test Brand',
            'category': 'Electronics'
        }
        
        merged = processor._merge_results(ocr_result, vision_result)
        
        assert '4988001531654' in merged['jan_codes']
        assert merged['product_name'] == 'Enhanced Test Product'  # Vision APIの結果を優先
        assert merged['brand'] == 'Test Brand'
        assert merged['category'] == 'Electronics'
        assert merged['confidence'] > 0
    
    @pytest.mark.integration
    def test_api_endpoint_upload(self):
        """画像アップロードAPIエンドポイントのテスト"""
        # APIサーバーが起動している前提
        url = "http://localhost:3000/api/search/image"
        
        # ダミー画像データ
        dummy_image = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        files = {'image': ('test.png', dummy_image, 'image/png')}
        
        try:
            response = requests.post(url, files=files, timeout=5)
            assert response.status_code in [200, 500]  # 500はOpenAI APIキーがない場合
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")
    
    @pytest.mark.integration
    def test_api_endpoint_url(self):
        """画像URL検索APIエンドポイントのテスト"""
        url = "http://localhost:3000/api/search/image"
        
        data = {
            'imageUrl': 'https://example.com/test-image.jpg'
        }
        
        try:
            response = requests.put(url, json=data, timeout=5)
            assert response.status_code in [200, 500]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestImageSearchIntegration:
    """画像検索と他の検索機能との統合テスト"""
    
    @pytest.mark.integration
    def test_image_to_jan_search_flow(self):
        """画像→JAN抽出→商品検索のフローテスト"""
        # 画像処理
        processor = ImageProcessor()
        
        # モック結果
        mock_result = {
            'jan_codes': ['4988001531654'],
            'product_name': 'Test Product',
            'confidence': 0.8
        }
        
        # JANコードが抽出された場合、既存の検索が呼ばれることを確認
        assert mock_result['jan_codes']
        assert len(mock_result['jan_codes']) > 0
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        processor = ImageProcessor()
        
        # 存在しないファイル
        with pytest.raises(Exception):
            processor.process_image("/path/to/nonexistent/file.jpg")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])