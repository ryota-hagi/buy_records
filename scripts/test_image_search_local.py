#!/usr/bin/env python3
"""
画像検索機能のローカルテストスクリプト
実際の画像ファイルでテスト可能
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.image_processor import ImageProcessor

def test_with_local_image(image_path: str):
    """ローカル画像でテスト"""
    print(f"Testing with image: {image_path}")
    
    processor = ImageProcessor()
    
    try:
        result = processor.process_image(image_path)
        
        print("\n=== 抽出結果 ===")
        print(f"JANコード: {result.get('jan_codes', [])}")
        print(f"商品名: {result.get('product_name', 'N/A')}")
        print(f"ブランド: {result.get('brand', 'N/A')}")
        print(f"カテゴリ: {result.get('category', 'N/A')}")
        print(f"信頼度: {result.get('confidence', 0):.2f}")
        print(f"情報ソース: {', '.join(result.get('sources', []))}")
        
        if result.get('jan_codes'):
            print(f"\n✅ JANコードが見つかりました。商品検索が可能です。")
        elif result.get('product_name'):
            print(f"\n⚠️  JANコードは見つかりませんでしたが、商品名で検索可能です。")
        else:
            print(f"\n❌ 商品情報を抽出できませんでした。")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python test_image_search_local.py <画像ファイルパス>")
        print("例: python test_image_search_local.py /path/to/product.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"エラー: 画像ファイルが見つかりません: {image_path}")
        sys.exit(1)
    
    test_with_local_image(image_path)

if __name__ == '__main__':
    main()