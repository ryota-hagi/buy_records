#!/bin/bash
# 統合検索エンジンのテストスクリプト

echo "=== 統合検索エンジンテスト ==="
echo "検索クエリ: Nintendo Switch"
echo "制限数: 10件"
echo ""

# 統合検索APIを呼び出し
echo "統合検索APIを呼び出し中..."
response=$(curl -s "http://localhost:3000/api/search/all?query=Nintendo+Switch&limit=10")

if [ -z "$response" ]; then
    echo "エラー: レスポンスが空です。サーバーが起動していることを確認してください。"
    exit 1
fi

# 結果を解析
echo "$response" | jq '{
  success: .success,
  total_results: .total_results,
  platforms_searched: .platforms_searched,
  mercari_results: (.platforms.mercari | length),
  yahoo_results: (.platforms.yahoo_shopping | length),
  ebay_results: (.platforms.ebay | length),
  mercari_method: .platform_metadata.mercari.scraping_method,
  mercari_source: .platform_metadata.mercari.data_source,
  cost_summary: .cost_summary
}'

echo ""
echo "=== 最も安い5件の商品 ==="
echo "$response" | jq '.results[:5] | .[] | {
  platform: .platform,
  title: .title,
  price: .price,
  url: .url
}'