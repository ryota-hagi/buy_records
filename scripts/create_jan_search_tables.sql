-- JANコード検索システム用テーブル作成スクリプト

-- JANコード検索タスクテーブル
CREATE TABLE IF NOT EXISTS jan_search_tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  jan_code VARCHAR(13) NOT NULL,
  product_name TEXT,
  brand_name TEXT,
  maker_name TEXT,
  product_image_url TEXT,
  product_url TEXT,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT
);

-- 検索結果テーブル
CREATE TABLE IF NOT EXISTS search_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  task_id UUID REFERENCES jan_search_tasks(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  item_title TEXT,
  price DECIMAL(10,2),
  shipping_fee DECIMAL(10,2) DEFAULT 0,
  service_fee DECIMAL(10,2) DEFAULT 0,
  total_price DECIMAL(10,2) GENERATED ALWAYS AS (price + shipping_fee + service_fee) STORED,
  currency VARCHAR(3) DEFAULT 'JPY',
  item_url TEXT,
  item_image_url TEXT,
  seller_name TEXT,
  condition_text TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days')
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_jan_search_tasks_jan_code ON jan_search_tasks(jan_code);
CREATE INDEX IF NOT EXISTS idx_jan_search_tasks_status ON jan_search_tasks(status);
CREATE INDEX IF NOT EXISTS idx_jan_search_tasks_created_at ON jan_search_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_search_results_task_id ON search_results(task_id);
CREATE INDEX IF NOT EXISTS idx_search_results_platform ON search_results(platform);
CREATE INDEX IF NOT EXISTS idx_search_results_total_price ON search_results(total_price);
CREATE INDEX IF NOT EXISTS idx_search_results_expires_at ON search_results(expires_at);

-- 期限切れデータ削除用の関数
CREATE OR REPLACE FUNCTION cleanup_expired_search_results()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM search_results WHERE expires_at < NOW();
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 自動更新トリガー用の関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 自動更新トリガー
CREATE TRIGGER update_jan_search_tasks_updated_at
  BEFORE UPDATE ON jan_search_tasks
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- コメント追加
COMMENT ON TABLE jan_search_tasks IS 'JANコード検索タスクを管理するテーブル';
COMMENT ON TABLE search_results IS '各プラットフォームからの検索結果を保存するテーブル';
COMMENT ON COLUMN search_results.total_price IS '価格 + 送料 + 手数料の合計（自動計算）';
COMMENT ON COLUMN search_results.expires_at IS '検索結果の有効期限（7日間）';
