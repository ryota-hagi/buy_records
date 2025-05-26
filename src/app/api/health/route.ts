import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // 基本的なヘルスチェック
    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: process.env.NODE_ENV || 'unknown',
      version: process.env.npm_package_version || '1.0.0',
    };

    // 環境変数の存在確認（値は返さない）
    const envCheck = {
      supabase_url: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
      supabase_anon_key: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
      yahoo_app_id: !!process.env.YAHOO_SHOPPING_APP_ID,
      ebay_app_id: !!process.env.EBAY_APP_ID,
    };

    return NextResponse.json({
      ...healthStatus,
      environment_variables: envCheck,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
