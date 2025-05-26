#!/usr/bin/env python3
"""
最適化されたMercari視覚スクレイピング
- GPT-4o-miniを使用（最も安価）
- Context7との連携を考慮
- 画像サイズ最適化
"""
import sys
import json
import os
import time
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import base64

# .envファイルを読み込む
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.visual_scraper.mercari_visual_scraper import MercariVisualScraper
from src.visual_scraper.ai_analyzer import OpenAIVisionAnalyzer

class OptimizedMercariScraper(MercariVisualScraper):
    """最適化されたMercariスクレイパー"""
    
    def __init__(self, ai_analyzer=None, headless=True, save_screenshots=True):
        super().__init__(ai_analyzer, headless, save_screenshots)
        self.cost_tracker = {
            'screenshots': 0,
            'api_calls': 0,
            'estimated_cost': 0.0
        }
    
    def take_screenshot(self, name=None):
        """スクリーンショットを撮影し、サイズを最適化"""
        screenshot_base64 = super().take_screenshot(name)
        
        if screenshot_base64:
            # 画像を最適化（サイズ削減）
            img_data = base64.b64decode(screenshot_base64)
            img = Image.open(BytesIO(img_data))
            
            # 画像を512x512以下にリサイズ（低解像度モード用）
            max_size = (512, 512)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 品質を調整してサイズを削減
            buffered = BytesIO()
            img.save(buffered, format="PNG", optimize=True)
            optimized_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # コスト追跡
            self.cost_tracker['screenshots'] += 1
            self.cost_tracker['estimated_cost'] += 0.001  # 約$0.001/画像
            
            print(f"スクリーンショット最適化: {len(screenshot_base64)} → {len(optimized_base64)} bytes", file=sys.stderr)
            
            return optimized_base64
        
        return None
    
    def extract_product_prompt(self):
        """最適化されたプロンプト（トークン数削減）"""
        return """メルカリ検索結果から商品を抽出。JSON形式で返す:
{
  "products": [
    {
      "title": "商品名",
      "price": "価格(数値のみ)",
      "sold": false,
      "x": 100,
      "y": 200
    }
  ],
  "has_next": true
}
注意:価格は数値のみ、売切除外、最大20件"""

def search_with_cost_tracking(query, limit=20):
    """コスト追跡付きで検索を実行"""
    start_time = time.time()
    
    # OpenAI Vision APIを初期化
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("警告: OpenAI APIキーが設定されていません", file=sys.stderr)
        ai_analyzer = None
    else:
        ai_analyzer = OpenAIVisionAnalyzer(api_key=api_key)
        print("OpenAI Vision API (GPT-4o-mini) を使用します", file=sys.stderr)
    
    # 最適化されたスクレイパーを使用
    scraper = OptimizedMercariScraper(
        ai_analyzer=ai_analyzer,
        headless=True,
        save_screenshots=True
    )
    
    # 検索を実行
    results = scraper.search(query, limit)
    
    # 実行時間とコストを計算
    execution_time = time.time() - start_time
    
    # Context7用のメタデータを追加
    metadata = {
        'execution_time': execution_time,
        'cost_tracking': scraper.cost_tracker,
        'model_used': 'gpt-4o-mini',
        'optimization': 'low_resolution',
        'context7_compatible': True
    }
    
    return results, metadata

def main():
    if len(sys.argv) < 2:
        print("Usage: search_mercari_visual_optimized.py <query> [limit]", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print("JSON_START")
    
    try:
        results, metadata = search_with_cost_tracking(query, limit)
        
        output = {
            'success': len(results) > 0,
            'results': results,
            'platform': 'mercari',
            'query': query,
            'method': 'visual_ai_optimized',
            'metadata': metadata
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
        # コストサマリーを表示
        print(f"\n=== コストサマリー ===", file=sys.stderr)
        print(f"スクリーンショット: {metadata['cost_tracking']['screenshots']}枚", file=sys.stderr)
        print(f"推定コスト: ${metadata['cost_tracking']['estimated_cost']:.4f}", file=sys.stderr)
        print(f"実行時間: {metadata['execution_time']:.2f}秒", file=sys.stderr)
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        error_output = {
            'success': False,
            'results': [],
            'error': str(e),
            'platform': 'mercari',
            'method': 'visual_ai_optimized'
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
    
    print("JSON_END")

if __name__ == "__main__":
    main()