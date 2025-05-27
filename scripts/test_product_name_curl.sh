#!/bin/bash

# 商品名検索APIのcurlテストスクリプト

BASE_URL="http://localhost:3000"

echo "====================================="
echo "商品名検索API テスト"
echo "====================================="
echo ""

# テスト1: Nintendo Switch
echo "テスト1: Nintendo Switch"
echo "------------------------"
curl -s "${BASE_URL}/api/search/product-name?product_name=Nintendo%20Switch&limit=5" | jq '.'
echo ""
echo ""

# テスト2: 日本語商品名
echo "テスト2: サントリー 緑茶 伊右衛門"
echo "------------------------"
curl -s "${BASE_URL}/api/search/product-name?product_name=%E3%82%B5%E3%83%B3%E3%83%88%E3%83%AA%E3%83%BC%20%E7%B7%91%E8%8C%B6%20%E4%BC%8A%E5%8F%B3%E8%A1%9B%E9%96%80&limit=5" | jq '.'
echo ""
echo ""

# テスト3: POSTメソッド
echo "テスト3: POST メソッドテスト (iPhone 15 Pro)"
echo "------------------------"
curl -s -X POST "${BASE_URL}/api/search/product-name" \
  -H "Content-Type: application/json" \
  -d '{"product_name": "iPhone 15 Pro", "limit": 5}' | jq '.'
echo ""

echo "====================================="
echo "テスト完了"
echo "====================================="