import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

interface Product {
  title: string;
  price: number;
  platform?: string;
  url?: string;
}

interface ClassifiedProduct extends Product {
  category: 'main' | 'accessory' | 'related' | 'unrelated';
  confidence: number;
  reason?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { products, target_product, intent } = body;

    if (!products || !Array.isArray(products) || products.length === 0) {
      return NextResponse.json(
        { error: '商品リストが必要です' },
        { status: 400 }
      );
    }

    if (!target_product) {
      return NextResponse.json(
        { error: 'ターゲット商品名が必要です' },
        { status: 400 }
      );
    }

    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { error: 'OpenAI APIキーが設定されていません' },
        { status: 500 }
      );
    }

    console.log(`商品分類開始: ${products.length}件の商品`);

    // バッチ処理のサイズ
    const batchSize = 20;
    const classifiedProducts: ClassifiedProduct[] = [];

    for (let i = 0; i < products.length; i += batchSize) {
      const batch = products.slice(i, i + batchSize);
      
      const prompt = `
以下の商品リストを「${target_product}」との関連性に基づいて分類してください。
検索意図: ${intent || 'main_product'}

商品リスト:
${batch.map((p, idx) => `${idx + 1}. ${p.title} (¥${p.price})`).join('\n')}

各商品を以下のカテゴリーに分類し、JSON配列で返してください:
- "main": 本体・主製品（探している商品そのもの）
- "accessory": アクセサリー・周辺機器
- "related": 関連商品（同じカテゴリーだが異なる製品）
- "unrelated": 無関係な商品

フォーマット:
[
  {"index": 1, "category": "main", "confidence": 0.95, "reason": "Nintendo Switch本体"},
  {"index": 2, "category": "accessory", "confidence": 0.9, "reason": "Switch用ケース"}
]
`;

      try {
        const response = await openai.chat.completions.create({
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: 'EC商品の分類専門家として、商品を正確にカテゴライズしてください。'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          response_format: { type: 'json_object' },
          temperature: 0.3,
          max_tokens: 1000
        });

        let classifications;
        try {
          const content = response.choices[0].message.content || '{}';
          const parsed = JSON.parse(content);
          // 配列が直接返される場合と、オブジェクトでラップされている場合の両方に対応
          classifications = Array.isArray(parsed) ? parsed : (parsed.classifications || parsed.results || []);
        } catch (parseError) {
          console.error('JSON解析エラー:', parseError);
          // フォールバック: すべての商品を関連商品として扱う
          classifications = batch.map((_, idx) => ({
            index: idx + 1,
            category: 'related',
            confidence: 0.5,
            reason: 'AI分類失敗'
          }));
        }

        // 分類結果を元の商品データとマージ
        batch.forEach((product, idx) => {
          const classification = classifications.find((c: any) => c.index === idx + 1) || {
            category: 'related',
            confidence: 0.5
          };

          classifiedProducts.push({
            ...product,
            category: classification.category || 'related',
            confidence: classification.confidence || 0.5,
            reason: classification.reason
          });
        });

      } catch (openaiError) {
        console.error('OpenAI APIエラー:', openaiError);
        // エラーの場合はデフォルト分類を適用
        batch.forEach(product => {
          classifiedProducts.push({
            ...product,
            category: 'related',
            confidence: 0.5,
            reason: 'AI分類エラー'
          });
        });
      }
    }

    // カテゴリーごとに集計
    const summary = {
      main: classifiedProducts.filter(p => p.category === 'main').length,
      accessory: classifiedProducts.filter(p => p.category === 'accessory').length,
      related: classifiedProducts.filter(p => p.category === 'related').length,
      unrelated: classifiedProducts.filter(p => p.category === 'unrelated').length
    };

    console.log('商品分類完了:', summary);

    return NextResponse.json({
      success: true,
      target_product,
      intent,
      classified_products: classifiedProducts,
      summary,
      total_products: products.length,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('商品分類エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '商品分類中にエラーが発生しました',
        details: error instanceof Error ? error.message : '不明なエラー'
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json(
    { error: 'このエンドポイントはPOSTメソッドのみサポートしています' },
    { status: 405 }
  );
}