-- 検索結果テーブルを作成
CREATE TABLE IF NOT EXISTS search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES search_tasks(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    title TEXT,
    artist TEXT,
    url TEXT,
    image_url TEXT,
    item_price DECIMAL(10,2),
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    condition TEXT,
    status VARCHAR(20) DEFAULT 'active',
    description TEXT,
    seller_name TEXT,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックスを作成
CREATE INDEX IF NOT EXISTS idx_search_results_task_id ON search_results(task_id);
CREATE INDEX IF NOT EXISTS idx_search_results_platform ON search_results(platform);
CREATE INDEX IF NOT EXISTS idx_search_results_total_price ON search_results(total_price);
CREATE INDEX IF NOT EXISTS idx_search_results_created_at ON search_results(created_at);

-- RLSを有効化
ALTER TABLE search_results ENABLE ROW LEVEL SECURITY;

-- 全てのユーザーが読み取り可能なポリシーを作成
CREATE POLICY IF NOT EXISTS "Allow read access for all users" ON search_results
    FOR SELECT USING (true);

-- 全てのユーザーが挿入可能なポリシーを作成
CREATE POLICY IF NOT EXISTS "Allow insert access for all users" ON search_results
    FOR INSERT WITH CHECK (true);

-- 全てのユーザーが更新可能なポリシーを作成
CREATE POLICY IF NOT EXISTS "Allow update access for all users" ON search_results
    FOR UPDATE USING (true);

-- 全てのユーザーが削除可能なポリシーを作成
CREATE POLICY IF NOT EXISTS "Allow delete access for all users" ON search_results
    FOR DELETE USING (true);
