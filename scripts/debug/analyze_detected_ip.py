#!/usr/bin/env python3
"""
検出されたIPアドレス 216.198.79.1 の詳細分析
"""

import requests
import json

def analyze_ip_details():
    """検出されたIPアドレスの詳細を分析"""
    
    detected_ip = "216.198.79.1"
    secondary_ip = "64.29.17.1"
    
    print("🔍 検出されたIPアドレスの詳細分析")
    print("=" * 60)
    print(f"プライマリIP: {detected_ip}")
    print(f"セカンダリIP: {secondary_ip}")
    print()
    
    # 複数のIPアドレス情報サービスで確認
    ip_services = [
        {
            "name": "ipinfo.io",
            "url": f"https://ipinfo.io/{detected_ip}/json",
            "fields": ["ip", "city", "region", "country", "org", "postal", "timezone"]
        },
        {
            "name": "ip-api.com",
            "url": f"http://ip-api.com/json/{detected_ip}",
            "fields": ["query", "city", "regionName", "country", "isp", "org", "as"]
        }
    ]
    
    for service in ip_services:
        print(f"📊 {service['name']} による分析")
        print("-" * 40)
        
        try:
            response = requests.get(service['url'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ 取得成功")
                for field in service['fields']:
                    value = data.get(field, 'N/A')
                    print(f"   {field}: {value}")
                
                # 特別な分析
                if service['name'] == 'ip-api.com':
                    isp = str(data.get('isp', '')).lower()
                    org = str(data.get('org', '')).lower()
                    as_info = str(data.get('as', '')).lower()
                    
                    print(f"\n🔍 サービス判定:")
                    
                    # Vercel/CloudFlareの判定
                    if any(keyword in text for text in [isp, org, as_info] 
                          for keyword in ['vercel', 'cloudflare', 'cf']):
                        print(f"   🎯 Vercel/CloudFlare関連のIPアドレス")
                        restriction_level = "高"
                    # その他のクラウドサービス判定
                    elif any(keyword in text for text in [isp, org, as_info] 
                            for keyword in ['amazon', 'aws', 'google', 'microsoft', 'azure']):
                        print(f"   ⚠️  その他のクラウドサービス")
                        restriction_level = "中〜高"
                    # CDN/ホスティングサービス判定
                    elif any(keyword in text for text in [isp, org, as_info] 
                            for keyword in ['hosting', 'cdn', 'datacenter', 'server']):
                        print(f"   📡 ホスティング/CDNサービス")
                        restriction_level = "中"
                    else:
                        print(f"   🏠 一般的なISP/企業IP")
                        restriction_level = "低"
                    
                    print(f"   制限レベル: {restriction_level}")
                
            else:
                print(f"❌ 取得失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
        
        print()
    
    # セカンダリIPも確認
    print(f"📊 セカンダリIP {secondary_ip} の確認")
    print("-" * 40)
    
    try:
        response = requests.get(f"http://ip-api.com/json/{secondary_ip}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ セカンダリIP情報取得成功")
            print(f"   国: {data.get('country', 'N/A')}")
            print(f"   地域: {data.get('regionName', 'N/A')}")
            print(f"   都市: {data.get('city', 'N/A')}")
            print(f"   ISP: {data.get('isp', 'N/A')}")
            print(f"   組織: {data.get('org', 'N/A')}")
            
        else:
            print(f"❌ セカンダリIP情報取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ セカンダリIP確認エラー: {str(e)}")

def test_api_restrictions():
    """実際のAPI制限をテスト"""
    
    print(f"\n🧪 実際のAPI制限テスト")
    print("=" * 60)
    
    # 簡単なAPIテスト（実際のAPIキーは使わない）
    test_apis = [
        {
            "name": "Yahoo!ショッピング",
            "url": "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
            "params": {"appid": "test", "query": "test"},
            "expected_error": "400 (無効なAPIキー)"
        },
        {
            "name": "eBay Finding",
            "url": "https://svcs.ebay.com/services/search/FindingService/v1",
            "params": {
                "OPERATION-NAME": "findItemsByKeywords",
                "SECURITY-APPNAME": "test",
                "keywords": "test"
            },
            "expected_error": "400/403 (無効なAPIキー)"
        }
    ]
    
    for api in test_apis:
        print(f"🔍 {api['name']} API接続テスト")
        print(f"   URL: {api['url']}")
        
        try:
            response = requests.get(api['url'], params=api['params'], timeout=10)
            
            print(f"   ステータス: {response.status_code}")
            print(f"   期待値: {api['expected_error']}")
            
            if response.status_code == 403:
                print(f"   🚨 IP制限の可能性（403 Forbidden）")
            elif response.status_code == 400:
                print(f"   ✅ IP制限なし（400 Bad Request = APIキー問題）")
            elif response.status_code == 429:
                print(f"   ⚠️  レート制限（429 Too Many Requests）")
            else:
                print(f"   ❓ その他のレスポンス")
                
        except Exception as e:
            print(f"   ❌ 接続エラー: {str(e)}")
        
        print()

def summarize_findings():
    """発見事項をまとめる"""
    
    print(f"🎯 分析結果まとめ")
    print("=" * 60)
    
    findings = [
        "1. 検出されたIPアドレス: 216.198.79.1, 64.29.17.1",
        "2. 初期分析では「一般的なIP」として判定",
        "3. テストAPIが404エラー（デプロイ問題の可能性）",
        "4. DNS解決は正常に動作",
        "5. IPアドレス自体は制限対象外の可能性"
    ]
    
    for finding in findings:
        print(f"   {finding}")
    
    print(f"\n💡 結論")
    print("-" * 30)
    print(f"   • IPアドレス制限が主要原因ではない可能性")
    print(f"   • 環境変数（APIキー）問題が最有力")
    print(f"   • テストAPIの404エラーはデプロイ問題")
    print(f"   • 実際のAPI制限テストが必要")

if __name__ == "__main__":
    analyze_ip_details()
    test_api_restrictions()
    summarize_findings()
