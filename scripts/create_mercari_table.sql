-- Mercariデータテーブル作成
CREATE TABLE mercari_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  search_term TEXT NOT NULL,
  item_id TEXT,
  title TEXT,
  price DECIMAL,
  currency TEXT DEFAULT 'JPY',
  status TEXT, -- 'active' または 'sold_out'
  sold_date TIMESTAMP WITH TIME ZONE,
  condition TEXT,
  url TEXT,
  image_url TEXT,
  seller TEXT,
  lowest_active_price DECIMAL,
  active_listings_count INTEGER,
  avg_sold_price DECIMAL,
  median_sold_price DECIMAL,
  sold_count INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX idx_mercari_search_term ON mercari_data(search_term);
CREATE INDEX idx_mercari_price ON mercari_data(price);
CREATE INDEX idx_mercari_status ON mercari_data(status);
CREATE INDEX idx_mercari_sold_date ON mercari_data(sold_date);

-- コメント追加
COMMENT ON TABLE mercari_data IS 'メルカリの出品中商品と売却済み商品のデータ';
COMMENT ON COLUMN mercari_data.search_term IS '検索キーワード';
COMMENT ON COLUMN mercari_data.item_id IS 'メルカリ商品ID';
COMMENT ON COLUMN mercari_data.title IS '商品タイトル';
COMMENT ON COLUMN mercari_data.price IS '価格';
COMMENT ON COLUMN mercari_data.currency IS '通貨（デフォルトはJPY）';
COMMENT ON COLUMN mercari_data.status IS '商品状態（active: 出品中, sold_out: 売却済み）';
COMMENT ON COLUMN mercari_data.sold_date IS '売却日時（売却済みの場合のみ）';
COMMENT ON COLUMN mercari_data.condition IS '商品の状態（新品、良好など）';
COMMENT ON COLUMN mercari_data.url IS '商品URL';
COMMENT ON COLUMN mercari_data.image_url IS '画像URL';
COMMENT ON COLUMN mercari_data.seller IS '出品者名';
COMMENT ON COLUMN mercari_data.lowest_active_price IS '現在の最安出品価格';
COMMENT ON COLUMN mercari_data.active_listings_count IS '現在の出品数';
COMMENT ON COLUMN mercari_data.avg_sold_price IS '平均売却価格';
COMMENT ON COLUMN mercari_data.median_sold_price IS '中央値売却価格';
COMMENT ON COLUMN mercari_data.sold_count IS '売却件数';
