'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Task {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  result?: {
    integrated_results?: {
      count: number;
      items: Array<{ price: number }>;
    };
  };
}

export default function HomePage() {
  const [searchType, setSearchType] = useState<'jan' | 'product' | 'image'>('jan');
  const [searchValue, setSearchValue] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  
  // マウス位置でタスク履歴の表示制御
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const threshold = window.innerHeight * 0.8; // 画面下部20%
      const historyElement = document.getElementById('search-history');
      
      if (historyElement && showHistory) {
        const rect = historyElement.getBoundingClientRect();
        // 履歴が表示中は、履歴領域外に出たときのみ非表示
        if (e.clientY < rect.top) {
          setShowHistory(false);
        }
      } else {
        // 履歴が非表示中は、画面下部でのみ表示
        setShowHistory(e.clientY > threshold);
      }
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [showHistory]);

  const handleSearch = async () => {
    if (!searchValue.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await fetch('/api/search/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: searchValue,
          type: searchType,
          jan_code: searchType === 'jan' ? searchValue : undefined,
          product_name: searchType === 'product' ? searchValue : undefined,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        // Refresh tasks list
        fetchTasks();
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/search/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-white relative overflow-hidden">
      {/* Google風中央検索エリア */}
      <div className="min-h-screen flex flex-col items-center justify-center">
        {/* ロゴ */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-6xl font-normal">
            <span className="text-blue-500">価</span>
            <span className="text-red-500">格</span>
            <span className="text-yellow-500">比</span>
            <span className="text-blue-500">較</span>
            <span className="text-green-500">検</span>
            <span className="text-red-500">索</span>
          </h1>
        </motion.div>

        {/* 検索ボックス */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-xl px-5"
        >
          <div className="relative">
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={
                searchType === 'jan' ? 'JANコードを入力' :
                searchType === 'product' ? '商品名で検索' :
                '画像をドロップ'
              }
              className="w-full px-12 py-4 border border-gray-200 rounded-full hover:shadow-md focus:outline-none focus:shadow-lg transition-shadow duration-200"
            />
            
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
              {/* 画像アップロードボタン */}
              <button
                onClick={() => setSearchType('image')}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          {/* 検索タイプ切り替えボタン */}
          <div className="flex justify-center mt-6 space-x-4">
            <button
              onClick={() => setSearchType('jan')}
              className={`px-4 py-2 rounded-md text-sm ${
                searchType === 'jan' 
                  ? 'bg-gray-100 text-gray-700' 
                  : 'text-gray-600 hover:bg-gray-50'
              } transition-colors`}
            >
              JANコード
            </button>
            <button
              onClick={() => setSearchType('product')}
              className={`px-4 py-2 rounded-md text-sm ${
                searchType === 'product' 
                  ? 'bg-gray-100 text-gray-700' 
                  : 'text-gray-600 hover:bg-gray-50'
              } transition-colors`}
            >
              商品名
            </button>
          </div>

          {/* 検索ボタン */}
          <div className="flex justify-center mt-8">
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="px-10 py-3 bg-gray-50 text-gray-700 rounded-md hover:shadow hover:bg-gray-100 transition-all duration-200 disabled:opacity-50"
            >
              {isSearching ? '検索中...' : '検索'}
            </button>
          </div>
        </motion.div>
      </div>

      {/* マウスオーバーで表示される検索履歴 */}
      <AnimatePresence>
        {showHistory && (
          <motion.div
            id="search-history"
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ 
              type: "spring",
              damping: 25,
              stiffness: 200,
              mass: 0.5
            }}
            className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 shadow-lg"
            style={{ maxHeight: '40vh' }}
          >
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-700 mb-4">検索履歴</h3>
              
              <div className="space-y-3 overflow-y-auto" style={{ maxHeight: '30vh' }}>
                {tasks.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">検索履歴はありません</p>
                ) : (
                  tasks.map((task) => (
                    <motion.div
                      key={task.id}
                      whileHover={{ backgroundColor: '#f9fafb' }}
                      onClick={() => {
                        setSelectedTask(task);
                        setSelectedPlatform('all');
                      }}
                      className="flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-2 h-2 rounded-full ${
                          task.status === 'completed' ? 'bg-green-500' :
                          task.status === 'running' ? 'bg-blue-500 animate-pulse' :
                          task.status === 'failed' ? 'bg-red-500' :
                          'bg-gray-300'
                        }`} />
                        <div>
                          <p className="text-gray-800">{task.name}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(task.created_at).toLocaleString('ja-JP')}
                          </p>
                        </div>
                      </div>
                      
                      {task.status === 'completed' && task.result && (
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-700">
                            {task.result.integrated_results?.count || 0}件
                          </p>
                          {task.result.integrated_results?.items && task.result.integrated_results.items.length > 0 && (
                            <p className="text-xs text-gray-500">
                              最安値: ¥{Math.min(...task.result.integrated_results.items.map(i => i.price)).toLocaleString()}
                            </p>
                          )}
                        </div>
                      )}
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* タスク詳細モーダル（ECサイト風） */}
      <AnimatePresence>
        {selectedTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
            onClick={() => setSelectedTask(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-xl shadow-2xl w-[95vw] h-[90vh] overflow-hidden flex flex-col"
            >
              <div className="p-6 border-b flex justify-between items-center">
                <h2 className="text-2xl font-semibold text-gray-800">{selectedTask.name}</h2>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6">
                {selectedTask.status === 'completed' && selectedTask.result?.integrated_results && (
                  <>
                    {/* プラットフォームタブ */}
                    {selectedTask.result.integrated_results.platform_results && (
                      <div className="mb-6 border-b">
                        <div className="flex flex-wrap gap-2 pb-4">
                          <button
                            onClick={() => setSelectedPlatform('all')}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                              selectedPlatform === 'all'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            すべて ({selectedTask.result.integrated_results.items?.length || 0})
                          </button>
                          {Object.entries(selectedTask.result.integrated_results.platform_results).map(([platform, items]: [string, any]) => (
                            <button
                              key={platform}
                              onClick={() => setSelectedPlatform(platform)}
                              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                                selectedPlatform === platform
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              {platform === 'yahoo_shopping' ? 'Yahoo!ショッピング' :
                               platform === 'mercari' ? 'メルカリ' :
                               platform === 'ebay' ? 'eBay' :
                               platform === 'paypay' ? 'PayPayフリマ' :
                               platform === 'rakuma' ? 'ラクマ' :
                               platform} ({items.length})
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* 検索結果グリッド */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                    {(selectedPlatform === 'all' 
                      ? selectedTask.result.integrated_results.items 
                      : selectedTask.result.integrated_results.platform_results[selectedPlatform] || []
                    ).map((item: any, index: number) => (
                      <div key={index} className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow bg-white">
                        <div className="aspect-square relative bg-gray-100">
                          {(item.image || item.image_url) ? (
                            <img 
                              src={item.image || item.image_url} 
                              alt={item.title} 
                              className="absolute inset-0 w-full h-full object-cover"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRTVFN0VCIi8+CjxwYXRoIGQ9Ik04MCAxMjBWODBIMTIwVjEyMEg4MFoiIGZpbGw9IiM5Q0E0QjQiLz4KPHBhdGggZD0iTTEwMCA5NUMxMDIuNzYxIDk1IDEwNSA5Mi43NjE0IDEwNSA5MEM5NS4yMzg2IDk1IDkwIDE5NS4yMzg2IDkwIDkwUzkyLjIzODYgODUgOTUgODVTOTcuNzYxNCA4NyA5NyA5MEw5NyA5MFoiIGZpbGw9IiM5Q0E0QjQiLz4KPHBhdGggZD0iTTgwIDExMEw5NSA5NUwxMTAgMTEwSDE2WiIgZmlsbD0iIzlDQTRCNCIvPgo8L3N2Zz4=';
                              }}
                            />
                          ) : (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          )}
                        </div>
                        
                        <div className="p-3">
                          <h3 className="font-medium text-sm text-gray-800 mb-2 line-clamp-2 min-h-[2.5rem]">
                            {item.title}
                          </h3>
                          
                          <div className="space-y-1 mb-3">
                            <p className="text-xl font-bold text-blue-600">
                              ¥{item.price.toLocaleString()}
                            </p>
                            
                            <div className="flex items-center gap-2 text-xs">
                              <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                                {item.platform}
                              </span>
                              {item.condition && (
                                <span className={`px-2 py-0.5 rounded ${
                                  item.condition.includes('新品') || item.condition.toLowerCase().includes('new')
                                    ? 'bg-green-100 text-green-700' 
                                    : 'bg-yellow-100 text-yellow-700'
                                }`}>
                                  {item.condition.includes('新品') || item.condition.toLowerCase().includes('new') ? '新品' : '中古'}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block w-full text-center bg-blue-500 text-white py-2 rounded text-sm hover:bg-blue-600 transition-colors"
                          >
                            商品を見る
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                  </>
                )}
                
                {selectedTask.status !== 'completed' && (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                      <p className="text-gray-600">検索を実行中です...</p>
                    </div>
                  </div>
                )}
                
                {selectedTask.status === 'completed' && (!selectedTask.result?.integrated_results?.items || selectedTask.result.integrated_results.items.length === 0) && (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-gray-600">検索結果が見つかりませんでした</p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}