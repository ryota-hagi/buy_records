# AI-Powered Visual Web Scraping System Implementation Plan

## Overview

This document outlines a comprehensive implementation plan for an AI-powered visual web scraping system that uses computer vision and AI models to analyze screenshots and interact with web pages visually, rather than relying on traditional DOM-based scraping.

## System Architecture

### Core Components

1. **Screenshot Capture Engine**
   - Headless browser automation (Playwright/Puppeteer)
   - Full page screenshot capabilities
   - Viewport management
   - Dynamic content waiting strategies

2. **Vision AI Analysis Module**
   - OpenAI Vision API integration
   - Google Cloud Vision API integration
   - Local vision models (YOLO, OCR)
   - Custom trained models for specific elements

3. **Element Detection & Interaction**
   - Visual element detection
   - Coordinate mapping
   - Click simulation
   - Form filling via visual recognition

4. **Data Extraction Pipeline**
   - Visual text extraction (OCR)
   - Structured data parsing
   - Image analysis for product details
   - Price and metadata extraction

5. **Orchestration Layer**
   - Task queue management
   - Retry logic with visual verification
   - State management
   - Error handling and recovery

## Required Tools and Libraries

### Python Dependencies
```python
# Core Web Automation
playwright>=1.40.0
selenium>=4.15.0
undetected-chromedriver>=3.5.0

# Computer Vision & AI
opencv-python>=4.8.0
pytesseract>=0.3.10
pillow>=10.0.0
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.35.0

# AI/ML APIs
openai>=1.0.0
google-cloud-vision>=3.4.0
anthropic>=0.7.0

# Image Processing
scikit-image>=0.22.0
numpy>=1.24.0
matplotlib>=3.7.0

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
aiohttp>=3.9.0
```

### JavaScript/Node.js Dependencies
```json
{
  "dependencies": {
    "puppeteer": "^21.5.0",
    "playwright": "^1.40.0",
    "@google-cloud/vision": "^4.0.0",
    "tesseract.js": "^5.0.0",
    "sharp": "^0.33.0",
    "openai": "^4.20.0"
  }
}
```

## Implementation Examples

### 1. Base Visual Scraper Class

```python
# src/visual_scraper/base_scraper.py
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser
import cv2
import numpy as np
from PIL import Image
import io
import base64
from openai import OpenAI
import json

class VisualWebScraper:
    """Base class for AI-powered visual web scraping"""
    
    def __init__(self, openai_api_key: str, headless: bool = True):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize(self):
        """Initialize the browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security'
            ]
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        
    async def navigate_to(self, url: str):
        """Navigate to a URL and wait for content"""
        await self.page.goto(url, wait_until='networkidle')
        await self.page.wait_for_timeout(3000)  # Wait for dynamic content
        
    async def take_screenshot(self, full_page: bool = True) -> bytes:
        """Take a screenshot of the current page"""
        screenshot = await self.page.screenshot(full_page=full_page)
        return screenshot
        
    async def analyze_screenshot_with_ai(self, screenshot: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze screenshot using OpenAI Vision API"""
        # Convert screenshot to base64
        base64_image = base64.b64encode(screenshot).decode('utf-8')
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            # Try to parse as JSON if the response is structured
            return json.loads(content)
        except:
            return {"raw_response": content}
            
    async def find_element_visually(self, description: str) -> Optional[Tuple[int, int]]:
        """Find an element on the page using visual description"""
        screenshot = await self.take_screenshot(full_page=False)
        
        prompt = f"""
        Analyze this screenshot and find the element matching this description: "{description}"
        
        Return the response in this exact JSON format:
        {{
            "found": true/false,
            "x": center_x_coordinate,
            "y": center_y_coordinate,
            "confidence": 0-100,
            "description": "brief description of what was found"
        }}
        
        If not found, set found to false and explain why.
        """
        
        result = await self.analyze_screenshot_with_ai(screenshot, prompt)
        
        if result.get("found", False):
            return (result["x"], result["y"])
        return None
        
    async def click_element_visually(self, description: str) -> bool:
        """Click an element identified visually"""
        coords = await self.find_element_visually(description)
        if coords:
            await self.page.mouse.click(coords[0], coords[1])
            await self.page.wait_for_timeout(1000)
            return True
        return False
        
    async def extract_data_visually(self, data_description: str) -> List[Dict[str, Any]]:
        """Extract structured data from the page visually"""
        screenshot = await self.take_screenshot()
        
        prompt = f"""
        Analyze this screenshot and extract the following data: {data_description}
        
        Return the data as a JSON array where each item contains relevant fields.
        Be as accurate as possible and include all visible information.
        """
        
        result = await self.analyze_screenshot_with_ai(screenshot, prompt)
        return result if isinstance(result, list) else []
        
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
```

### 2. Mercari Visual Scraper Implementation

```python
# src/visual_scraper/mercari_visual_scraper.py
from typing import List, Dict, Any, Optional
import asyncio
from .base_scraper import VisualWebScraper
import json

class MercariVisualScraper(VisualWebScraper):
    """Visual scraper specifically for Mercari"""
    
    def __init__(self, openai_api_key: str):
        super().__init__(openai_api_key)
        self.base_url = "https://jp.mercari.com"
        
    async def search_items(self, keyword: str, max_items: int = 20) -> List[Dict[str, Any]]:
        """Search for items on Mercari using visual scraping"""
        await self.initialize()
        
        try:
            # Navigate to search page
            search_url = f"{self.base_url}/search?keyword={keyword}&status=on_sale"
            await self.navigate_to(search_url)
            
            # Take screenshot and analyze the search results
            items = await self._extract_search_results(max_items)
            
            # Process each item for detailed information
            detailed_items = []
            for item in items[:max_items]:
                if 'url' in item:
                    detailed_item = await self._get_item_details(item['url'])
                    detailed_items.append({**item, **detailed_item})
                else:
                    detailed_items.append(item)
                    
            return detailed_items
            
        finally:
            await self.close()
            
    async def _extract_search_results(self, max_items: int) -> List[Dict[str, Any]]:
        """Extract search results from the current page"""
        prompt = f"""
        Analyze this Mercari search results page and extract product information.
        
        For each visible product, extract:
        - title: The product name/title
        - price: The price in JPY (number only, no currency symbol)
        - image_url: The URL of the product image
        - product_url: The URL to the product detail page (construct from item ID if needed)
        - condition: The item condition if visible
        - seller: The seller name if visible
        
        Return as a JSON array with up to {max_items} items.
        Format URLs as full URLs starting with https://jp.mercari.com
        """
        
        screenshot = await self.take_screenshot()
        result = await self.analyze_screenshot_with_ai(screenshot, prompt)
        
        # Ensure we have a list
        if isinstance(result, dict) and 'items' in result:
            return result['items']
        elif isinstance(result, list):
            return result
        else:
            return []
            
    async def _get_item_details(self, item_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific item"""
        await self.navigate_to(item_url)
        
        prompt = """
        Analyze this Mercari product detail page and extract:
        - description: Full product description
        - condition: Exact condition of the item
        - shipping_method: Shipping method if specified
        - shipping_cost: Who pays for shipping
        - location: Seller's location/prefecture
        - category: Product category
        - brand: Brand name if specified
        - size: Size if applicable
        - color: Color if specified
        - sold: Whether the item is already sold (true/false)
        
        Return as a JSON object with these fields.
        """
        
        screenshot = await self.take_screenshot()
        details = await self.analyze_screenshot_with_ai(screenshot, prompt)
        
        return details if isinstance(details, dict) else {}
        
    async def monitor_price_changes(self, item_url: str, check_interval: int = 3600):
        """Monitor an item for price changes"""
        await self.initialize()
        
        previous_price = None
        while True:
            try:
                await self.navigate_to(item_url)
                
                prompt = """
                Extract the current price and availability status from this Mercari item page.
                Return as JSON: {"price": number, "available": true/false, "sold": true/false}
                """
                
                screenshot = await self.take_screenshot()
                result = await self.analyze_screenshot_with_ai(screenshot, prompt)
                
                current_price = result.get('price')
                if previous_price and current_price != previous_price:
                    yield {
                        'timestamp': asyncio.get_event_loop().time(),
                        'previous_price': previous_price,
                        'current_price': current_price,
                        'url': item_url
                    }
                    
                previous_price = current_price
                
                if result.get('sold', False):
                    break
                    
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"Error monitoring price: {e}")
                await asyncio.sleep(check_interval)
```

### 3. Advanced Visual Element Detection

```python
# src/visual_scraper/element_detector.py
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import pytesseract
from PIL import Image
import io

class VisualElementDetector:
    """Advanced visual element detection using CV and OCR"""
    
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6'
        
    def detect_buttons(self, screenshot: bytes) -> List[Dict[str, Any]]:
        """Detect button-like elements in screenshot"""
        # Convert bytes to numpy array
        nparr = np.frombuffer(screenshot, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size typical for buttons
            aspect_ratio = w / h if h > 0 else 0
            if 1.5 < aspect_ratio < 6 and 20 < h < 100 and 50 < w < 500:
                # Extract the region
                button_region = img[y:y+h, x:x+w]
                
                # OCR to get button text
                button_text = self._extract_text_from_region(button_region)
                
                buttons.append({
                    'x': x + w // 2,
                    'y': y + h // 2,
                    'width': w,
                    'height': h,
                    'text': button_text,
                    'confidence': self._calculate_button_confidence(button_region)
                })
                
        return buttons
        
    def detect_input_fields(self, screenshot: bytes) -> List[Dict[str, Any]]:
        """Detect input fields in screenshot"""
        nparr = np.frombuffer(screenshot, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold to find light backgrounds (typical for input fields)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        input_fields = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by typical input field dimensions
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio > 3 and 20 < h < 60 and w > 100:
                # Check if it looks like an input field
                field_region = img[y:y+h, x:x+w]
                if self._is_input_field(field_region):
                    # Look for label text nearby
                    label_region = img[max(0, y-30):y, x:x+w]
                    label_text = self._extract_text_from_region(label_region)
                    
                    input_fields.append({
                        'x': x + w // 2,
                        'y': y + h // 2,
                        'width': w,
                        'height': h,
                        'label': label_text,
                        'type': self._detect_input_type(label_text)
                    })
                    
        return input_fields
        
    def detect_product_cards(self, screenshot: bytes) -> List[Dict[str, Any]]:
        """Detect product card layouts in screenshot"""
        nparr = np.frombuffer(screenshot, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Use template matching or ML model to find product cards
        # This is a simplified version - in production, use trained model
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect rectangular regions that could be product cards
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cards = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by typical product card dimensions
            if 150 < w < 400 and 200 < h < 600:
                card_region = img[y:y+h, x:x+w]
                
                # Extract product information from card
                product_info = self._extract_product_info(card_region)
                if product_info:
                    cards.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        **product_info
                    })
                    
        return cards
        
    def _extract_text_from_region(self, region: np.ndarray) -> str:
        """Extract text from image region using OCR"""
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(region, cv2.COLOR_BGR2RGB))
            
            # Perform OCR
            text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
            return text.strip()
        except:
            return ""
            
    def _calculate_button_confidence(self, region: np.ndarray) -> float:
        """Calculate confidence that a region is a button"""
        # Simple heuristic based on color uniformity and borders
        # In production, use ML model
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray)
        
        # Buttons typically have uniform backgrounds
        if std_dev < 30:
            return 0.8
        elif std_dev < 50:
            return 0.6
        else:
            return 0.3
            
    def _is_input_field(self, region: np.ndarray) -> bool:
        """Check if region looks like an input field"""
        # Check for typical input field characteristics
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        mean_color = np.mean(gray)
        
        # Input fields are typically light colored
        return mean_color > 230
        
    def _detect_input_type(self, label: str) -> str:
        """Detect input field type from label"""
        label_lower = label.lower()
        
        if any(word in label_lower for word in ['email', 'mail', 'メール']):
            return 'email'
        elif any(word in label_lower for word in ['password', 'pass', 'パスワード']):
            return 'password'
        elif any(word in label_lower for word in ['search', '検索', 'キーワード']):
            return 'search'
        elif any(word in label_lower for word in ['name', '名前', '氏名']):
            return 'name'
        else:
            return 'text'
            
    def _extract_product_info(self, card_region: np.ndarray) -> Optional[Dict[str, Any]]:
        """Extract product information from a card region"""
        # This would use more sophisticated ML in production
        text = self._extract_text_from_region(card_region)
        
        if not text:
            return None
            
        # Simple pattern matching for price
        import re
        price_match = re.search(r'[¥￥]?(\d{1,3}(?:,\d{3})*)', text)
        price = price_match.group(1).replace(',', '') if price_match else None
        
        return {
            'raw_text': text,
            'price': int(price) if price else None,
            'has_image': self._detect_image_in_region(card_region)
        }
        
    def _detect_image_in_region(self, region: np.ndarray) -> bool:
        """Detect if region contains an image"""
        # Check for high variance areas typical of product images
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return laplacian_var > 100
```

### 4. Integration with Existing buy_records Project

```python
# src/collectors/mercari_visual.py
import asyncio
from typing import List, Dict, Any
from ..visual_scraper.mercari_visual_scraper import MercariVisualScraper
from ..utils.config import get_config
import os

class MercariVisualCollector:
    """Mercari collector using visual AI scraping"""
    
    def __init__(self):
        self.openai_api_key = get_config("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
            
    async def search_items(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for items using visual scraping"""
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
                    'scraping_method': 'visual_ai'
                })
                
            return transformed_items
            
        except Exception as e:
            print(f"Error in visual scraping: {e}")
            return []
            
    def _extract_item_id(self, url: str) -> str:
        """Extract item ID from URL"""
        if '/item/' in url:
            return url.split('/item/')[-1].split('?')[0]
        return ''
        
    def get_complete_data(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get complete data synchronously (wrapper for async method)"""
        return asyncio.run(self.search_items(keyword, limit))
```

### 5. Deployment Configuration

```yaml
# docker-compose.yml addition
  visual-scraper:
    build:
      context: .
      dockerfile: Dockerfile.visual
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CLOUD_VISION_KEY=${GOOGLE_CLOUD_VISION_KEY}
    volumes:
      - ./screenshots:/app/screenshots
    depends_on:
      - postgres
    networks:
      - app-network
```

```dockerfile
# Dockerfile.visual
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0

WORKDIR /app

# Copy requirements
COPY requirements-visual.txt .
RUN pip install -r requirements-visual.txt

# Install playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

CMD ["python", "-m", "src.visual_scraper.server"]
```

## Advanced Features

### 1. Self-Healing Selectors
```python
async def find_element_with_fallback(self, descriptions: List[str]) -> Optional[Tuple[int, int]]:
    """Try multiple descriptions to find an element"""
    for desc in descriptions:
        coords = await self.find_element_visually(desc)
        if coords:
            return coords
    return None
```

### 2. Visual Change Detection
```python
async def wait_for_visual_change(self, region: Tuple[int, int, int, int], timeout: int = 30):
    """Wait for visual changes in a specific region"""
    initial_screenshot = await self.capture_region(region)
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        current_screenshot = await self.capture_region(region)
        if not self._images_are_similar(initial_screenshot, current_screenshot):
            return True
        await asyncio.sleep(0.5)
    
    return False
```

### 3. Multi-Model Consensus
```python
async def extract_with_consensus(self, screenshot: bytes, prompt: str) -> Dict[str, Any]:
    """Use multiple AI models and merge results"""
    results = []
    
    # OpenAI Vision
    openai_result = await self.analyze_with_openai(screenshot, prompt)
    results.append(openai_result)
    
    # Google Vision
    google_result = await self.analyze_with_google(screenshot, prompt)
    results.append(google_result)
    
    # Local model
    local_result = await self.analyze_with_local_model(screenshot, prompt)
    results.append(local_result)
    
    # Merge and validate results
    return self._merge_results(results)
```

## Benefits Over Traditional Scraping

1. **Resilience to DOM Changes**: Visual scraping doesn't rely on specific HTML structure
2. **Works with Dynamic Content**: Can handle JavaScript-rendered content naturally
3. **Human-like Interaction**: Interacts with pages as a human would
4. **Better Anti-Bot Evasion**: Harder to detect than traditional scraping
5. **Cross-Platform Compatibility**: Same approach works across different sites
6. **Visual Verification**: Can verify actions were successful visually

## Challenges and Solutions

1. **Cost**: Vision API calls can be expensive
   - Solution: Implement caching and selective visual analysis

2. **Speed**: Visual analysis is slower than DOM parsing
   - Solution: Parallel processing and optimized screenshot regions

3. **Accuracy**: AI might misinterpret visual elements
   - Solution: Use multiple models and validation logic

4. **Dynamic Content**: Pages might change during scraping
   - Solution: Visual change detection and retry logic

## Monitoring and Debugging

```python
# src/visual_scraper/debugger.py
class VisualScraperDebugger:
    """Debugging tools for visual scraping"""
    
    async def save_annotated_screenshot(self, screenshot: bytes, elements: List[Dict], filename: str):
        """Save screenshot with detected elements highlighted"""
        # Implementation for visual debugging
        pass
        
    async def record_scraping_session(self, output_dir: str):
        """Record entire scraping session for debugging"""
        # Implementation for session recording
        pass
```

This implementation provides a robust foundation for AI-powered visual web scraping that can be integrated into the existing buy_records project while maintaining compatibility with the current data structures and workflows.