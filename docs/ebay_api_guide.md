# eBay API利用ガイド

## Marketplace Insights APIについて

eBayのMarketplace Insights API（`/buy/marketplace_insights/v1_beta`）は、過去90日間の売却データを取得できる強力なAPIですが、限定リリースであり、通常のアプリケーションキーでは利用できません。以下に申請方法と代替手段を説明します。

## 申請方法

### 1. Production Keysetの有効化

ユーザーデータ削除通知（Marketplace deletion/account closure notification）に対応するためのWebhookを設定する必要があります：

#### Webhook設定手順

1. **Webhookエンドポイントの準備**
   - HTTPSエンドポイント（例：`https://your-domain.com/ebay/webhook`）を用意
   - GETリクエストでチャレンジコードを処理
   - POSTリクエストで削除通知を受信

2. **チャレンジコード処理の実装**
   ```python
   import hashlib
   
   def handle_challenge(challenge_code, verification_token, endpoint_url):
       # 3つの値を連結
       combined = challenge_code + verification_token + endpoint_url
       # SHA-256ハッシュを計算
       hash_value = hashlib.sha256(combined.encode()).hexdigest()
       # レスポンスを返す
       return {"challengeResponse": hash_value}
   ```

3. **eBay開発者ポータルでの設定**
   - Application Keysページで該当App IDの「Notifications」リンクをクリック
   - メールアドレスを入力
   - エンドポイントURLと検証トークン（32～80文字）を入力
   - 「Save」をクリック
   - テスト通知を受けて動作確認

### 2. Marketplace Insights APIへのアクセス申請

Production Keysetが有効化された後、以下の手順でMarketplace Insights APIへのアクセスを申請します：

1. [eBay開発者ポータル](https://developer.ebay.com/)にログイン
2. 「Support」タブを選択
3. 「Contact Us」をクリック
4. 「API Technical Support」を選択
5. 以下の情報を含めて申請：
   - アプリケーション名
   - アプリケーションの目的
   - Marketplace Insights APIの利用目的
   - 予想されるAPI呼び出し頻度

申請後、eBayのチームによる審査があり、承認されるとAPIにアクセスできるようになります。審査には通常1～2週間かかります。

## 代替手段

Marketplace Insights APIが利用できない場合や申請が承認されるまでの間、以下の代替手段があります：

### 1. Finding APIの`findCompletedItems`

Finding API（`/services/search/FindingService/v1`）の`findCompletedItems`操作を使用して、過去の売却データを取得できます。

```python
def search_completed_items(keyword, sold_only=True):
    endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"
    headers = {
        "X-EBAY-SOA-SECURITY-APPNAME": app_id,
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
        "Content-Type": "application/xml"
    }
    
    # XMLリクエストを構築
    xml_request = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <findCompletedItemsRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
      <keywords>{keyword}</keywords>
      <itemFilter>
        <name>SoldItemsOnly</name>
        <value>{str(sold_only).lower()}</value>
      </itemFilter>
      <sortOrder>EndTimeSoonest</sortOrder>
      <paginationInput>
        <entriesPerPage>100</entriesPerPage>
        <pageNumber>1</pageNumber>
      </paginationInput>
    </findCompletedItemsRequest>
    """
    
    response = requests.post(endpoint, headers=headers, data=xml_request)
    # XMLレスポンスをパース
    # ...
    
    return results
```

### 2. eBay公式サイトのスクレイピング（非推奨）

**注意**: eBayの利用規約ではスクレイピングは禁止されています。これはあくまで情報提供のみを目的としています。

eBayの「Sold Items」検索結果ページをスクレイピングする方法もありますが、以下の理由から推奨されません：

- eBayの利用規約違反になる可能性がある
- ページ構造の変更に弱い
- IPブロックなどのリスクがある

### 3. 公式APIの組み合わせ

Browse APIとFinding APIを組み合わせて、現在の出品情報と一部の売却情報を取得する方法もあります：

1. Browse API（`/buy/browse/v1`）で現在の出品情報を取得
2. Finding APIで最近の出品情報を取得
3. 独自のデータベースで時系列データを蓄積し、売却パターンを分析

## 実装例の修正

現在の`EbayClient`クラスをMarketplace Insights APIが利用できない場合に対応するよう修正するには：

```python
def search_sold_items_alternative(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Finding APIを使用して売却済み商品を検索する代替メソッド
    """
    # Finding APIのエンドポイント
    endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"
    
    headers = {
        "X-EBAY-SOA-SECURITY-APPNAME": self.app_id,
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
        "Content-Type": "application/xml"
    }
    
    # XMLリクエストを構築
    xml_request = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <findCompletedItemsRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
      <keywords>{keyword}</keywords>
      <itemFilter>
        <name>SoldItemsOnly</name>
        <value>true</value>
      </itemFilter>
      <sortOrder>EndTimeSoonest</sortOrder>
      <paginationInput>
        <entriesPerPage>{limit}</entriesPerPage>
        <pageNumber>1</pageNumber>
      </paginationInput>
    </findCompletedItemsRequest>
    """
    
    try:
        response = requests.post(endpoint, headers=headers, data=xml_request)
        response.raise_for_status()
        
        # XMLレスポンスをパース
        # ここでは簡略化のためにlxmlを使用
        from lxml import etree
        root = etree.fromstring(response.content)
        
        # 名前空間を定義
        ns = {"ns": "http://www.ebay.com/marketplace/search/v1/services"}
        
        results = []
        items = root.xpath("//ns:searchResult/ns:item", namespaces=ns)
        
        for item in items:
            item_id = item.xpath("ns:itemId/text()", namespaces=ns)[0]
            title = item.xpath("ns:title/text()", namespaces=ns)[0]
            
            # 価格情報を取得
            price_elem = item.xpath("ns:sellingStatus/ns:currentPrice", namespaces=ns)[0]
            price_value = float(price_elem.text)
            currency = price_elem.get("currencyId")
            
            # 終了日時を取得
            end_time = item.xpath("ns:listingInfo/ns:endTime/text()", namespaces=ns)[0]
            
            # URL情報を取得
            url = item.xpath("ns:viewItemURL/text()", namespaces=ns)[0]
            
            # 画像URLを取得
            image_url = item.xpath("ns:galleryURL/text()", namespaces=ns)[0] if item.xpath("ns:galleryURL", namespaces=ns) else ""
            
            result = {
                "search_term": keyword,
                "item_id": item_id,
                "title": title,
                "sold_price": price_value,
                "currency": currency,
                "sold_date": end_time,
                "sold_quantity": 1,  # 詳細情報がないため1と仮定
                "condition": "",  # 詳細情報の取得が必要
                "url": url,
                "image_url": image_url,
                "seller": ""  # 詳細情報の取得が必要
            }
            
            results.append(result)
        
        return results
    except Exception as e:
        print(f"Error searching sold items for '{keyword}' using alternative method: {str(e)}")
        return []
```

## まとめ

1. **最適な方法**: Marketplace Insights APIへのアクセス申請
   - Webhook設定で通知を受け取れるようにする
   - eBayサポートに申請を行う

2. **代替方法**: Finding APIの`findCompletedItems`
   - 機能は限定的だが、基本的な売却データは取得可能
   - 既存のアプリケーションキーで利用可能

3. **長期的な解決策**:
   - Marketplace Insights APIの申請を進めながら、一時的に代替方法を使用
   - 独自のデータベースで時系列データを蓄積し、分析機能を強化
