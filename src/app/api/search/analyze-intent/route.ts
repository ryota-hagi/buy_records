import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

interface IntentAnalysis {
  intent: 'main_product' | 'accessory' | 'both' | 'unclear';
  main_product?: string;
  accessory_type?: string;
  keywords: string[];
  confidence: number;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;

    if (!query) {
      return NextResponse.json(
        { error: 'クエリが必要です' },
        { status: 400 }
      );
    }

    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { error: 'OpenAI APIキーが設定されていません' },
        { status: 500 }
      );
    }

    console.log(`検索意図分析開始: ${query}`);

    const prompt = `
以下の検索クエリを分析して、ユーザーの検索意図をJSON形式で返してください。

検索クエリ: "${query}"

分析項目:
1. intent: ユーザーが探しているのは主製品(main_product)、アクセサリー(accessory)、両方(both)、または不明(unclear)か
2. main_product: 主製品の名前（例：Nintendo Switch、iPhone 15）
3. accessory_type: アクセサリーの種類（例：ケース、保護フィルム、充電器）
4. keywords: 検索に使用すべきキーワードの配列
5. confidence: 分析の確信度（0-1の数値）

例:
- "Nintendo Switch 本体" → {"intent": "main_product", "main_product": "Nintendo Switch", "keywords": ["Nintendo Switch", "ニンテンドースイッチ", "本体"], "confidence": 0.95}
- "Switch ケース" → {"intent": "accessory", "main_product": "Nintendo Switch", "accessory_type": "ケース", "keywords": ["Switch ケース", "Nintendo Switch ケース"], "confidence": 0.9}
- "iPhone 15 Pro Max 256GB" → {"intent": "main_product", "main_product": "iPhone 15 Pro Max 256GB", "keywords": ["iPhone 15 Pro Max", "256GB"], "confidence": 0.95}
`;

    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: '日本語の商品検索クエリを分析する専門家として、検索意図を正確に判定してください。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        response_format: { type: 'json_object' },
        temperature: 0.3,
        max_tokens: 500
      });

      const analysis = JSON.parse(response.choices[0].message.content || '{}') as IntentAnalysis;

      console.log('検索意図分析結果:', analysis);

      return NextResponse.json({
        success: true,
        query,
        analysis,
        timestamp: new Date().toISOString()
      });

    } catch (openaiError) {
      console.error('OpenAI APIエラー:', openaiError);
      return NextResponse.json(
        { 
          success: false,
          error: 'AI分析中にエラーが発生しました',
          details: openaiError instanceof Error ? openaiError.message : '不明なエラー'
        },
        { status: 500 }
      );
    }

  } catch (error) {
    console.error('検索意図分析エラー:', error);
    
    return NextResponse.json(
      { 
        success: false,
        error: '検索意図分析中にエラーが発生しました',
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