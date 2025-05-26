#!/usr/bin/env python3
"""
視覚スクレイピングのテストスクリプト
"""
import os
import sys

# 環境変数の確認
print("=== 環境変数チェック ===")
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OPENAI_API_KEY: 設定済み (長さ: {len(openai_key)})")
else:
    print("❌ OPENAI_API_KEY: 未設定")

# OpenAIライブラリのインポートテスト
print("\n=== OpenAIライブラリテスト ===")
try:
    from openai import OpenAI
    print("✅ OpenAIライブラリ: インポート成功")
    
    if openai_key:
        client = OpenAI(api_key=openai_key)
        print("✅ OpenAIクライアント: 初期化成功")
except Exception as e:
    print(f"❌ OpenAIライブラリエラー: {e}")

# Seleniumのテスト
print("\n=== Seleniumテスト ===")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    print("✅ Selenium: インポート成功")
    
    # ヘッドレスでChromeを起動
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome Driver: 起動成功")
        driver.quit()
    except Exception as e:
        print(f"⚠️ Chrome Driver起動エラー: {e}")
        print("   代替方法を使用します")
        
except Exception as e:
    print(f"❌ Seleniumエラー: {e}")

# 視覚スクレイパーのテスト
print("\n=== 視覚スクレイパーテスト ===")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from src.visual_scraper import MercariVisualScraper, OpenAIVisionAnalyzer
    print("✅ 視覚スクレイパーモジュール: インポート成功")
    
    # AI解析器の初期化
    if openai_key:
        analyzer = OpenAIVisionAnalyzer()
        print("✅ OpenAI Vision Analyzer: 初期化成功")
        
        # 簡単なテスト
        scraper = MercariVisualScraper(ai_analyzer=analyzer, headless=True, save_screenshots=True)
        print("✅ Mercari Visual Scraper: 初期化成功")
    else:
        print("⚠️ OpenAI APIキーが未設定のため、AI解析はスキップします")
        
except Exception as e:
    print(f"❌ 視覚スクレイパーエラー: {e}")
    import traceback
    traceback.print_exc()

print("\n=== テスト完了 ===")
print("問題がある場合は以下を確認してください：")
print("1. OpenAI APIキーが.envファイルに設定されているか")
print("2. Chrome/Chromiumがインストールされているか")
print("3. 必要なPythonパッケージがインストールされているか")