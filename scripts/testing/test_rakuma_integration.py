#!/usr/bin/env python3
"""
Rakuma統合テストスクリプト
"""

import sys
import requests
import json
import time
from datetime import datetime

# 環境設定
BASE_URL = "http://localhost:3000"  # ローカル環境
# BASE_URL = "https://buy-records.vercel.app"  # 本番環境

def test_rakuma_search(query="レコード", limit=5):
    """Rakuma API エンドポイントをテスト"""
    print(f"\n=== Rakuma検索テスト ===")
    print(f"検索クエリ: {query}")
    print(f"取得件数: {limit}")
    
    # APIエンドポイント
    url = f"{BASE_URL}/api/search/rakuma"
    params = {
        "query": query,
        "limit": limit
    }
    
    try:
        # リクエスト送信
        print(f"\nリクエスト送信中...")
        start_time = time.time()
        response = requests.get(url, params=params, timeout=60)
        elapsed_time = time.time() - start_time
        
        print(f"レスポンス時間: {elapsed_time:.2f}秒")
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n=== 検索結果 ===")
            print(f"成功: {data.get('success', False)}")
            print(f"プラットフォーム: {data.get('platform', 'N/A')}")
            print(f"検索クエリ: {data.get('query', 'N/A')}")
            print(f"取得件数: {data.get('total_results', 0)}")
            print(f"データソース: {data.get('data_source', 'N/A')}")
            print(f"スクレイピング方法: {data.get('scraping_method', 'N/A')}")
            
            if data.get('warning'):
                print(f"警告: {data['warning']}")
            
            if data.get('error'):
                print(f"エラー: {data['error']}")
            
            # 結果の詳細表示
            results = data.get('results', [])
            if results:
                print(f"\n=== 商品一覧 (最初の3件) ===")
                for i, item in enumerate(results[:3]):
                    print(f"\n--- 商品 {i+1} ---")
                    print(f"タイトル: {item.get('title', 'N/A')}")
                    print(f"価格: ¥{item.get('price', 0):,}" if isinstance(item.get('price'), (int, float)) else f"価格: {item.get('price', 'N/A')}")
                    print(f"送料: {item.get('shipping_fee', 'N/A')}")
                    print(f"合計: ¥{item.get('total_price', 0):,}")
                    print(f"商品状態: {item.get('condition', 'N/A')}")
                    print(f"出品者: {item.get('seller_name', item.get('store_name', 'N/A'))}")
                    print(f"URL: {item.get('url', 'N/A')}")
                    print(f"画像: {item.get('image_url', 'N/A')[:50]}...")
            else:
                print("\n商品が見つかりませんでした。")
            
            # メタデータの表示
            metadata = data.get('metadata')
            if metadata:
                print(f"\n=== メタデータ ===")
                print(json.dumps(metadata, ensure_ascii=False, indent=2))
            
            return True
            
        else:
            print(f"エラー: HTTPステータス {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("エラー: リクエストがタイムアウトしました")
        return False
    except requests.exceptions.ConnectionError:
        print("エラー: サーバーに接続できません")
        print(f"サーバーが起動していることを確認してください: {BASE_URL}")
        return False
    except Exception as e:
        print(f"エラー: {str(e)}")
        return False


def test_all_platforms_with_rakuma(query="レコード", limit=5):
    """Rakumaを含む全プラットフォーム統合検索をテスト"""
    print(f"\n=== 全プラットフォーム統合検索テスト (Rakuma含む) ===")
    print(f"検索クエリ: {query}")
    print(f"取得件数: {limit}")
    
    # APIエンドポイント
    url = f"{BASE_URL}/api/search/all"
    params = {
        "query": query,
        "limit": limit
    }
    
    try:
        # リクエスト送信
        print(f"\nリクエスト送信中...")
        start_time = time.time()
        response = requests.get(url, params=params, timeout=90)
        elapsed_time = time.time() - start_time
        
        print(f"レスポンス時間: {elapsed_time:.2f}秒")
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n=== 統合検索結果 ===")
            print(f"成功: {data.get('success', False)}")
            print(f"総結果数: {data.get('total_results', 0)}")
            print(f"検索プラットフォーム数: {data.get('platforms_searched', 0)}")
            
            # プラットフォーム別の結果
            platforms = data.get('platforms', {})
            print(f"\n=== プラットフォーム別結果 ===")
            for platform_name, platform_results in platforms.items():
                print(f"{platform_name}: {len(platform_results)}件")
            
            # Rakumaの結果を確認
            rakuma_results = platforms.get('rakuma', [])
            if rakuma_results:
                print(f"\n=== Rakuma検索結果 (最初の2件) ===")
                for i, item in enumerate(rakuma_results[:2]):
                    print(f"\n--- 商品 {i+1} ---")
                    print(f"タイトル: {item.get('title', 'N/A')}")
                    print(f"価格: ¥{item.get('price', 0):,}")
                    print(f"URL: {item.get('url', 'N/A')}")
            else:
                print("\nRakumaの結果がありませんでした。")
            
            # エラー情報
            errors = data.get('errors', [])
            if errors:
                print(f"\n=== エラー ===")
                for error in errors:
                    print(f"- {error}")
            
            return True
            
        else:
            print(f"エラー: HTTPステータス {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"エラー: {str(e)}")
        return False


def main():
    """メイン関数"""
    print(f"Rakuma統合テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト環境: {BASE_URL}")
    
    # コマンドライン引数の処理
    query = sys.argv[1] if len(sys.argv) > 1 else "レコード"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # 個別テスト
    success1 = test_rakuma_search(query, limit)
    
    # 少し待機
    time.sleep(2)
    
    # 統合テスト
    success2 = test_all_platforms_with_rakuma(query, limit)
    
    # 結果サマリー
    print(f"\n=== テスト結果サマリー ===")
    print(f"Rakuma個別検索: {'成功' if success1 else '失敗'}")
    print(f"統合検索（Rakuma含む）: {'成功' if success2 else '失敗'}")
    print(f"総合結果: {'すべて成功' if success1 and success2 else '一部失敗'}")
    
    return 0 if success1 and success2 else 1


if __name__ == "__main__":
    sys.exit(main())