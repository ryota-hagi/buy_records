#!/usr/bin/env python3
"""
buy-records.vercel.app の実際のAPIリクエスト元IPアドレスを特定
"""

import requests
import json
import socket
from datetime import datetime

def detect_vercel_ip():
    """Vercelアプリの実際のIPアドレスを検出"""
    
    print("🔍 buy-records.vercel.app のIPアドレス特定")
    print("=" * 60)
    
    base_url = "https://buy-records.vercel.app"
    
    # 1. テストAPIから情報を取得
    print("1. テストAPIからIP情報を取得")
    print("-" * 40)
    
    try:
        test_url = f"{base_url}/api/test-production"
        response = requests.get(test_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            ip_info = data.get('data', {}).get('ip_info', {})
            
            print(f"✅ テストAPI成功")
            print(f"   x-forwarded-for: {ip_info.get('x_forwarded_for', 'なし')}")
            print(f"   x-real-ip: {ip_info.get('x_real_ip', 'なし')}")
            print(f"   cf-connecting-ip: {ip_info.get('cf_connecting_ip', 'なし')}")
            print(f"   Vercelリージョン: {data.get('data', {}).get('vercel_region', 'なし')}")
            
            # 実際のIPアドレスを特定
            actual_ip = (ip_info.get('x_forwarded_for') or 
                        ip_info.get('x_real_ip') or 
                        ip_info.get('cf_connecting_ip') or 
                        'unknown')
            
            if actual_ip != 'unknown':
                print(f"🎯 検出されたIPアドレス: {actual_ip}")
                return actual_ip
            else:
                print("⚠️  IPアドレスを検出できませんでした")
                
        else:
            print(f"❌ テストAPI失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ テストAPIエラー: {str(e)}")
    
    # 2. DNS解決でVercelのIPを取得
    print("\n2. DNS解決でVercelのIPアドレスを取得")
    print("-" * 40)
    
    try:
        hostname = "buy-records.vercel.app"
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        
        print(f"✅ DNS解決成功")
        print(f"   ホスト名: {hostname}")
        for i, ip in enumerate(ip_addresses, 1):
            print(f"   IPアドレス{i}: {ip}")
            
        if ip_addresses:
            primary_ip = ip_addresses[0]
            print(f"🎯 プライマリIPアドレス: {primary_ip}")
            return primary_ip
            
    except Exception as e:
        print(f"❌ DNS解決エラー: {str(e)}")
    
    # 3. 外部サービスでIPを確認
    print("\n3. 外部サービスでIPアドレス情報を取得")
    print("-" * 40)
    
    external_services = [
        {
            "name": "ipinfo.io",
            "url": "https://ipinfo.io/{ip}/json"
        },
        {
            "name": "ip-api.com", 
            "url": "http://ip-api.com/json/{ip}"
        }
    ]
    
    # DNS解決で取得したIPがある場合、それを使用
    if 'primary_ip' in locals():
        target_ip = primary_ip
        
        for service in external_services:
            try:
                url = service['url'].format(ip=target_ip)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"✅ {service['name']} 成功")
                    print(f"   IPアドレス: {target_ip}")
                    print(f"   国: {data.get('country', 'unknown')}")
                    print(f"   地域: {data.get('region', data.get('regionName', 'unknown'))}")
                    print(f"   都市: {data.get('city', 'unknown')}")
                    print(f"   ISP: {data.get('isp', data.get('org', 'unknown'))}")
                    print(f"   組織: {data.get('org', data.get('as', 'unknown'))}")
                    
                    # Vercelかどうかを判定
                    org_info = str(data.get('org', '')).lower()
                    isp_info = str(data.get('isp', '')).lower()
                    
                    is_vercel = ('vercel' in org_info or 'vercel' in isp_info or
                               'cloudflare' in org_info or 'cloudflare' in isp_info)
                    
                    if is_vercel:
                        print(f"🎯 Vercel/CloudFlareのIPアドレスと確認")
                    else:
                        print(f"⚠️  Vercel以外のIPアドレスの可能性")
                    
                    break
                    
            except Exception as e:
                print(f"❌ {service['name']} エラー: {str(e)}")
    
    return target_ip if 'target_ip' in locals() else None

def analyze_ip_restrictions(ip_address):
    """IPアドレスの制限状況を分析"""
    
    if not ip_address:
        print("\n❌ IPアドレスが特定できないため、制限分析をスキップします")
        return
    
    print(f"\n📊 IPアドレス {ip_address} の制限分析")
    print("=" * 60)
    
    # IPアドレスの範囲を分析
    ip_parts = ip_address.split('.')
    if len(ip_parts) == 4:
        first_octet = int(ip_parts[0])
        second_octet = int(ip_parts[1])
        
        # 既知のクラウドサービスIPレンジ
        cloud_ranges = [
            {"name": "Vercel/CloudFlare", "ranges": ["76.76.0.0/16", "76.223.0.0/16", "104.16.0.0/12"]},
            {"name": "AWS", "ranges": ["52.0.0.0/8", "54.0.0.0/8", "3.0.0.0/8"]},
            {"name": "Google Cloud", "ranges": ["35.0.0.0/8", "34.0.0.0/8"]},
            {"name": "Azure", "ranges": ["20.0.0.0/8", "40.0.0.0/8"]}
        ]
        
        detected_service = None
        for service in cloud_ranges:
            for range_str in service['ranges']:
                network_ip = range_str.split('/')[0]
                network_parts = network_ip.split('.')
                
                if (first_octet == int(network_parts[0]) and 
                    (len(network_parts) < 2 or second_octet == int(network_parts[1]))):
                    detected_service = service['name']
                    break
            if detected_service:
                break
        
        if detected_service:
            print(f"🏷️  検出されたサービス: {detected_service}")
            
            # 制限レベルを判定
            if "Vercel" in detected_service or "CloudFlare" in detected_service:
                restriction_level = "高"
                yahoo_status = "❌ 拒否される可能性が高い"
                ebay_status = "❌ 拒否される可能性が高い"
                mercari_status = "❌ 拒否される可能性が高い"
            elif "AWS" in detected_service:
                restriction_level = "中〜高"
                yahoo_status = "⚠️ レート制限の可能性"
                ebay_status = "❌ 拒否される可能性"
                mercari_status = "❌ 拒否される可能性が高い"
            else:
                restriction_level = "中"
                yahoo_status = "⚠️ レート制限の可能性"
                ebay_status = "⚠️ レート制限の可能性"
                mercari_status = "❌ 拒否される可能性"
                
        else:
            print(f"🏷️  検出されたサービス: 不明（一般的なIP）")
            restriction_level = "低"
            yahoo_status = "✅ 通常受け入れ"
            ebay_status = "✅ 通常受け入れ"
            mercari_status = "✅ 通常受け入れ"
        
        print(f"📈 制限レベル: {restriction_level}")
        print(f"🛒 Yahoo!ショッピングAPI: {yahoo_status}")
        print(f"🛍️  eBay API: {ebay_status}")
        print(f"📦 Mercari API: {mercari_status}")
        
        # 推奨対策
        print(f"\n💡 推奨対策")
        print("-" * 30)
        
        if restriction_level in ["高", "中〜高"]:
            recommendations = [
                "1. プロキシサービスの利用を検討",
                "2. 専用サーバー（VPS）への移行",
                "3. APIプロバイダーとの商用利用申請",
                "4. 代替APIサービス（RapidAPI等）の利用"
            ]
        else:
            recommendations = [
                "1. 環境変数（APIキー）の確認・更新",
                "2. APIリクエストの頻度調整",
                "3. エラーハンドリングの改善"
            ]
        
        for rec in recommendations:
            print(f"   {rec}")

def create_ip_monitoring_script():
    """IP監視用のスクリプトを作成"""
    
    script = f'''
# Vercel IP監視スクリプト
# 定期的にIPアドレスの変化を監視

import requests
import json
from datetime import datetime

def monitor_vercel_ip():
    """Vercel IPアドレスを監視"""
    
    url = "https://buy-records.vercel.app/api/test-production"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            ip_info = data.get('data', {{}}).get('ip_info', {{}})
            
            current_ip = (ip_info.get('x_forwarded_for') or 
                         ip_info.get('x_real_ip') or 
                         'unknown')
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"[{{timestamp}}] Current IP: {{current_ip}}")
            
            # ログファイルに記録
            with open('vercel_ip_log.txt', 'a') as f:
                f.write(f"{{timestamp}},{{current_ip}}\\n")
                
        else:
            print(f"Error: {{response.status_code}}")
            
    except Exception as e:
        print(f"Error: {{str(e)}}")

if __name__ == "__main__":
    monitor_vercel_ip()
'''
    
    print(f"\n🔄 IP監視スクリプト")
    print("=" * 60)
    print("以下のスクリプトでIPアドレスの変化を監視できます:")
    print(script)

def main():
    """メイン実行関数"""
    
    print(f"🚀 buy-records.vercel.app IPアドレス特定開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # IPアドレスを検出
    detected_ip = detect_vercel_ip()
    
    # 制限分析
    analyze_ip_restrictions(detected_ip)
    
    # 監視スクリプト提供
    create_ip_monitoring_script()
    
    print(f"\n🎯 結論")
    print("=" * 60)
    if detected_ip:
        print(f"検出されたIPアドレス: {detected_ip}")
        print(f"このIPアドレスがYahoo、eBay、MercariのAPIリクエスト元として使用されます。")
        print(f"クラウドサービスのIPの場合、API制限の対象となる可能性が高いです。")
    else:
        print(f"IPアドレスの特定に失敗しました。")
        print(f"テストAPIが正常に動作していない可能性があります。")

if __name__ == "__main__":
    main()
