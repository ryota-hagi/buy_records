#!/usr/bin/env python3
"""
APIリクエスト元IPアドレスの詳細説明
ローカル環境と本番環境での違いを解説
"""

def explain_api_request_ip():
    """APIリクエスト元IPアドレスについて詳しく説明"""
    
    print("🌐 APIリクエスト元IPアドレスとは？")
    print("=" * 70)
    
    print("""
APIリクエスト元IPアドレスとは、外部APIサーバー（Yahoo、eBay、Mercari）から見て、
「どのIPアドレスからリクエストが来ているか」を示すものです。

これは、あなたのアプリケーションが外部APIを呼び出す際に、
外部APIプロバイダーが識別する「送信者のIPアドレス」です。
""")
    
    print("\n🏠 ローカル環境でのAPIリクエスト")
    print("-" * 50)
    
    local_scenario = {
        "環境": "ローカル開発環境（あなたのPC）",
        "IPアドレス": "あなたの自宅/オフィスのグローバルIP",
        "例": "203.104.209.xxx（固定または準固定）",
        "特徴": [
            "ISP（インターネットプロバイダー）から割り当てられたIP",
            "比較的安定したIPアドレス",
            "一般的な個人/企業のIPアドレス",
            "APIプロバイダーから見ると「通常のユーザー」"
        ],
        "APIプロバイダーの反応": "通常は制限なしで受け入れ"
    }
    
    print(f"環境: {local_scenario['環境']}")
    print(f"IPアドレス: {local_scenario['IPアドレス']}")
    print(f"例: {local_scenario['例']}")
    print("特徴:")
    for feature in local_scenario['特徴']:
        print(f"  - {feature}")
    print(f"APIプロバイダーの反応: {local_scenario['APIプロバイダーの反応']}")
    
    print("\n☁️ 本番環境（Vercel）でのAPIリクエスト")
    print("-" * 50)
    
    production_scenario = {
        "環境": "Vercel Serverless Functions",
        "IPアドレス": "VercelのデータセンターのグローバルIP",
        "例": "76.76.19.xxx, 76.223.126.xxx（動的に変化）",
        "特徴": [
            "Vercelのサーバーファームから割り当てられたIP",
            "リクエストごとに異なるIPの可能性",
            "明らかに「クラウドサービス」のIPアドレス",
            "大量のトラフィックを生成する可能性があるIP"
        ],
        "APIプロバイダーの反応": "制限や拒否の可能性が高い"
    }
    
    print(f"環境: {production_scenario['環境']}")
    print(f"IPアドレス: {production_scenario['IPアドレス']}")
    print(f"例: {production_scenario['例']}")
    print("特徴:")
    for feature in production_scenario['特徴']:
        print(f"  - {feature}")
    print(f"APIプロバイダーの反応: {production_scenario['APIプロバイダーの反応']}")
    
    print("\n🚨 なぜVercelのIPが問題になるのか？")
    print("=" * 70)
    
    problems = [
        {
            "問題": "クラウドサービスIPの識別",
            "説明": "Yahoo、eBayなどはVercelのIPレンジを「クラウドサービス」として認識",
            "影響": "自動的にレート制限や拒否の対象になる"
        },
        {
            "問題": "大量トラフィックの懸念",
            "説明": "同じIPから多数のアプリケーションがAPIを呼び出す可能性",
            "影響": "APIプロバイダーが予防的に制限をかける"
        },
        {
            "問題": "動的IP変更",
            "説明": "Vercelは負荷分散のためIPアドレスを動的に変更",
            "影響": "IP許可リストに登録しても効果が限定的"
        },
        {
            "問題": "地理的位置の問題",
            "説明": "VercelのIPが日本以外の地域に割り当てられている場合",
            "影響": "地域制限のあるAPIで拒否される"
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"\n{i}. {problem['問題']}")
        print(f"   説明: {problem['説明']}")
        print(f"   影響: {problem['影響']}")
    
    print("\n🔍 実際のIPアドレスの確認方法")
    print("=" * 70)
    
    print("""
作成したテストAPI（/api/test-production）で以下の情報を確認できます：

1. x-forwarded-for: リクエストの転送経路
2. x-real-ip: 実際のクライアントIP
3. cf-connecting-ip: CloudFlare経由の場合の接続IP

これらの値を見ることで、実際にどのIPアドレスから
外部APIにリクエストが送信されているかが分かります。
""")
    
    print("\n📊 IPアドレス別の制限パターン")
    print("=" * 70)
    
    ip_patterns = [
        {
            "IPタイプ": "個人/企業IP",
            "例": "203.104.209.xxx",
            "Yahoo API": "✅ 通常受け入れ",
            "eBay API": "✅ 通常受け入れ",
            "Mercari": "✅ 通常受け入れ",
            "制限理由": "なし"
        },
        {
            "IPタイプ": "AWS IP",
            "例": "52.xxx.xxx.xxx",
            "Yahoo API": "⚠️ レート制限",
            "eBay API": "❌ 拒否の可能性",
            "Mercari": "❌ 高確率で拒否",
            "制限理由": "クラウドサービス検出"
        },
        {
            "IPタイプ": "Vercel IP",
            "例": "76.76.19.xxx",
            "Yahoo API": "❌ 拒否",
            "eBay API": "❌ 拒否",
            "Mercari": "❌ 拒否",
            "制限理由": "Serverless/CDN検出"
        },
        {
            "IPタイプ": "Google Cloud IP",
            "例": "35.xxx.xxx.xxx",
            "Yahoo API": "⚠️ レート制限",
            "eBay API": "⚠️ レート制限",
            "Mercari": "❌ 拒否の可能性",
            "制限理由": "クラウドサービス検出"
        }
    ]
    
    print(f"{'IPタイプ':<15} {'Yahoo API':<12} {'eBay API':<12} {'Mercari':<12} {'制限理由'}")
    print("-" * 70)
    for pattern in ip_patterns:
        print(f"{pattern['IPタイプ']:<15} {pattern['Yahoo API']:<12} {pattern['eBay API']:<12} {pattern['Mercari']:<12} {pattern['制限理由']}")
    
    print("\n💡 解決策")
    print("=" * 70)
    
    solutions = [
        {
            "方法": "プロキシサービス利用",
            "説明": "住宅用IPを提供するプロキシサービス経由でAPIを呼び出し",
            "メリット": "個人IPとして認識される",
            "デメリット": "追加コストとレイテンシ"
        },
        {
            "方法": "専用サーバー利用",
            "説明": "VPSや専用サーバーで固定IPを取得",
            "メリット": "IP許可リストに登録可能",
            "デメリット": "サーバー管理の複雑さ"
        },
        {
            "方法": "APIプロバイダーとの直接交渉",
            "説明": "Yahoo、eBayに商用利用として申請",
            "メリット": "公式にIP制限を解除",
            "デメリット": "審査と承認が必要"
        },
        {
            "方法": "代替APIサービス利用",
            "説明": "RapidAPIなどの仲介サービス利用",
            "メリット": "IP制限を回避",
            "デメリット": "追加コストと機能制限"
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n{i}. {solution['方法']}")
        print(f"   説明: {solution['説明']}")
        print(f"   メリット: {solution['メリット']}")
        print(f"   デメリット: {solution['デメリット']}")
    
    return ip_patterns, solutions

def create_ip_detection_script():
    """IPアドレス検出用のスクリプトを作成"""
    
    script = '''
import requests
import json

def detect_current_ip():
    """現在のIPアドレスを検出"""
    
    services = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
        "https://api.myip.com"
    ]
    
    print("🔍 現在のIPアドレス検出")
    print("=" * 40)
    
    for service in services:
        try:
            response = requests.get(service, timeout=10)
            if response.status_code == 200:
                data = response.json()
                ip = data.get('ip') or data.get('origin')
                print(f"サービス: {service}")
                print(f"IPアドレス: {ip}")
                
                # IP情報の詳細取得
                ip_info_url = f"http://ip-api.com/json/{ip}"
                info_response = requests.get(ip_info_url, timeout=10)
                if info_response.status_code == 200:
                    info = info_response.json()
                    print(f"国: {info.get('country')}")
                    print(f"地域: {info.get('regionName')}")
                    print(f"都市: {info.get('city')}")
                    print(f"ISP: {info.get('isp')}")
                    print(f"組織: {info.get('org')}")
                print("-" * 40)
                break
                
        except Exception as e:
            print(f"エラー: {service} - {str(e)}")

if __name__ == "__main__":
    detect_current_ip()
'''
    
    print("\n🔍 IPアドレス検出スクリプト")
    print("=" * 70)
    print("以下のスクリプトで現在のIPアドレスを確認できます:")
    print(script)

if __name__ == "__main__":
    ip_patterns, solutions = explain_api_request_ip()
    create_ip_detection_script()
    
    print(f"\n🎯 結論: Vercelのようなクラウドサービスから外部APIを呼び出すと")
    print(f"IPアドレスベースの制限により拒否される可能性が高いです。")
