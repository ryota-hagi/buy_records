"""
Mercari collector using visual AI scraping
"""

import asyncio
from typing import List, Dict, Any
from ..visual_scraper.mercari_visual_scraper import MercariVisualScraper
from ..utils.config import get_config
import os
import logging

logger = logging.getLogger(__name__)

class MercariVisualCollector:
    """Mercari collector using visual AI scraping"""
    
    def __init__(self):
        self.openai_api_key = get_config("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
            
    async def search_items_async(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for items using visual scraping (async)"""
        scraper = MercariVisualScraper(self.openai_api_key)
        
        try:
            # Get items using visual scraping
            items = await scraper.search_items(keyword, limit)
            
            # Transform to match existing data format
            transformed_items = []
            for item in items:
                transformed_items.append({
                    'search_term': keyword,
                    'item_id': self._extract_item_id(item.get('url', '')),
                    'title': item.get('title', ''),
                    'price': item.get('price', 0),
                    'currency': 'JPY',
                    'status': 'sold' if item.get('sold', False) else 'active',
                    'condition': item.get('condition', ''),
                    'url': item.get('url', ''),
                    'image_url': item.get('image_url', ''),
                    'seller': item.get('seller', ''),
                    'description': item.get('description', ''),
                    'platform': 'mercari',
                    'scraping_method': 'visual_ai',
                    'category': item.get('category', ''),
                    'brand': item.get('brand', ''),
                    'size': item.get('size', ''),
                    'color': item.get('color', ''),
                    'shipping_method': item.get('shipping_method', ''),
                    'shipping_cost': item.get('shipping_cost', ''),
                    'location': item.get('location', '')
                })
                
            return transformed_items
            
        except Exception as e:
            logger.error(f"Error in visual scraping: {e}")
            return []
            
    def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for items using visual scraping (sync wrapper)"""
        return asyncio.run(self.search_items_async(keyword, limit))
        
    def _extract_item_id(self, url: str) -> str:
        """Extract item ID from URL"""
        if '/item/' in url:
            return url.split('/item/')[-1].split('?')[0]
        return ''
        
    def get_complete_data(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get complete data synchronously (wrapper for async method)"""
        return self.search_items(keyword, limit)
        
    async def search_sold_items_async(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for sold items using visual scraping"""
        scraper = MercariVisualScraper(self.openai_api_key)
        
        try:
            await scraper.initialize()
            
            # Navigate to sold items search
            search_url = f"{scraper.base_url}/search?keyword={keyword}&status=sold_out"
            await scraper.navigate_to(search_url)
            
            # Extract sold items
            items = await scraper._extract_search_results(limit)
            
            # Transform items
            transformed_items = []
            for item in items:
                if item.get('sold', False):  # Ensure it's actually sold
                    transformed_items.append({
                        'search_term': keyword,
                        'item_id': self._extract_item_id(item.get('url', '')),
                        'title': item.get('title', ''),
                        'price': item.get('price', 0),
                        'currency': 'JPY',
                        'status': 'sold',
                        'condition': item.get('condition', ''),
                        'url': item.get('url', ''),
                        'image_url': item.get('image_url', ''),
                        'seller': item.get('seller', ''),
                        'platform': 'mercari',
                        'scraping_method': 'visual_ai'
                    })
                    
            return transformed_items
            
        except Exception as e:
            logger.error(f"Error searching sold items: {e}")
            return []
        finally:
            await scraper.close()
            
    def search_sold_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for sold items (sync wrapper)"""
        return asyncio.run(self.search_sold_items_async(keyword, limit))
        
    async def monitor_item_async(self, item_url: str, check_interval: int = 3600):
        """Monitor an item for changes"""
        scraper = MercariVisualScraper(self.openai_api_key)
        
        async for change in scraper.monitor_price_changes(item_url, check_interval):
            yield change
            
    def compare_with_traditional(self, keyword: str) -> Dict[str, Any]:
        """Compare visual scraping results with traditional scraping"""
        # Get results from visual scraping
        visual_results = self.search_items(keyword, limit=10)
        
        # Get results from traditional scraping (if available)
        traditional_results = []
        try:
            from .mercari import MercariClient
            traditional_client = MercariClient()
            traditional_results = traditional_client.search_active_items(keyword, limit=10)
        except Exception as e:
            logger.error(f"Could not get traditional results: {e}")
            
        # Compare results
        comparison = {
            'visual_count': len(visual_results),
            'traditional_count': len(traditional_results),
            'visual_items': visual_results,
            'traditional_items': traditional_results,
            'visual_only_items': [],
            'traditional_only_items': [],
            'common_items': []
        }
        
        # Find differences
        visual_ids = {item['item_id'] for item in visual_results if item['item_id']}
        traditional_ids = {item['item_id'] for item in traditional_results if item['item_id']}
        
        common_ids = visual_ids & traditional_ids
        visual_only_ids = visual_ids - traditional_ids
        traditional_only_ids = traditional_ids - visual_ids
        
        comparison['common_items'] = [item for item in visual_results if item['item_id'] in common_ids]
        comparison['visual_only_items'] = [item for item in visual_results if item['item_id'] in visual_only_ids]
        comparison['traditional_only_items'] = [item for item in traditional_results if item['item_id'] in traditional_only_ids]
        
        return comparison