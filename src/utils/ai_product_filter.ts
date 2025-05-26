import OpenAI from 'openai';

export interface ProductRelevanceCheck {
  isRelevant: boolean;
  confidence: number;
  reason: string;
  category: 'exact_match' | 'related_product' | 'accessory' | 'unrelated';
}

export interface FilterConfig {
  minConfidence?: number;
  allowAccessories?: boolean;
  enableLogging?: boolean;
}

/**
 * AI-powered product relevance filter
 * Uses OpenAI GPT-4 to determine if search results match user intent
 */
export class AIProductFilter {
  private openai: OpenAI | null = null;
  private config: FilterConfig;

  constructor(config: FilterConfig = {}) {
    this.config = {
      minConfidence: 0.7,
      allowAccessories: false,
      enableLogging: true,
      ...config
    };

    // Initialize OpenAI client if API key is available
    const apiKey = process.env.OPENAI_API_KEY;
    if (apiKey) {
      this.openai = new OpenAI({ apiKey });
    } else if (this.config.enableLogging) {
      console.warn('[AI_FILTER] OpenAI API key not found. AI filtering will be disabled.');
    }
  }

  /**
   * Check if a product is relevant to the user's search intent
   */
  async checkProductRelevance(
    searchQuery: string,
    productTitle: string,
    productDescription?: string
  ): Promise<ProductRelevanceCheck> {
    if (!this.openai) {
      // Fallback: basic keyword matching
      return this.fallbackRelevanceCheck(searchQuery, productTitle);
    }

    try {
      const prompt = this.buildRelevancePrompt(searchQuery, productTitle, productDescription);
      
      const response = await this.openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: "あなたは商品検索の関連性を判定するエキスパートです。ユーザーの検索意図と商品が一致するかを正確に判断してください。JSON形式で結果を返してください。"
          },
          {
            role: "user",
            content: prompt
          }
        ],
        max_tokens: 500,
        temperature: 0.1,
        response_format: { type: "json_object" }
      });

      const result = response.choices[0].message.content;
      if (!result) {
        throw new Error('Empty response from OpenAI');
      }

      const parsed = JSON.parse(result) as ProductRelevanceCheck;
      
      if (this.config.enableLogging) {
        console.log(`[AI_FILTER] Query: "${searchQuery}" → Product: "${productTitle}" → Relevant: ${parsed.isRelevant} (${parsed.confidence})`);
      }
      
      return parsed;

    } catch (error) {
      if (this.config.enableLogging) {
        console.error('[AI_FILTER] OpenAI API error:', error);
      }
      
      // Fallback to keyword matching
      return this.fallbackRelevanceCheck(searchQuery, productTitle);
    }
  }

  /**
   * Filter an array of products based on relevance to search query
   */
  async filterProducts<T extends { title?: string; item_title?: string; description?: string }>(
    searchQuery: string,
    products: T[]
  ): Promise<T[]> {
    if (!products.length) return products;

    const relevanceChecks = await Promise.all(
      products.map(async (product) => {
        const title = product.title || product.item_title || '';
        const description = product.description || '';
        
        const check = await this.checkProductRelevance(searchQuery, title, description);
        return { product, check };
      })
    );

    const filteredProducts = relevanceChecks
      .filter(({ check }) => {
        if (!check.isRelevant) return false;
        if (check.confidence < this.config.minConfidence!) return false;
        if (!this.config.allowAccessories && check.category === 'accessory') return false;
        return true;
      })
      .map(({ product }) => product);

    if (this.config.enableLogging) {
      console.log(`[AI_FILTER] Filtered ${products.length} → ${filteredProducts.length} products for query: "${searchQuery}"`);
    }

    return filteredProducts;
  }

  /**
   * Build the prompt for relevance checking
   */
  private buildRelevancePrompt(searchQuery: string, productTitle: string, productDescription?: string): string {
    return `
ユーザーの検索クエリ: "${searchQuery}"
商品タイトル: "${productTitle}"
${productDescription ? `商品説明: "${productDescription}"` : ''}

この商品がユーザーの検索意図に合致するかを判定してください。

判定基準:
1. exact_match: 検索クエリと完全に一致する商品
2. related_product: 関連する商品（同シリーズ、互換品など）
3. accessory: 付属品やアクセサリー（ケース、カバー、充電器など）
4. unrelated: 無関係な商品

例:
- 検索: "iPhone 15" → "iPhone 15 128GB" = exact_match
- 検索: "iPhone 15" → "iPhone 15 Pro" = related_product  
- 検索: "iPhone 15" → "iPhone 15 ケース" = accessory
- 検索: "iPhone 15" → "Samsung Galaxy" = unrelated

以下のJSON形式で回答してください:
{
  "isRelevant": boolean,
  "confidence": number (0.0-1.0),
  "reason": "判定理由",
  "category": "exact_match | related_product | accessory | unrelated"
}
    `.trim();
  }

  /**
   * Fallback relevance check using keyword matching
   */
  private fallbackRelevanceCheck(searchQuery: string, productTitle: string): ProductRelevanceCheck {
    const query = searchQuery.toLowerCase().trim();
    const title = productTitle.toLowerCase().trim();

    // Basic keyword matching
    const queryWords = query.split(/\s+/);
    const titleWords = title.split(/\s+/);
    
    const matchingWords = queryWords.filter(word => 
      titleWords.some(titleWord => titleWord.includes(word) || word.includes(titleWord))
    );
    
    const matchRatio = matchingWords.length / queryWords.length;
    
    // Check for accessory keywords
    const accessoryKeywords = ['ケース', 'カバー', '充電器', 'フィルム', '保護', 'スタンド', 'ホルダー', 'case', 'cover', 'charger', 'film', 'protector', 'stand', 'holder'];
    const isAccessory = accessoryKeywords.some(keyword => title.includes(keyword));
    
    let category: ProductRelevanceCheck['category'] = 'unrelated';
    let isRelevant = false;
    let confidence = matchRatio;
    
    if (matchRatio >= 0.8) {
      category = 'exact_match';
      isRelevant = true;
      confidence = 0.9;
    } else if (matchRatio >= 0.5) {
      category = isAccessory ? 'accessory' : 'related_product';
      isRelevant = !isAccessory || this.config.allowAccessories!;
      confidence = 0.7;
    } else if (matchRatio >= 0.3) {
      category = 'accessory';
      isRelevant = this.config.allowAccessories!;
      confidence = 0.5;
    }
    
    return {
      isRelevant,
      confidence,
      reason: `Keyword matching: ${matchRatio.toFixed(2)} match ratio${isAccessory ? ' (accessory detected)' : ''}`,
      category
    };
  }
}

// Export default instance
export const aiProductFilter = new AIProductFilter();