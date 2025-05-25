# Mercari Scraper Actor

A custom Apify Actor for scraping product data from Mercari, Japan's largest marketplace platform.

## Features

- Search products by keyword
- Extract product titles, prices, URLs, and images
- Configurable maximum item count
- Robust error handling
- Optimized for Mercari's current DOM structure

## Input Parameters

- **searchKeyword** (required): The keyword to search for on Mercari
- **maxItems** (optional): Maximum number of items to scrape (default: 20, max: 100)
- **includeImages** (optional): Whether to include product image URLs (default: true)
- **includeDescription** (optional): Whether to include product descriptions (default: false, not implemented yet)

## Output

The actor outputs an array of product objects with the following structure:

```json
{
  "title": "Nintendo Switch 本体",
  "price": 25000,
  "priceText": "¥25,000",
  "url": "https://jp.mercari.com/item/m12345678901",
  "condition": "やや傷や汚れあり",
  "platform": "mercari",
  "currency": "JPY",
  "imageUrl": "https://static.mercdn.net/item/detail/orig/photos/..."
}
```

## Usage

### Via Apify API

```javascript
const ApifyClient = require('apify-client');

const client = new ApifyClient({
    token: 'YOUR_APIFY_TOKEN',
});

const input = {
    searchKeyword: 'Nintendo Switch',
    maxItems: 20,
    includeImages: true
};

const run = await client.actor('YOUR_USERNAME/mercari-scraper').call(input);
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items);
```

### Via Python

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")

run_input = {
    "searchKeyword": "Nintendo Switch",
    "maxItems": 20,
    "includeImages": True
}

run = client.actor("YOUR_USERNAME/mercari-scraper").call(run_input=run_input)

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

## Technical Details

- Built with Apify SDK v3
- Uses Puppeteer for web scraping
- Handles dynamic content loading
- Includes retry logic for failed requests
- Optimized for Mercari's anti-bot measures

## Development

To run locally:

1. Install dependencies: `npm install`
2. Run the actor: `npm start`

To deploy to Apify:

1. Install Apify CLI: `npm install -g apify-cli`
2. Login: `apify login`
3. Push to Apify: `apify push`

## Notes

- This actor is designed specifically for Mercari Japan (jp.mercari.com)
- Respects Mercari's robots.txt and terms of service
- Includes appropriate delays to avoid overwhelming the server
- May require updates if Mercari changes their DOM structure

## License

MIT License
