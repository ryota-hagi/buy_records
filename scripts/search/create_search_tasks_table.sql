-- 検索タスクテーブルの作成
CREATE TABLE IF NOT EXISTS public.search_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    search_params JSONB NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS search_tasks_status_idx ON public.search_tasks (status);
CREATE INDEX IF NOT EXISTS search_tasks_created_at_idx ON public.search_tasks (created_at DESC);

-- RLSポリシーの設定
ALTER TABLE public.search_tasks ENABLE ROW LEVEL SECURITY;

-- 匿名ユーザーにも読み書き権限を付与
CREATE POLICY "Allow anonymous select" ON public.search_tasks FOR SELECT USING (true);
CREATE POLICY "Allow anonymous insert" ON public.search_tasks FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous update" ON public.search_tasks FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous delete" ON public.search_tasks FOR DELETE USING (true);

-- 更新時に updated_at を自動更新する関数とトリガーの作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_search_tasks_updated_at ON public.search_tasks;
CREATE TRIGGER update_search_tasks_updated_at
BEFORE UPDATE ON public.search_tasks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- コメント
COMMENT ON TABLE public.search_tasks IS '検索タスク情報を管理するテーブル';
COMMENT ON COLUMN public.search_tasks.id IS 'タスクの一意識別子';
COMMENT ON COLUMN public.search_tasks.name IS 'タスク名';
COMMENT ON COLUMN public.search_tasks.status IS 'タスクのステータス (pending, running, completed, failed, cancelled)';
COMMENT ON COLUMN public.search_tasks.search_params IS '検索パラメータ (JSON形式)';
COMMENT ON COLUMN public.search_tasks.result IS '検索結果 (JSON形式)';
COMMENT ON COLUMN public.search_tasks.error IS 'エラーメッセージ';
COMMENT ON COLUMN public.search_tasks.created_at IS 'タスク作成日時';
COMMENT ON COLUMN public.search_tasks.updated_at IS 'タスク更新日時';
COMMENT ON COLUMN public.search_tasks.completed_at IS 'タスク完了日時';
