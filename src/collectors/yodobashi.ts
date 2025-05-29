export class YodobashiScraper {
  async search(query: string, limit: number = 20) {
    // Yodobashi.comの検索APIを使用
    const apiUrl = `https://www.yodobashi.com/category/ajax/search/?word=${encodeURIComponent(query)}&num=${limit}`;
    
    try {
      const response = await fetch(apiUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Handle different response formats
      const products = data.productList || data.products || data.items || data.results || [];
      const totalCount = data.totalCount || data.total || data.count || products.length;
      
      return {
        success: true,
        results: this.formatResults(products),
        metadata: {
          total_results: totalCount,
          search_query: query
        }
      };
    } catch (error) {
      console.error('Yodobashi search error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        results: []
      };
    }
  }

  private formatResults(products: any[]) {
    if (!Array.isArray(products)) {
      console.error('Yodobashi: products is not an array:', products);
      return [];
    }
    
    return products.map((product: any) => ({
      platform: 'yodobashi',
      title: product.productName || product.name || product.title || '',
      url: product.productUrl || product.url || '',
      image_url: product.imageUrl || product.image || '',
      price: parseInt(product.price || '0') || 0,
      shipping_fee: 0, // ヨドバシは送料無料
      total_price: parseInt(product.price || '0') || 0,
      condition: '新品',
      store_name: 'ヨドバシカメラ',
      location: '日本',
      currency: 'JPY',
      jan_code: product.janCode || product.jan || '',
      availability: product.stockStatus || product.stock || ''
    }));
  }
}