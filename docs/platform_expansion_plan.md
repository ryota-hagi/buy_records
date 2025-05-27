# プラットフォーム拡張計画

## 概要
現在の3プラットフォーム（eBay、メルカリ、Yahoo!ショッピング）から、段階的に対応プラットフォームを拡大します。

## プラットフォーム追加ロードマップ

### Phase A: 国内プラットフォーム拡張（並行開発可能）

#### A-1: ヤフオク!（Yahoo!オークション）
**ブランチ**: `feature/platform-yahoo-auction`
- 既存のYahoo! APIの活用
- オークション特有の価格表示対応
- 即決価格と現在価格の両方を取得

#### A-2: ラクマ（楽天）
**ブランチ**: `feature/platform-rakuma`
- 楽天APIの統合
- 楽天ポイント考慮の価格計算

#### A-3: Amazon Japan
**ブランチ**: `feature/platform-amazon-jp`
- Amazon Product Advertising API
- プライム配送の考慮
- 新品/中古の明確な区別

### Phase B: 海外プラットフォーム拡張

#### B-1: Discogs（音楽特化）
**ブランチ**: `feature/platform-discogs`
- 音楽商品専門の検索最適化
- グレーディング情報の統合
- 国際配送料の計算

#### B-2: Reverb（楽器特化）
**ブランチ**: `feature/platform-reverb`
- 楽器カテゴリの専門検索
- 状態評価の詳細化

#### B-3: StockX（スニーカー/ストリートウェア）
**ブランチ**: `feature/platform-stockx`
- リアルタイム相場情報
- サイズ別価格の対応

### Phase C: 専門プラットフォーム

#### C-1: BOOTH（同人/創作物）
**ブランチ**: `feature/platform-booth`
- pixiv連携
- デジタル/物理商品の区別

#### C-2: BASE
**ブランチ**: `feature/platform-base`
- 個人ショップ検索
- ショップ評価の統合

## プラットフォーム追加の標準化

### 1. プラットフォームアダプターインターフェース

```typescript
// src/platforms/interfaces/platform-adapter.ts
export interface PlatformAdapter {
  name: string;
  code: string;
  supportedSearchTypes: SearchType[];
  supportedRegions: string[];
  
  search(request: SearchRequest): Promise<SearchResult[]>;
  validateCredentials(): Promise<boolean>;
  getApiLimits(): ApiLimits;
}

export interface ApiLimits {
  requestsPerMinute: number;
  requestsPerDay: number;
  maxResultsPerRequest: number;
}
```

### 2. プラットフォーム追加テンプレート

```typescript
// src/platforms/template/platform-template.ts
export class NewPlatformAdapter implements PlatformAdapter {
  name = 'Platform Name';
  code = 'platform_code';
  supportedSearchTypes = [SearchType.PRODUCT_NAME, SearchType.JAN_CODE];
  supportedRegions = ['JP'];
  
  async search(request: SearchRequest): Promise<SearchResult[]> {
    // 実装
  }
  
  async validateCredentials(): Promise<boolean> {
    // API認証確認
  }
  
  getApiLimits(): ApiLimits {
    return {
      requestsPerMinute: 60,
      requestsPerDay: 10000,
      maxResultsPerRequest: 50
    };
  }
}
```

### 3. プラットフォーム設定管理

```typescript
// src/config/platforms.config.ts
export const PLATFORM_CONFIG = {
  ebay: {
    enabled: true,
    apiKey: process.env.EBAY_API_KEY,
    priority: 1,
    searchMethods: ['browse_api', 'finding_api']
  },
  mercari: {
    enabled: true,
    searchMethods: ['dom_scraping', 'visual_ai'],
    priority: 2
  },
  yahoo_shopping: {
    enabled: true,
    apiKey: process.env.YAHOO_API_KEY,
    priority: 3
  },
  // 新規プラットフォーム追加時はここに設定を追加
};
```

## 実装優先順位

### 優先度: 高
1. **ヤフオク!** - Yahoo!との既存統合を活用
2. **Amazon Japan** - 市場シェアが大きい
3. **ラクマ** - メルカリの競合として重要

### 優先度: 中
4. **Discogs** - 音楽ジャンルで必須
5. **BOOTH** - 特定ジャンルで需要高

### 優先度: 低
6. **Reverb** - 楽器特化
7. **StockX** - 特定カテゴリ
8. **BASE** - 小規模ショップ

## プラットフォーム別の技術的課題

### API利用可能
- eBay ✅
- Yahoo!ショッピング ✅
- Amazon Japan
- 楽天/ラクマ
- Discogs

### スクレイピング必要
- メルカリ ✅（実装済み）
- ヤフオク!（一部）
- BOOTH
- BASE

### 認証が複雑
- Amazon（署名付きリクエスト）
- StockX（OAuth2）

## ディレクトリ構造

```
src/
├── platforms/
│   ├── interfaces/
│   │   ├── platform-adapter.ts
│   │   └── platform-config.ts
│   ├── adapters/
│   │   ├── ebay/
│   │   │   ├── ebay.adapter.ts
│   │   │   ├── ebay.config.ts
│   │   │   └── ebay.test.ts
│   │   ├── mercari/
│   │   ├── yahoo-shopping/
│   │   ├── yahoo-auction/
│   │   ├── rakuma/
│   │   ├── amazon-jp/
│   │   └── discogs/
│   ├── registry/
│   │   └── platform-registry.ts
│   └── utils/
│       ├── rate-limiter.ts
│       ├── price-converter.ts
│       └── shipping-calculator.ts
```

## プラットフォーム追加チェックリスト

- [ ] プラットフォームアダプター実装
- [ ] API認証設定
- [ ] 検索メソッド実装
- [ ] 価格正規化処理
- [ ] エラーハンドリング
- [ ] レート制限対応
- [ ] ユニットテスト作成
- [ ] 統合テスト作成
- [ ] ドキュメント作成
- [ ] 環境変数追加

## 並行開発戦略

### チーム編成案

**チーム1: 検索機能拡張**
- 商品名検索
- 画像検索
- 自然言語検索

**チーム2: 国内プラットフォーム**
- ヤフオク!
- ラクマ
- Amazon Japan

**チーム3: 海外・専門プラットフォーム**
- Discogs
- BOOTH
- その他

## マイルストーン（更新版）

### Month 1
- Week 1-2: 検索基盤 + ヤフオク!
- Week 3-4: 商品名検索 + Amazon Japan

### Month 2
- Week 1-2: 画像検索 + ラクマ
- Week 3-4: 自然言語検索 + Discogs

### Month 3
- Week 1-2: 統合テスト
- Week 3-4: 最適化とリリース

## メトリクス

### 成功指標
- 対応プラットフォーム数: 3 → 10
- 検索カバレッジ: 60% → 90%
- 平均検索時間: <3秒を維持
- API利用料: 予算内に収める

### モニタリング項目
- 各プラットフォームの応答時間
- エラー率
- API利用量
- キャッシュヒット率