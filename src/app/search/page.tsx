'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

interface SearchResult {
  platform: string;
  item_title: string;
  item_url: string;
  item_image_url: string;
  price: number;
  total_price: number;
  shipping_cost: number;
  condition: string;
  seller: string;
}

interface Task {
  id: string;
  name: string;
  status: string;
  search_params: {
    jan_code: string;
    platforms: string[];
  };
  result?: {
    integrated_results: {
      count: number;
      items: SearchResult[];
    };
    platform_results: {
      ebay: SearchResult[];
      yahoo_shopping: SearchResult[];
      mercari: SearchResult[];
    };
    summary: any;
  };
  created_at: string;
  completed_at?: string;
  error?: string;
  processing_logs?: any[];
}

export default function SearchPage() {
  const [janCode, setJanCode] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!janCode.trim()) {
      setError('JANコードを入力してください');
      return;
    }

    setIsSearching(true);
    setError(null);
    setCurrentTask(null);
    setSearchResults([]);

    try {
      console.log('Starting search for JAN code:', janCode);
      
      // 検索タスクを作成
      const response = await fetch('/api/search/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jan_code: janCode.trim()
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        let errorMessage = '検索タスクの作成に失敗しました';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
          errorMessage = `サーバーエラー (${response.status})`;
        }
        throw new Error(errorMessage);
      }

      let taskData;
      try {
        taskData = await response.json();
        console.log('Task created:', taskData);
      } catch (parseError) {
        console.error('Failed to parse response JSON:', parseError);
        throw new Error('サーバーからの応答の解析に失敗しました');
      }
      
      if (taskData.success && taskData.task) {
        setCurrentTask(taskData.task);
        
        // タスクの完了を監視
        pollTaskStatus(taskData.task.id);
      } else {
        throw new Error(taskData.error || 'タスクの作成に失敗しました');
      }
    } catch (err) {
      console.error('Search error:', err);
      setError((err as Error).message);
      setIsSearching(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 30; // 最大30回（30秒）
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        console.log(`Polling task status (attempt ${attempts}/${maxAttempts})`);
        
        const response = await fetch(`/api/search/tasks/${taskId}`);
        if (!response.ok) {
          throw new Error('タスクの状態取得に失敗しました');
        }

        const taskData = await response.json();
        console.log('Task status:', taskData);
        
        if (taskData.success && taskData.task) {
          setCurrentTask(taskData.task);

          if (taskData.task.status === 'completed') {
            console.log('Task completed successfully');
            if (taskData.task.result?.integrated_results?.items) {
              setSearchResults(taskData.task.result.integrated_results.items);
            }
            setIsSearching(false);
            return;
          } else if (taskData.task.status === 'failed') {
            console.log('Task failed:', taskData.task.error);
            setError(taskData.task.error || '検索に失敗しました');
            setIsSearching(false);
            return;
          }
        }

        // まだ完了していない場合、1秒後に再試行
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
        } else {
          setError('検索がタイムアウトしました');
          setIsSearching(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        setError((err as Error).message);
        setIsSearching(false);
      }
    };

    poll();
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY'
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">JANコード検索</h1>
          
          <div className="flex gap-4 mb-6">
            <input
              type="text"
              value={janCode}
              onChange={(e) => setJanCode(e.target.value)}
              placeholder="JANコードを入力してください（例: 4902370542912）"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSearching}
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isSearching ? '検索中...' : '検索'}
            </button>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {currentTask && (
            <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
              <p><strong>タスク状態:</strong> {currentTask.status}</p>
              <p><strong>商品名:</strong> {currentTask.name}</p>
              {currentTask.status === 'running' && (
                <p className="text-sm mt-2">検索を実行中です。しばらくお待ちください...</p>
              )}
            </div>
          )}
        </div>

        {searchResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              検索結果 ({searchResults.length}件)
            </h2>
            
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {searchResults.map((result, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-4">
                    <div className="w-20 h-20 flex-shrink-0 bg-gray-50 rounded overflow-hidden">
                      {result.item_image_url ? (
                        <img
                          src={result.item_image_url}
                          alt={result.item_title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent && !parent.querySelector('svg')) {
                              const placeholder = document.createElement('div');
                              placeholder.className = 'w-full h-full flex items-center justify-center';
                              placeholder.innerHTML = `
                                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              `;
                              parent.appendChild(placeholder);
                            }
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
                        {result.item_title}
                      </h3>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p><strong>価格:</strong> {formatPrice(result.total_price)}</p>
                        <p><strong>プラットフォーム:</strong> {result.platform}</p>
                        <p><strong>状態:</strong> {result.condition}</p>
                        {result.seller && (
                          <p><strong>販売者:</strong> {result.seller}</p>
                        )}
                      </div>
                      {result.item_url && (
                        <a
                          href={result.item_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block mt-3 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                        >
                          商品を見る
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {isSearching && searchResults.length === 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">検索中です。しばらくお待ちください...</p>
          </div>
        )}
      </div>
    </div>
  );
}
