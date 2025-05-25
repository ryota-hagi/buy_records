#!/usr/bin/env python3
"""
ローカル環境 vs 本番環境の違い分析
APIが動作しない原因を特定
"""

def analyze_differences():
    """ローカル環境と本番環境の主要な違いを分析"""
    
    print("🔍 ローカル環境 vs 本番環境（Vercel）の違い分析")
    print("=" * 70)
    
    differences = [
        {
            "category": "🌐 ネットワーク・IP制限",
            "local": "開発者のローカルIP（固定・既知）",
            "production": "Vercelのサーバーファーム（動的・複数IP）",
            "impact": "Yahoo/eBay APIがVercelのIPを制限している可能性",
            "solution": "APIプロバイダーでIP制限を確認・解除"
        },
        {
            "category": "🔑 環境変数・APIキー",
            "local": ".env.localファイルから読み込み",
            "production": "Vercel環境変数設定から読み込み",
            "impact": "APIキーが正しく設定されていない可能性",
            "solution": "Vercelダッシュボードで環境変数を確認・設定"
        },
        {
            "category": "🚀 デプロイ・ビルド",
            "local": "リアルタイムでコード変更が反映",
            "production": "デプロイ時にビルドされた静的バージョン",
            "impact": "最新のコード修正が反映されていない",
            "solution": "Vercelで再デプロイを実行"
        },
        {
            "category": "🔒 CORS・セキュリティ",
            "local": "制限が緩い開発環境",
            "production": "厳格なセキュリティポリシー",
            "impact": "外部API呼び出しがブロックされる可能性",
            "solution": "CORS設定やセキュリティヘッダーを調整"
        },
        {
            "category": "⏱️ タイムアウト・制限",
            "local": "無制限の実行時間",
            "production": "Vercel Serverless Functions（10秒制限）",
            "impact": "長時間のAPI呼び出しがタイムアウト",
            "solution": "タイムアウト時間を短縮、並行処理を最適化"
        },
        {
            "category": "🌍 地理的位置",
            "local": "日本国内からのアクセス",
            "production": "Vercelのグローバルエッジネットワーク",
            "impact": "地域制限のあるAPIが動作しない",
            "solution": "リージョン設定を日本に固定"
        },
        {
            "category": "📊 ログ・デバッグ",
            "local": "詳細なコンソールログが見える",
            "production": "限定的なログ、デバッグが困難",
            "impact": "エラーの詳細が分からない",
            "solution": "Vercelログを確認、詳細ログを追加"
        },
        {
            "category": "🔄 キャッシュ・CDN",
            "local": "キャッシュなし",
            "production": "Vercel CDNによるキャッシュ",
            "impact": "古いレスポンスがキャッシュされている",
            "solution": "キャッシュをクリア、Cache-Controlヘッダー設定"
        }
    ]
    
    for i, diff in enumerate(differences, 1):
        print(f"\n{i}. {diff['category']}")
        print(f"   ローカル: {diff['local']}")
        print(f"   本番環境: {diff['production']}")
        print(f"   🚨 影響: {diff['impact']}")
        print(f"   💡 解決策: {diff['solution']}")
    
    print("\n" + "=" * 70)
    print("🎯 最も可能性の高い原因")
    print("=" * 70)
    
    likely_causes = [
        {
            "rank": 1,
            "cause": "環境変数（APIキー）の設定問題",
            "evidence": "Yahoo APIで400エラー = 認証失敗",
            "check": "Vercelダッシュボード > Settings > Environment Variables"
        },
        {
            "rank": 2,
            "cause": "デプロイされていない最新コード",
            "evidence": "統合検索APIで404エラー",
            "check": "Vercel > Deployments で最新デプロイを確認"
        },
        {
            "rank": 3,
            "cause": "IP制限・地域制限",
            "evidence": "eBay APIで500エラー",
            "check": "eBay Developer Console でIP制限を確認"
        },
        {
            "rank": 4,
            "cause": "Serverless Function制限",
            "evidence": "タイムアウトやメモリ制限",
            "check": "Vercel Function Logs でエラー詳細を確認"
        }
    ]
    
    for cause in likely_causes:
        print(f"\n{cause['rank']}位: {cause['cause']}")
        print(f"   根拠: {cause['evidence']}")
        print(f"   確認方法: {cause['check']}")
    
    print("\n" + "=" * 70)
    print("🔧 即座に実行すべき対策")
    print("=" * 70)
    
    actions = [
        "1. Vercelで環境変数を確認・再設定",
        "2. 最新コードを強制デプロイ",
        "3. Vercel Function Logsでエラー詳細を確認",
        "4. Yahoo/eBay Developer Consoleで制限を確認",
        "5. 簡単なテストAPIを作成して基本動作を確認"
    ]
    
    for action in actions:
        print(f"   {action}")
    
    return differences, likely_causes

def create_test_api_code():
    """本番環境テスト用の簡単なAPIコードを生成"""
    
    test_api_code = '''
// src/app/api/test-production/route.ts
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
'''
    
    print("\n" + "=" * 70)
    print("🧪 本番環境テスト用APIコード")
    print("=" * 70)
    print("以下のコードを src/app/api/test-production/route.ts に作成してください:")
    print(test_api_code)
    print("\nデプロイ後、以下のURLでテスト:")
    print("https://buy-records.vercel.app/api/test-production")

if __name__ == "__main__":
    differences, likely_causes = analyze_differences()
    create_test_api_code()
    
    print(f"\n🎯 結論: ローカルで動作するAPIが本番で失敗する主な理由は")
    print(f"環境の違い（特に環境変数とデプロイ状況）です。")
