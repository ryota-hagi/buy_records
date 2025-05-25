import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const testResults = {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV,
      vercel_region: process.env.VERCEL_REGION || 'unknown',
      yahoo_api_key_exists: !!process.env.YAHOO_SHOPPING_APP_ID,
      ebay_api_key_exists: !!process.env.EBAY_APP_ID,
      yahoo_api_key_length: process.env.YAHOO_SHOPPING_APP_ID?.length || 0,
      ebay_api_key_length: process.env.EBAY_APP_ID?.length || 0,
      user_agent: request.headers.get('user-agent'),
      ip_info: {
        x_forwarded_for: request.headers.get('x-forwarded-for'),
        x_real_ip: request.headers.get('x-real-ip'),
        cf_connecting_ip: request.headers.get('cf-connecting-ip')
      }
    };
    
    return NextResponse.json({
      success: true,
      message: "本番環境テスト成功",
      data: testResults
    });
    
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    }, { status: 500 });
  }
}
