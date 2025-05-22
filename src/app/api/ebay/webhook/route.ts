import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

// 環境変数から検証トークンを取得
// 注意: 実際のデプロイ時には、Vercelの環境変数設定でこの値を設定する必要があります
const VERIFICATION_TOKEN = process.env.EBAY_VERIFICATION_TOKEN || '8f7d56a1e9b3c2d4f5e6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8';

// GETリクエスト - チャレンジコード処理
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const challengeCode = searchParams.get('challenge_code');
  
  if (!challengeCode) {
    return NextResponse.json({ error: 'Challenge code is required' }, { status: 400 });
  }
  
  // チャレンジレスポンスの計算
  const endpointUrl = new URL(request.url).origin + new URL(request.url).pathname;
  const dataToHash = challengeCode + VERIFICATION_TOKEN + endpointUrl;
  const challengeResponse = crypto.createHash('sha256').update(dataToHash).digest('hex');
  
  // レスポンスを返す
  return NextResponse.json({ challengeResponse });
}

// POSTリクエスト - 削除通知処理
export async function POST(request: NextRequest) {
  try {
    const notification = await request.json();
    console.log('Received eBay notification:', notification);
    
    // 通知を処理
    // ユーザーデータの削除処理などを実装
    
    // 成功レスポンスを返す
    return NextResponse.json({ status: 'success' });
  } catch (error) {
    console.error('Error processing eBay notification:', error);
    return NextResponse.json({ error: 'Failed to process notification' }, { status: 500 });
  }
}
