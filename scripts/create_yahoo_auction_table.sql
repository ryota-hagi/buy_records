-- Yahoo!オークションアイテムテーブル
CREATE TABLE IF NOT EXISTS yahoo_auction_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  search_term TEXT NOT NULL,
  item_id TEXT NOT NULL,
  title TEXT NOT NULL,
  current_price INTEGER,
  buy_now_price INTEGER,
  bids INTEGER,
  currency TEXT DEFAULT 'JPY',
  status TEXT NOT NULL,  -- 'active' または 'ended'
  end_time TIMESTAMP WITH TIME ZONE,
  condition TEXT,
  url TEXT,
  image_url TEXT,
  seller TEXT,
  lowest_current_price INTEGER,
  active_listings_count INTEGER,
  avg_sold_price NUMERIC(10, 2),
  median_sold_price NUMERIC(10, 2),
  sold_count INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(item_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_yahoo_auction_search_term ON yahoo_auction_items(search_term);
CREATE INDEX IF NOT EXISTS idx_yahoo_auction_status ON yahoo_auction_items(status);
CREATE INDEX IF NOT EXISTS idx_yahoo_auction_current_price ON yahoo_auction_items(current_price);
