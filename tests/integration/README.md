# 統合テストフレームワーク

## 概要
Buy Recordsプロジェクトの新機能開発における統合テストフレームワークです。

## テスト構造

```
tests/
├── integration/
│   ├── search/           # 検索機能テスト
│   │   ├── jan_code_test.py
│   │   ├── product_name_test.py
│   │   ├── image_search_test.py
│   │   └── natural_language_test.py
│   ├── platforms/        # プラットフォーム統合テスト
│   │   ├── ebay_test.py
│   │   ├── mercari_test.py
│   │   ├── yahoo_shopping_test.py
│   │   └── new_platform_test_template.py
│   ├── fixtures/         # テストデータ
│   │   ├── search_requests.json
│   │   ├── expected_results.json
│   │   └── test_images/
│   └── conftest.py      # pytest設定
├── unit/                # 単体テスト
├── e2e/                 # E2Eテスト
└── performance/         # パフォーマンステスト
```

## テスト実行方法

### 全統合テストの実行
```bash
pytest tests/integration -v
```

### 特定の機能テスト
```bash
# 検索機能のみ
pytest tests/integration/search -v

# 特定のプラットフォーム
pytest tests/integration/platforms/ebay_test.py -v
```

### カバレッジ付き実行
```bash
pytest tests/integration --cov=src --cov-report=html
```

## テストフレームワーク設定

### conftest.py
```python
import pytest
import asyncio
from typing import Generator
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv('.env.test')

@pytest.fixture(scope="session")
def event_loop():
    """非同期テスト用のイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_search_request():
    """テスト用検索リクエスト"""
    return {
        "type": "jan_code",
        "query": "4988001531654",
        "platforms": ["ebay", "mercari", "yahoo"],
        "options": {
            "include_sold": True,
            "max_results": 10
        }
    }

@pytest.fixture
def mock_api_responses():
    """APIレスポンスのモック"""
    return {
        "ebay": {"items": [], "total": 0},
        "mercari": {"items": [], "total": 0},
        "yahoo": {"items": [], "total": 0}
    }
```

## 基本テストテンプレート

### 新機能テストテンプレート
```python
import pytest
from src.search.unified_search_engine import UnifiedSearchEngine

class TestNewFeature:
    """新機能の統合テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト前の準備"""
        self.engine = UnifiedSearchEngine()
        yield
        # クリーンアップ処理
    
    def test_basic_functionality(self, test_search_request):
        """基本機能のテスト"""
        result = self.engine.search(test_search_request)
        assert result is not None
        assert "results" in result
        assert len(result["results"]) > 0
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        with pytest.raises(ValueError):
            self.engine.search({"type": "invalid"})
    
    @pytest.mark.parametrize("platform", ["ebay", "mercari", "yahoo"])
    def test_platform_integration(self, platform):
        """プラットフォーム統合テスト"""
        request = {
            "type": "jan_code",
            "query": "test",
            "platforms": [platform]
        }
        result = self.engine.search(request)
        assert platform in result["results"]
```

### プラットフォームテストテンプレート
```python
import pytest
from src.platforms.adapters import PlatformAdapter

class TestNewPlatform:
    """新プラットフォームの統合テスト"""
    
    def test_adapter_initialization(self):
        """アダプター初期化テスト"""
        adapter = PlatformAdapter("new_platform")
        assert adapter.name == "new_platform"
        assert adapter.is_available()
    
    def test_search_functionality(self):
        """検索機能テスト"""
        adapter = PlatformAdapter("new_platform")
        results = adapter.search({
            "type": "product_name",
            "query": "test product"
        })
        assert isinstance(results, list)
    
    def test_rate_limiting(self):
        """レート制限テスト"""
        adapter = PlatformAdapter("new_platform")
        # 複数リクエストを送信
        for _ in range(5):
            adapter.search({"query": "test"})
        # レート制限が適切に機能することを確認
        assert adapter.get_remaining_quota() >= 0
```

## CI/CD統合

### GitHub Actions設定
`.github/workflows/integration-tests.yml`
```yaml
name: Integration Tests

on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/integration/**'
  push:
    branches:
      - develop
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/test
        run: |
          pytest tests/integration -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## モックとスタブ

### プラットフォームAPIモック
```python
# tests/integration/mocks/platform_mocks.py
from unittest.mock import Mock, patch

def mock_ebay_api():
    """eBay APIのモック"""
    mock = Mock()
    mock.search.return_value = {
        "items": [
            {
                "title": "Test Product",
                "price": 1000,
                "currency": "JPY",
                "itemId": "123456"
            }
        ],
        "total": 1
    }
    return mock

def mock_mercari_scraper():
    """Mercariスクレイパーのモック"""
    mock = Mock()
    mock.scrape.return_value = {
        "items": [
            {
                "name": "テスト商品",
                "price": 2000,
                "sold": False,
                "id": "m123456"
            }
        ]
    }
    return mock
```

## パフォーマンステスト

### 負荷テスト
```python
# tests/integration/performance/load_test.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """パフォーマンステスト"""
    
    def test_concurrent_searches(self):
        """並行検索のテスト"""
        engine = UnifiedSearchEngine()
        requests = [
            {"type": "jan_code", "query": f"test{i}"}
            for i in range(10)
        ]
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(engine.search, requests))
        end_time = time.time()
        
        # 全リクエストが10秒以内に完了
        assert end_time - start_time < 10
        # 全リクエストが成功
        assert all(r is not None for r in results)
    
    def test_response_time(self):
        """レスポンス時間のテスト"""
        engine = UnifiedSearchEngine()
        
        times = []
        for _ in range(5):
            start = time.time()
            engine.search({"type": "jan_code", "query": "test"})
            times.append(time.time() - start)
        
        # 平均レスポンス時間が2秒以内
        assert sum(times) / len(times) < 2.0
```

## データ駆動テスト

### テストデータファイル
```json
// tests/integration/fixtures/test_cases.json
{
  "search_tests": [
    {
      "name": "basic_jan_search",
      "request": {
        "type": "jan_code",
        "query": "4988001531654"
      },
      "expected": {
        "min_results": 1,
        "platforms": ["ebay", "mercari", "yahoo"]
      }
    },
    {
      "name": "product_name_search",
      "request": {
        "type": "product_name",
        "query": "Nintendo Switch"
      },
      "expected": {
        "min_results": 5,
        "contains_keywords": ["Nintendo", "Switch"]
      }
    }
  ]
}
```

### データ駆動テストの実装
```python
import json
import pytest

with open("tests/integration/fixtures/test_cases.json") as f:
    test_cases = json.load(f)["search_tests"]

@pytest.mark.parametrize("test_case", test_cases, ids=[tc["name"] for tc in test_cases])
def test_search_scenarios(test_case):
    """データ駆動による検索シナリオテスト"""
    engine = UnifiedSearchEngine()
    result = engine.search(test_case["request"])
    
    # 期待値の検証
    expected = test_case["expected"]
    if "min_results" in expected:
        assert len(result["results"]) >= expected["min_results"]
    
    if "platforms" in expected:
        for platform in expected["platforms"]:
            assert platform in result["results"]
```

## デバッグとログ

### テストログ設定
```python
# tests/integration/conftest.py
import logging

# テスト用ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/integration/test.log'),
        logging.StreamHandler()
    ]
)
```

## 次のステップ

1. 基本的な統合テストを作成
2. CI/CDパイプラインに統合
3. カバレッジ目標（80%以上）を設定
4. パフォーマンステストベースラインを確立