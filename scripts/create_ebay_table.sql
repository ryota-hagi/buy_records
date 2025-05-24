-- eBay販売データテーブル作成
CREATE TABLE ebay_sales_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  search_term TEXT NOT NULL,
  item_id TEXT,
  title TEXT,
  sold_price DECIMAL,
  currency TEXT DEFAULT 'USD',
  sold_date TIMESTAMP WITH TIME ZONE,
  sold_quantity INTEGER,
  condition TEXT,
  url TEXT,
  image_url TEXT,
  seller TEXT,
  lowest_current_price DECIMAL,
  current_listings_count INTEGER,
  avg_sold_price_90days DECIMAL,
  median_sold_price_90days DECIMAL,
  sold_count_90days INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX idx_ebay_sales_search_term ON ebay_sales_data(search_term);
CREATE INDEX idx_ebay_sales_sold_price ON ebay_sales_data(sold_price);
CREATE INDEX idx_ebay_sales_sold_date ON ebay_sales_data(sold_date);

-- コメント追加
COMMENT ON TABLE ebay_sales_data IS 'eBayの販売履歴データと現在の出品情報';
COMMENT ON COLUMN ebay_sales_data.search_term IS '検索キーワード';
COMMENT ON COLUMN ebay_sales_data.item_id IS 'eBay商品ID';
COMMENT ON COLUMN ebay_sales_data.title IS '商品タイトル';
COMMENT ON COLUMN ebay_sales_data.sold_price IS '売却価格';
COMMENT ON COLUMN ebay_sales_data.currency IS '通貨';
COMMENT ON COLUMN ebay_sales_data.sold_date IS '売却日時';
COMMENT ON COLUMN ebay_sales_data.sold_quantity IS '売却数量';
COMMENT ON COLUMN ebay_sales_data.condition IS '商品状態';
COMMENT ON COLUMN ebay_sales_data.url IS '商品URL';
COMMENT ON COLUMN ebay_sales_data.image_url IS '画像URL';
COMMENT ON COLUMN ebay_sales_data.seller IS '販売者名';
COMMENT ON COLUMN ebay_sales_data.lowest_current_price IS '現在の最安出品価格';
COMMENT ON COLUMN ebay_sales_data.current_listings_count IS '現在の出品数';
COMMENT ON COLUMN ebay_sales_data.avg_sold_price_90days IS '過去90日間の平均売却価格';
COMMENT ON COLUMN ebay_sales_data.median_sold_price_90days IS '過去90日間の中央値売却価格';
COMMENT ON COLUMN ebay_sales_data.sold_count_90days IS '過去90日間の売却件数';
