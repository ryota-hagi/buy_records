#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.exchange_rate import get_usd_to_jpy_rate

def main():
    try:
        rate = get_usd_to_jpy_rate()
        print(rate)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        print(150)  # フォールバックレート

if __name__ == "__main__":
    main()
