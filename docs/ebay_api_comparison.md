# Marketplace Insights API と代替実装の比較

eBayのMarketplace Insights APIと代替実装（Finding API）には、いくつかの重要な違いがあります。この文書では、両者の違いを詳細に説明します。

## 1. データの鮮度と範囲

### Marketplace Insights API

- **データ範囲**: 過去90日間の売却データを提供
- **データの鮮度**: リアルタイムに近い更新（通常24時間以内）
- **地域カバレッジ**: 複数の国際マーケットプレイスをカバー
- **集計データ**: 90日間の集計データ（平均価格、中央値など）を直接提供

### Finding API（代替実装）

- **データ範囲**: 過去30日間の売却データが中心（最大90日まで可能だが制限あり）
- **データの鮮度**: やや遅延がある場合がある（最大48時間）
- **地域カバレッジ**: 主要マーケットプレイスのみ
- **集計データ**: 自前で計算する必要がある（APIは生データのみ提供）

## 2. 提供される情報の詳細さ

### Marketplace Insights API

- **価格情報**: 売却価格、配送料、税金などの詳細な内訳
- **売却状況**: 正確な売却日時、数量、購入オプション
- **商品詳細**: 詳細な商品情報（コンディション、カテゴリなど）
- **売主情報**: 売主の詳細情報（評価、販売履歴など）
- **統計情報**: 価格分布、売却頻度などの統計データ

### Finding API（代替実装）

- **価格情報**: 基本的な売却価格のみ（内訳は限定的）
- **売却状況**: 売却完了日のみ（正確な時間は提供されない場合がある）
- **商品詳細**: 基本的な商品情報のみ
- **売主情報**: 限定的な情報のみ
- **統計情報**: 提供されない（自前で計算する必要がある）

## 3. API構造と使いやすさ

### Marketplace Insights API

- **API形式**: RESTful API（JSON形式）
- **認証**: OAuth 2.0（アプリケーションアクセストークン）
- **レスポンス構造**: 一貫性のある構造化されたJSONレスポンス
- **ページネーション**: 標準的なページネーション（offset/limit）
- **フィルタリング**: 豊富なフィルタリングオプション
- **ドキュメント**: 詳細なドキュメントと例

### Finding API（代替実装）

- **API形式**: XML形式のSOAP API（レガシー）
- **認証**: アプリケーションキー（App ID）
- **レスポンス構造**: 複雑なXML構造（パースが難しい）
- **ページネーション**: 独自のページネーション方式
- **フィルタリング**: 限定的なフィルタリングオプション
- **ドキュメント**: やや古いドキュメント

## 4. レート制限と利用コスト

### Marketplace Insights API

- **レート制限**: 比較的厳しい（5,000リクエスト/日程度）
- **アクセス**: 限定リリース（申請と承認が必要）
- **コスト**: 無料（現時点では）
- **使用条件**: より厳格な利用規約

### Finding API（代替実装）

- **レート制限**: やや緩い（5,000～25,000リクエスト/日）
- **アクセス**: 標準的なeBay開発者アカウントで利用可能
- **コスト**: 無料
- **使用条件**: 標準的な利用規約

## 5. データ品質と信頼性

### Marketplace Insights API

- **データ品質**: 高品質（eBayが直接提供する公式データ）
- **完全性**: ほぼすべての売却データを含む
- **一貫性**: 一貫したデータ形式と構造
- **正確性**: 非常に正確（実際の取引データに基づく）

### Finding API（代替実装）

- **データ品質**: やや低い（検索結果ベース）
- **完全性**: 一部の売却データが欠落している可能性がある
- **一貫性**: データ形式にばらつきがある場合がある
- **正確性**: やや不正確な場合がある（特に古いデータ）

## 6. 実装の複雑さ

### Marketplace Insights API

- **実装の難易度**: 中程度（RESTful APIの標準的な実装）
- **パース処理**: 比較的簡単（JSON）
- **エラーハンドリング**: 標準的なHTTPステータスコードとエラーメッセージ
- **メンテナンス**: 比較的容易（APIの変更は少ない）

### Finding API（代替実装）

- **実装の難易度**: やや高い（XMLパースと複雑なリクエスト構造）
- **パース処理**: 複雑（XML）
- **エラーハンドリング**: 独自のエラーコードと複雑なエラー構造
- **メンテナンス**: やや困難（レガシーAPIのため）

## 7. 具体的な違いの例

### 例1: 売却価格データの取得

**Marketplace Insights API**:
```json
{
  "itemSales": [
    {
      "itemId": "123456789012",
      "title": "Beatles Abbey Road Vinyl LP",
      "price": {
        "value": "45.99",
        "currency": "USD"
      },
      "soldDate": "2023-05-15T14:23:45.000Z",
      "soldQuantity": 1,
      "condition": {
        "conditionId": "3000",
        "conditionDisplayName": "Very Good"
      },
      "seller": {
        "username": "record_store_nyc",
        "feedbackPercentage": "99.8",
        "feedbackScore": 2345
      }
    }
  ],
  "total": 120,
  "aggregations": {
    "averagePrice": {
      "value": "42.50",
      "currency": "USD"
    },
    "medianPrice": {
      "value": "39.99",
      "currency": "USD"
    },
    "priceDistribution": [
      { "range": "0-20", "count": 5 },
      { "range": "20-40", "count": 45 },
      { "range": "40-60", "count": 60 },
      { "range": "60+", "count": 10 }
    ]
  }
}
```

**Finding API（代替実装）**:
```xml
<findCompletedItemsResponse>
  <searchResult count="2">
    <item>
      <itemId>123456789012</itemId>
      <title>Beatles Abbey Road Vinyl LP</title>
      <sellingStatus>
        <currentPrice currencyId="USD">45.99</currentPrice>
        <sellingState>EndedWithSales</sellingState>
      </sellingStatus>
      <listingInfo>
        <endTime>2023-05-15T14:23:45.000Z</endTime>
      </listingInfo>
      <condition>
        <conditionDisplayName>Very Good</conditionDisplayName>
      </condition>
    </item>
    <!-- 他のアイテム -->
  </searchResult>
  <paginationOutput>
    <totalEntries>120</totalEntries>
    <pageNumber>1</pageNumber>
    <entriesPerPage>10</entriesPerPage>
  </paginationOutput>
</findCompletedItemsResponse>
```

### 例2: 検索とフィルタリング

**Marketplace Insights API**:
```
GET /buy/marketplace_insights/v1_beta/item_sales/search?
    q=Beatles+Abbey+Road+Vinyl
    &filter=soldWithin:DAYS_90,
            priceCurrency:USD,
            conditionIds:{1000|1500|2000|2500|3000}
    &sort=soldDate
    &limit=50
```

**Finding API（代替実装）**:
```xml
<findCompletedItemsRequest>
  <keywords>Beatles Abbey Road Vinyl</keywords>
  <itemFilter>
    <name>SoldItemsOnly</name>
    <value>true</value>
  </itemFilter>
  <itemFilter>
    <name>Currency</name>
    <value>USD</value>
  </itemFilter>
  <sortOrder>EndTimeSoonest</sortOrder>
  <paginationInput>
    <entriesPerPage>50</entriesPerPage>
    <pageNumber>1</pageNumber>
  </paginationInput>
</findCompletedItemsRequest>
```

## 8. 実装上の考慮事項

### Marketplace Insights APIを使用する場合

- **利点**: 高品質なデータ、使いやすいAPI、詳細な情報
- **欠点**: アクセス申請が必要、厳しいレート制限
- **推奨用途**: 本番環境、正確なデータが必要な場合

### Finding APIを使用する場合

- **利点**: すぐに利用可能、標準的なアクセス
- **欠点**: データ品質がやや低い、実装が複雑
- **推奨用途**: 開発・テスト環境、Marketplace Insights APIが利用できない場合の代替手段

## 9. 移行戦略

Marketplace Insights APIへのアクセスが承認されるまでの間、以下の戦略を検討できます：

1. **段階的移行**:
   - 初期段階: Finding APIを使用
   - 中間段階: 両方のAPIを並行して使用し、結果を比較
   - 最終段階: Marketplace Insights APIに完全移行

2. **データ補完**:
   - Finding APIのデータを基本として使用
   - 独自のデータ収集と分析で補完
   - 時系列データを蓄積して傾向分析

3. **ハイブリッドアプローチ**:
   - 現在の出品情報: Browse API（RESTful）
   - 売却履歴データ: Finding API（SOAP）
   - 自前の集計処理: 独自実装

## まとめ

Marketplace Insights APIは、高品質で詳細なデータを提供する最新のAPIですが、アクセスには申請と承認が必要です。一方、Finding APIは即座に利用可能ですが、データ品質と使いやすさの面で劣ります。

プロジェクトの要件と状況に応じて、適切なAPIを選択するか、両方を組み合わせて使用することを検討してください。長期的には、Marketplace Insights APIへのアクセス申請を進めながら、一時的な解決策としてFinding APIを使用するアプローチが推奨されます。
