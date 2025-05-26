#!/usr/bin/env python3
"""
Test script for visual web scraping
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.visual_scraper.mercari_visual_scraper import MercariVisualScraper
from src.visual_scraper.element_detector import VisualElementDetector
from src.collectors.mercari_visual import MercariVisualCollector
from src.utils.config import get_config

async def test_basic_visual_scraping():
    """Test basic visual scraping functionality"""
    print("\n=== Testing Basic Visual Scraping ===")
    
    openai_key = get_config("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        return
        
    scraper = MercariVisualScraper(openai_key)
    
    try:
        # Test searching for a simple item
        keyword = "Nintendo Switch"
        print(f"\nSearching for: {keyword}")
        
        items = await scraper.search_items(keyword, max_items=5)
        
        print(f"\nFound {len(items)} items:")
        for i, item in enumerate(items, 1):
            print(f"\n{i}. {item.get('title', 'No title')}")
            print(f"   Price: ¥{item.get('price', 0):,}")
            print(f"   URL: {item.get('url', 'No URL')}")
            print(f"   Condition: {item.get('condition', 'Unknown')}")
            print(f"   Sold: {item.get('sold', False)}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
async def test_element_detection():
    """Test visual element detection"""
    print("\n=== Testing Element Detection ===")
    
    openai_key = get_config("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        return
        
    scraper = MercariVisualScraper(openai_key)
    detector = VisualElementDetector()
    
    try:
        await scraper.initialize()
        await scraper.navigate_to("https://jp.mercari.com")
        
        # Take screenshot
        screenshot = await scraper.take_screenshot(full_page=False)
        
        # Detect various elements
        print("\nDetecting buttons...")
        buttons = detector.detect_buttons(screenshot)
        print(f"Found {len(buttons)} buttons")
        for btn in buttons[:3]:
            print(f"  - Button at ({btn['x']}, {btn['y']}): {btn.get('text', 'No text')}")
            
        print("\nDetecting input fields...")
        inputs = detector.detect_input_fields(screenshot)
        print(f"Found {len(inputs)} input fields")
        for inp in inputs[:3]:
            print(f"  - Input at ({inp['x']}, {inp['y']}): {inp.get('label', 'No label')} (type: {inp['type']})")
            
        print("\nDetecting prices...")
        prices = detector.detect_prices(screenshot)
        print(f"Found {len(prices)} prices")
        for price in prices[:3]:
            print(f"  - Price at ({price['x']}, {price['y']}): ¥{price['price']:,}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
        
async def test_visual_interaction():
    """Test visual interaction capabilities"""
    print("\n=== Testing Visual Interaction ===")
    
    openai_key = get_config("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        return
        
    scraper = MercariVisualScraper(openai_key)
    
    try:
        await scraper.initialize()
        await scraper.navigate_to("https://jp.mercari.com")
        
        # Try to find and interact with search box
        print("\nLooking for search box...")
        search_found = await scraper.type_in_field_visually(
            "search box or 検索 input field",
            "レコード"
        )
        
        if search_found:
            print("✓ Successfully typed in search box")
            
            # Try to click search button
            print("\nLooking for search button...")
            button_clicked = await scraper.click_element_visually(
                "search button or magnifying glass icon or 検索 button"
            )
            
            if button_clicked:
                print("✓ Successfully clicked search button")
                
                # Wait for results
                await scraper.wait_for_visual_change(timeout=5)
                
                # Extract results
                print("\nExtracting search results...")
                results = await scraper.extract_data_visually(
                    "product listings with titles and prices"
                )
                
                print(f"Found {len(results)} results")
                for i, result in enumerate(results[:3], 1):
                    print(f"\n{i}. {result}")
            else:
                print("✗ Could not find search button")
        else:
            print("✗ Could not find search box")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
        
async def test_pagination():
    """Test pagination capabilities"""
    print("\n=== Testing Pagination ===")
    
    openai_key = get_config("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set in environment")
        return
        
    scraper = MercariVisualScraper(openai_key)
    
    try:
        # Test pagination
        keyword = "vintage record"
        print(f"\nSearching for '{keyword}' across multiple pages...")
        
        all_items = await scraper.extract_with_pagination(
            keyword, 
            max_pages=2, 
            items_per_page=10
        )
        
        print(f"\nTotal items found: {len(all_items)}")
        
        # Group by page (approximate)
        for i in range(0, len(all_items), 10):
            page_num = i // 10 + 1
            page_items = all_items[i:i+10]
            print(f"\nPage {page_num}: {len(page_items)} items")
            for j, item in enumerate(page_items[:3], 1):
                print(f"  {j}. {item.get('title', 'No title')} - ¥{item.get('price', 0):,}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
def test_collector_integration():
    """Test the collector integration"""
    print("\n=== Testing Collector Integration ===")
    
    try:
        collector = MercariVisualCollector()
        
        # Test search
        keyword = "Beatles LP"
        print(f"\nSearching for: {keyword}")
        
        items = collector.search_items(keyword, limit=5)
        
        print(f"\nFound {len(items)} items:")
        for item in items:
            print(f"\n- {item['title']}")
            print(f"  Price: ¥{item['price']:,}")
            print(f"  Status: {item['status']}")
            print(f"  ID: {item['item_id']}")
            print(f"  Method: {item['scraping_method']}")
            
        # Save results
        output_file = f"visual_scraping_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'keyword': keyword,
                'items': items
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
def test_comparison():
    """Test comparison between visual and traditional scraping"""
    print("\n=== Testing Visual vs Traditional Comparison ===")
    
    try:
        collector = MercariVisualCollector()
        
        keyword = "Nintendo Switch"
        print(f"\nComparing results for: {keyword}")
        
        comparison = collector.compare_with_traditional(keyword)
        
        print(f"\nVisual scraping: {comparison['visual_count']} items")
        print(f"Traditional scraping: {comparison['traditional_count']} items")
        print(f"Common items: {len(comparison['common_items'])}")
        print(f"Visual-only items: {len(comparison['visual_only_items'])}")
        print(f"Traditional-only items: {len(comparison['traditional_only_items'])}")
        
        if comparison['visual_only_items']:
            print("\nItems found only by visual scraping:")
            for item in comparison['visual_only_items'][:3]:
                print(f"  - {item['title']} (¥{item['price']:,})")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("="*60)
    print("AI-Powered Visual Web Scraping Test Suite")
    print("="*60)
    
    # Check for required API key
    if not get_config("OPENAI_API_KEY"):
        print("\nERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        return
        
    # Run tests
    await test_basic_visual_scraping()
    await test_element_detection()
    await test_visual_interaction()
    await test_pagination()
    
    # Run sync tests
    test_collector_integration()
    test_comparison()
    
    print("\n" + "="*60)
    print("Test suite completed!")
    print("="*60)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())