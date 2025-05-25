# モックデータ禁止ガイドライン

## 概要

このプロジェクトでは、実際のプラットフォーム検索による真正なデータ取得を重視しており、モックデータやハードコーディングされた値の使用を禁止しています。

## 基本原則

### 1. 完全なモックデータ禁止
- 偽の商品データ、価格情報、URL等の生成は禁止
- サンプルデータやテストデータの本番コードでの使用禁止
- ハードコーディングされた商品名、JANコード、価格の禁止

### 2. 実データ優先
- 実際のプラットフォームAPI（メルカリ、eBay、Yahoo!等）からのデータ取得
- リアルタイム為替レート（ExchangeRate-API）の使用
- 実際のJANコードルックアップサービスの使用

### 3. 環境別制御
- 本番環境では`NODE_ENV=production`でモックデータを完全無効化
- 開発環境でも可能な限り実データを使用
- テスト環境では限定的なモックデータのみ許可

## 禁止事項

### コード内での禁止事項

```javascript
// ❌ 禁止: モックデータの生成
const mockResults = [
  { title: 'Test Item 1', price: 1000 },
  { title: 'Test Item 2', price: 2000 }
];

// ❌ 禁止: ハードコーディングされた値
const productName = janCode === '4901777300446' ? 'サントリー 緑茶' : '商品';

// ❌ 禁止: 偽のURL生成
const fakeUrl = `https://example.com/item/${itemId}`;
```

```python
# ❌ 禁止: サンプルデータの使用
sample_data = {
    'title': 'Sample Product',
    'price': 1000,
    'url': 'https://test.com/item/123'
}

# ❌ 禁止: ハードコーディングされた商品辞書
PRODUCT_DICT = {
    '4901777300446': 'サントリー 緑茶 伊右衛門',
    '4902370548501': 'Nintendo Switch'
}
```

### ファイル名での禁止事項

- `sample_*.json`
- `mock_*.py`
- `test_data.json`
- `dummy_*.js`

## 推奨事項

### 1. 実データ取得の実装

```python
# ✅ 推奨: 実際のAPI呼び出し
def search_mercari(query, limit=20):
    """実際のメルカリ検索を実行"""
    driver = webdriver.Chrome()
    try:
        # 実際のメルカリサイトにアクセス
        driver.get(f"https://mercari.com/search?keyword={query}")
        # 実際のデータを取得
        return extract_real_data(driver)
    finally:
        driver.quit()
```

### 2. 環境変数の活用

```python
# ✅ 推奨: 環境変数からの設定取得
TEST_JAN_CODE = os.environ.get('TEST_JAN_CODE', '4902370548501')
API_ENDPOINT = os.environ.get('API_ENDPOINT', 'https://api.example.com')
```

### 3. 設定ベースの制御

```python
# ✅ 推奨: 設定による制御
from src.utils.anti_mock_config import validate_search_results

def process_search_results(results, platform):
    # モックデータ検証を自動実行
    validated_results = validate_search_results(results, platform)
    return validated_results
```

## 実装ガイド

### 1. 新機能開発時

1. **実データソースの特定**
   - 使用するプラットフォームのAPI仕様を確認
   - 実際のエンドポイントとレスポンス形式を調査

2. **エラーハンドリングの実装**
   - API呼び出し失敗時の適切な処理
   - フォールバック機能（別プラットフォームへの切り替え等）

3. **データ検証の追加**
   - `anti_mock_config.py`の検証機能を使用
   - 取得データの妥当性チェック

### 2. テスト実装時

```python
# ✅ 推奨: 実際のAPIを使用した統合テスト
def test_ebay_search():
    strategy = EbayStrategy()
    results = strategy.search("Nintendo Switch", limit=3)
    assert len(results) > 0
    assert all('price' in item for item in results)
```

### 3. 設定ファイルの活用

```json
// config/platforms.json
{
  "ebay": {
    "enabled": true,
    "api_endpoint": "https://api.ebay.com/buy/browse/v1",
    "fallback_enabled": true
  },
  "mercari": {
    "enabled": true,
    "scraping_url": "https://mercari.com/search",
    "fallback_enabled": false
  }
}
```

## 監視とチェック

### 1. 自動検証

- `anti_mock_config.py`による実行時チェック
- 本番環境でのモックデータ検出時の自動エラー
- ログによるデータソース追跡

### 2. コードレビューチェックリスト

- [ ] モックデータやサンプルデータが含まれていないか
- [ ] ハードコーディングされた値が使用されていないか
- [ ] 実際のAPI呼び出しが実装されているか
- [ ] エラーハンドリングが適切に実装されているか
- [ ] 環境変数による設定が使用されているか

### 3. 定期監査

- 月次でのコードベース全体のモックデータ検索
- 本番環境ログの監視
- パフォーマンス指標による実データ取得の確認

## 例外処理

### 許可される場合

1. **単体テスト**
   - 外部API依存を排除する必要がある場合
   - モック使用を明示的にコメントで記載

2. **開発環境での一時的使用**
   - API制限回避のための短期間使用
   - 実装完了後は必ず実データに切り替え

3. **フォールバック機能**
   - 全てのAPI呼び出しが失敗した場合の最終手段
   - ユーザーに明確にエラー状況を通知

### 例外使用時の要件

```python
# 例外使用時は必ずコメントで理由を明記
def get_fallback_data():
    """
    例外的なフォールバックデータ
    理由: 全てのAPI呼び出しが失敗した場合の最終手段
    使用条件: 実際のAPI呼び出しが3回連続で失敗した場合のみ
    """
    logger.warning("フォールバックデータを使用しています")
    return {"error": "データ取得に失敗しました"}
```

## 違反時の対応

### 1. 開発時
- コードレビューでの指摘と修正要求
- 実データ取得への実装変更

### 2. 本番環境
- 自動エラー検出とアラート
- 緊急修正とホットフィックスの適用

### 3. 継続的改善
- 違反パターンの分析と防止策の強化
- ガイドラインの更新と周知

## 関連ファイル

- `src/utils/anti_mock_config.py` - モックデータ検証システム
- `src/app/api/search/tasks/route.ts` - 実際の検索エンジン統合
- `scripts/test_*.py` - 実データを使用したテストスクリプト

## 更新履歴

- 2025/05/25: 初版作成
- モックデータ完全禁止ポリシーの策定
- 実データ優先アーキテクチャの確立
