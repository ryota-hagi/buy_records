#!/usr/bin/env python3
"""
統合検索結果の詳細分析スクリプト
"""
import json
import sys

def analyze_unified_search_results(filename='unified_search_result.json'):
    # 結果ファイルを読み込み
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=== 統合検索エンジン動作確認レポート ===')
    print(f'検索クエリ: {data.get("query", "N/A")}')
    print(f'検索成功: {data.get("success", False)}')
    print(f'検索時刻: {data.get("timestamp", "N/A")}')
    print()

    # プラットフォーム別の結果を集計
    print('=== プラットフォーム別取得データ ===')
    platforms = data.get('platforms', {})
    platform_summary = {}

    for platform, items in platforms.items():
        if items:
            platform_summary[platform] = {
                'count': len(items),
                'min_price': min(item.get('price', 0) for item in items),
                'max_price': max(item.get('price', 0) for item in items),
                'avg_price': sum(item.get('price', 0) for item in items) / len(items),
                'sample_items': items[:3]  # 最初の3件をサンプルとして保存
            }

    # 各プラットフォームの詳細
    total_platform_items = 0
    for platform, summary in platform_summary.items():
        total_platform_items += summary['count']
        print(f'\n【{platform.upper()}】')
        print(f'  取得件数: {summary["count"]}件')
        print(f'  価格範囲: ¥{summary["min_price"]:,} - ¥{summary["max_price"]:,}')
        print(f'  平均価格: ¥{summary["avg_price"]:,.0f}')
        print(f'  サンプル商品:')
        for i, item in enumerate(summary["sample_items"], 1):
            print(f'    {i}. {item.get("title", "タイトル不明")}')
            print(f'       価格: ¥{item.get("price", 0):,}')
            print(f'       状態: {item.get("condition", "不明")}')
            print(f'       URL: {item.get("url", "URL不明")[:60]}...')

    # メタデータの確認
    print('\n=== スクレイピング方法とコスト ===')
    metadata = data.get('platform_metadata', {})
    for platform, meta in metadata.items():
        print(f'{platform}:')
        print(f'  方法: {meta.get("scraping_method", "N/A")}')
        print(f'  データソース: {meta.get("data_source", "N/A")}')
        print(f'  取得結果: {meta.get("total_results", "N/A")}件')

    # コストサマリー
    cost_summary = data.get('cost_summary', {})
    print(f'\n総推定コスト: ${cost_summary.get("total_estimated_cost", 0):.4f} {cost_summary.get("currency", "USD")}')
    
    if cost_summary.get('details'):
        details = cost_summary['details']
        print(f'  スクリーンショット数: {details.get("screenshots", 0)}')
        print(f'  API呼び出し数: {details.get("api_calls", 0)}')

    # 統合結果（最安値TOP10）
    print('\n=== 統合結果（全プラットフォーム価格順TOP10） ===')
    all_results = data.get('results', [])
    print(f'総取得件数: {data.get("total_results", 0)}件')
    print(f'プラットフォーム別合計: {total_platform_items}件')
    print(f'表示件数: {len(all_results)}件')

    for i, item in enumerate(all_results[:10], 1):
        print(f'\n{i}. [{item.get("platform", "不明").upper()}] {item.get("title", "タイトル不明")}')
        print(f'   価格: ¥{item.get("price", 0):,}')
        if item.get('shipping_fee', 0) > 0:
            print(f'   送料: ¥{item.get("shipping_fee", 0):,}')
        print(f'   合計: ¥{item.get("total_price", item.get("price", 0)):,}')
        print(f'   状態: {item.get("condition", "不明")}')
        print(f'   販売者: {item.get("store_name", item.get("seller_name", "不明"))}')
        print(f'   URL: {item.get("url", "不明")}')

    # エラー情報
    errors = data.get('errors', [])
    if errors:
        print('\n=== エラー情報 ===')
        for error in errors:
            print(f'  - {error}')
    
    # 最終統計
    print('\n=== 最終統計 ===')
    print(f'検索プラットフォーム数: {data.get("platforms_searched", 0)}')
    print(f'成功したプラットフォーム: {len(platform_summary)}')
    print(f'失敗したプラットフォーム: {data.get("platforms_searched", 0) - len(platform_summary)}')
    
    # プラットフォーム別の割合
    if total_platform_items > 0:
        print('\nプラットフォーム別取得割合:')
        for platform, summary in platform_summary.items():
            percentage = (summary['count'] / total_platform_items) * 100
            print(f'  {platform}: {percentage:.1f}% ({summary["count"]}/{total_platform_items}件)')

if __name__ == '__main__':
    analyze_unified_search_results()