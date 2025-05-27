#!/usr/bin/env python3
"""
画像検索処理スクリプト
画像から商品情報を抽出してJSON形式で出力
"""

import sys
import json
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.image_processor import ImageProcessor

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No image path provided'}))
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(json.dumps({'error': f'Image file not found: {image_path}'}))
        sys.exit(1)
    
    try:
        # 画像処理を実行
        processor = ImageProcessor()
        result = processor.process_image(image_path)
        
        # 結果をJSON形式で出力
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'type': type(e).__name__
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()