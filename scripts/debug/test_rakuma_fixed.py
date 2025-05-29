#!/usr/bin/env python3
"""
修正されたラクマスクレイパーのテスト
"""
import os
import sys
import json

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.collectors.rakuma_selenium import RakumaSeleniumScraper

def test_rakuma_scraper():
    """修正されたラクマスクレイパーをテスト"""
    print("=== Testing Fixed Rakuma Scraper ===\n")
    
    # スクレイパーインスタンス作成
    scraper = RakumaSeleniumScraper()
    
    # テスト検索
    test_keywords = [
        "Nintendo Switch",
        "PS5",
        "iPhone 15"
    ]
    
    all_results = {}
    
    for keyword in test_keywords:
        print(f"\n📍 Testing search for: {keyword}")
        
        try:
            # 検索実行
            results = scraper.search(keyword)
            
            if results:
                print(f"✅ Found {len(results)} items")
                
                # 最初の3件を表示
                for i, item in enumerate(results[:3]):
                    print(f"\n  Item {i+1}:")
                    print(f"    Title: {item.get('title', 'N/A')}")
                    print(f"    Price: ¥{item.get('price', 0):,}")
                    print(f"    URL: {item.get('url', 'N/A')[:80]}...")
                    
                all_results[keyword] = results
            else:
                print("❌ No items found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # 結果を保存
    if all_results:
        with open('rakuma_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print("\n✅ Test results saved to rakuma_test_results.json")
        
        # 統計情報
        print("\n📊 Summary:")
        for keyword, results in all_results.items():
            if results:
                prices = [item.get('price', 0) for item in results if item.get('price', 0) > 0]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    print(f"  {keyword}: {len(results)} items, avg price: ¥{avg_price:,.0f}")
    
    return len(all_results) > 0

if __name__ == "__main__":
    # スクレイパーテスト
    success = test_rakuma_scraper()
    
    if success:
        print("\n✅ Rakuma scraper is working correctly!")
    else:
        print("\n❌ Rakuma scraper needs further fixes")
        print("\nRecommended actions:")
        print("1. Check if Selenium server is running")
        print("2. Review error messages above")
        print("3. Check network connectivity")