#!/usr/bin/env python3
"""
Supabase直接接続テスト
"""
import requests
import os
from supabase import create_client, Client

def test_direct_connection():
    """Supabaseへの直接接続をテスト"""
    print("=== Direct Supabase Connection Test ===\n")
    
    # 環境変数から取得
    url = "https://ggvuuixcswldxfeygxvy.supabase.co"
    anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdndnV1aXhjc3dsZHhmZXlneHZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczMTcxMzAsImV4cCI6MjA2Mjg5MzEzMH0.s-P9q19IqqZDotGeZlrbsBcpHFGxbfH_okZ78MpjdR8"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdndnV1aXhjc3dsZHhmZXlneHZ5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzMxNzEzMCwiZXhwIjoyMDYyODkzMTMwfQ.fkFZinlf1e8YTM8QDlzFap0dOmh_lIH3ma8n1cLANrQ"
    
    print(f"URL: {url}")
    print(f"Using service key\n")
    
    # REST APIテスト
    print("📍 Testing REST API directly...")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
    
    # ヘルスチェック
    try:
        response = requests.get(f"{url}/rest/v1/", headers=headers)
        print(f"Health check status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ REST API error: {str(e)}")
    
    # Pythonクライアントテスト
    print("\n📍 Testing Python client...")
    try:
        supabase: Client = create_client(url, service_key)
        print("✅ Client created successfully")
        
        # テーブル一覧を取得
        print("\n📍 Checking available tables...")
        try:
            # search_tasksテーブルをチェック
            result = supabase.table('search_tasks').select('*').limit(1).execute()
            print("✅ search_tasks table exists")
        except Exception as e:
            print(f"❌ search_tasks table error: {str(e)}")
            
        try:
            # search_resultsテーブルをチェック
            result = supabase.table('search_results').select('*').limit(1).execute()
            print("✅ search_results table exists")
        except Exception as e:
            print(f"❌ search_results table error: {str(e)}")
            
    except Exception as e:
        print(f"❌ Client creation error: {str(e)}")
        print("\nPossible issues:")
        print("1. Supabase project might be paused")
        print("2. Network connectivity issues")
        print("3. Invalid API keys")

if __name__ == "__main__":
    test_direct_connection()