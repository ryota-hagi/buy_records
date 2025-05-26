# AI-Powered Visual Web Scraping System

## Overview

This visual web scraping system uses AI vision models to analyze screenshots and interact with web pages visually, providing a more robust alternative to traditional DOM-based scraping.

## Quick Start

### 1. Set up environment variables

```bash
export OPENAI_API_KEY='your-openai-api-key'
export GOOGLE_CLOUD_VISION_KEY='your-google-vision-key'  # Optional
```

### 2. Install dependencies

```bash
pip install -r requirements-visual.txt
playwright install chromium
```

### 3. Run test script

```bash
python scripts/test_visual_scraper.py
```

## Usage Examples

### Basic Search

```python
from src.collectors.mercari_visual import MercariVisualCollector

collector = MercariVisualCollector()
items = collector.search_items("vintage record", limit=10)

for item in items:
    print(f"{item['title']} - ¥{item['price']:,}")
```

### Async Usage

```python
import asyncio
from src.visual_scraper.mercari_visual_scraper import MercariVisualScraper

async def search_products():
    scraper = MercariVisualScraper(openai_api_key)
    items = await scraper.search_items("Beatles LP", max_items=20)
    return items

items = asyncio.run(search_products())
```

### Monitor Price Changes

```python
async def monitor_item():
    scraper = MercariVisualScraper(openai_api_key)
    item_url = "https://jp.mercari.com/item/m12345678"
    
    async for change in scraper.monitor_price_changes(item_url):
        print(f"Price changed from ¥{change['previous_price']} to ¥{change['current_price']}")
```

### Visual Element Detection

```python
from src.visual_scraper.element_detector import VisualElementDetector

detector = VisualElementDetector()

# Detect buttons in screenshot
buttons = detector.detect_buttons(screenshot_bytes)

# Extract all text regions
text_regions = detector.extract_text_regions(screenshot_bytes)

# Find prices
prices = detector.detect_prices(screenshot_bytes)
```

## Architecture

### Components

1. **Base Visual Scraper** (`base_scraper.py`)
   - Core functionality for browser automation
   - AI vision API integration
   - Visual element finding and interaction

2. **Mercari Visual Scraper** (`mercari_visual_scraper.py`)
   - Mercari-specific implementation
   - Product search and extraction
   - Price monitoring

3. **Element Detector** (`element_detector.py`)
   - Computer vision-based element detection
   - OCR for text extraction
   - Pattern matching for specific elements

4. **Collector Integration** (`mercari_visual.py`)
   - Integration with existing buy_records project
   - Data transformation to match existing formats

## Features

### Advantages Over Traditional Scraping

1. **DOM-Independent**: Works even when HTML structure changes
2. **JavaScript Support**: Naturally handles dynamic content
3. **Anti-Bot Resilient**: Harder to detect than DOM scraping
4. **Visual Verification**: Can verify actions visually
5. **Cross-Platform**: Same approach works on different sites

### Advanced Capabilities

- **Multi-Model Consensus**: Use multiple AI models for accuracy
- **Visual Change Detection**: Wait for visual changes
- **Self-Healing**: Multiple fallback descriptions for elements
- **Pagination Support**: Navigate through multiple pages
- **Image-Based Search**: Search by uploading images

## Docker Deployment

### Build the image

```bash
docker build -f Dockerfile.visual -t visual-scraper .
```

### Run container

```bash
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY \
           -v $(pwd)/screenshots:/app/screenshots \
           visual-scraper
```

### Docker Compose

```yaml
services:
  visual-scraper:
    build:
      context: .
      dockerfile: Dockerfile.visual
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./screenshots:/app/screenshots
```

## Cost Optimization

### Tips to Reduce API Costs

1. **Cache Results**: Store and reuse AI analysis results
2. **Selective Analysis**: Only analyze changed regions
3. **Lower Resolution**: Use lower resolution for initial detection
4. **Batch Processing**: Combine multiple queries into one
5. **Local Models**: Use local OCR for text extraction

### Example Caching Implementation

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_ai_analysis(image_hash: str, prompt: str):
    # Cached AI analysis
    return ai_result

def analyze_with_cache(screenshot: bytes, prompt: str):
    image_hash = hashlib.md5(screenshot).hexdigest()
    return cached_ai_analysis(image_hash, prompt)
```

## Debugging

### Enable Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Save Screenshots

```python
# Save screenshot for debugging
with open('debug_screenshot.png', 'wb') as f:
    f.write(screenshot_bytes)
```

### Visual Debugging

```python
# Highlight detected elements
import cv2
for button in buttons:
    cv2.rectangle(img, 
                  (button['x']-button['width']//2, button['y']-button['height']//2),
                  (button['x']+button['width']//2, button['y']+button['height']//2),
                  (0, 255, 0), 2)
cv2.imwrite('detected_buttons.png', img)
```

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Set the environment variable: `export OPENAI_API_KEY='your-key'`

2. **"Playwright browsers not installed"**
   - Run: `playwright install chromium`

3. **"OCR not working"**
   - Install Tesseract: `apt-get install tesseract-ocr tesseract-ocr-jpn`

4. **"Import errors"**
   - Ensure PYTHONPATH includes project root: `export PYTHONPATH=/path/to/buy_records`

### Performance Tips

1. Use `full_page=False` for faster screenshots
2. Limit the number of items to extract
3. Use region-specific screenshots when possible
4. Implement parallel processing for multiple searches

## API Reference

### VisualWebScraper

```python
async def initialize()
async def navigate_to(url: str)
async def take_screenshot(full_page: bool = True) -> bytes
async def analyze_screenshot_with_ai(screenshot: bytes, prompt: str) -> Dict
async def find_element_visually(description: str) -> Optional[Tuple[int, int]]
async def click_element_visually(description: str) -> bool
async def extract_data_visually(data_description: str) -> List[Dict]
async def close()
```

### MercariVisualScraper

```python
async def search_items(keyword: str, max_items: int = 20) -> List[Dict]
async def monitor_price_changes(item_url: str, check_interval: int = 3600)
async def search_by_image(image_path: str, max_items: int = 20) -> List[Dict]
async def get_seller_items(seller_name: str, max_items: int = 50) -> List[Dict]
```

### VisualElementDetector

```python
def detect_buttons(screenshot: bytes) -> List[Dict]
def detect_input_fields(screenshot: bytes) -> List[Dict]
def detect_product_cards(screenshot: bytes) -> List[Dict]
def detect_prices(screenshot: bytes) -> List[Dict]
def extract_text_regions(screenshot: bytes) -> List[Dict]
```

## Future Enhancements

1. **Local Vision Models**: Integrate open-source vision models
2. **Multi-Site Support**: Add support for Yahoo Auctions, eBay
3. **Mobile View**: Support mobile web scraping
4. **Video Analysis**: Analyze video content on pages
5. **3D Product Views**: Extract from 360° product views
6. **Batch Processing**: Process multiple searches in parallel
7. **Smart Caching**: Intelligent caching based on page regions
8. **A/B Testing**: Compare different AI models automatically