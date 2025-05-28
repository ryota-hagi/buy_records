#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.translator import translate_for_platform

def main():
    if len(sys.argv) < 2:
        print("Usage: python translate_for_ebay.py <product_name>", file=sys.stderr)
        sys.exit(1)
    
    product_name = sys.argv[1]
    
    try:
        translated = translate_for_platform(product_name, 'ebay')
        print(translated)
    except Exception as e:
        print(f"Translation error: {str(e)}", file=sys.stderr)
        print(product_name)  # 翻訳失敗時は元のテキストを出力

if __name__ == "__main__":
    main()
