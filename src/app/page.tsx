'use client';

import React, { useState, useEffect } from 'react';
import Header from '@/components/Header';
import TaskList, { Task } from '@/components/TaskList';
import TaskDetail from '@/components/TaskDetail';

export default function HomePage() {
  const [janCode, setJanCode] = useState('');
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isTaskDetailLoading, setIsTaskDetailLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // タスク一覧を取得
  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/search/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      } else {
        console.error('Failed to fetch tasks');
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // タスク詳細を取得
  const fetchTaskDetail = async (taskId: string) => {
    setIsTaskDetailLoading(true);
    try {
      const response = await fetch(`/api/search/tasks/${taskId}`);
      if (response.ok) {
        const taskDetail = await response.json();
        setSelectedTask(taskDetail);
      } else {
        console.error('Failed to fetch task detail');
      }
    } catch (error) {
      console.error('Error fetching task detail:', error);
    } finally {
      setIsTaskDetailLoading(false);
    }
  };

  // タスクをキャンセル
  const cancelTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/search/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        // タスク一覧を更新
        await fetchTasks();
        // 選択されたタスクが更新されたタスクの場合、詳細を再取得
        if (selectedTask && selectedTask.id === taskId) {
          await fetchTaskDetail(taskId);
        }
      } else {
        console.error('Failed to cancel task');
      }
    } catch (error) {
      console.error('Error cancelling task:', error);
    }
  };

  // タスクを削除
  const deleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/search/tasks/${taskId}?action=delete`, {
        method: 'DELETE',
      });
      if (response.ok) {
        // タスク一覧を更新
        await fetchTasks();
        // 選択されたタスクが削除されたタスクの場合、選択を解除
        if (selectedTask && selectedTask.id === taskId) {
          setSelectedTask(null);
        }
      } else {
        console.error('Failed to delete task');
      }
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  // JANコード検索タスクを作成
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!janCode.trim()) {
      setError('JANコードを入力してください');
      return;
    }
    
    // JANコードの基本的なバリデーション（13桁または8桁）
    const cleanJanCode = janCode.trim().replace(/[^0-9]/g, '');
    if (cleanJanCode.length !== 13 && cleanJanCode.length !== 8) {
      setError('JANコードは8桁または13桁の数字で入力してください');
      return;
    }
    
    setIsCreatingTask(true);
    setError(null);
    
    try {
      // 新しい検索タスクを作成
      const response = await fetch('/api/search/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jan_code: cleanJanCode
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'タスクの作成に失敗しました');
      }
      
      // タスク作成成功
      console.log('Task created:', result.task);
      
      // JANコード入力欄をクリア
      setJanCode('');
      
      // タスク一覧を更新
      await fetchTasks();
      
      // 新しく作成されたタスクの詳細を表示
      if (result.task && result.task.id) {
        await fetchTaskDetail(result.task.id);
      }
      
    } catch (err: any) {
      console.error('Task creation error:', err);
      setError(err.message || 'タスクの作成中にエラーが発生しました');
    } finally {
      setIsCreatingTask(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    
    // 定期的にタスク一覧を更新（5秒間隔）
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  // 選択されたタスクの詳細も定期的に更新
  useEffect(() => {
    if (selectedTask && (selectedTask.status === 'pending' || selectedTask.status === 'running')) {
      const interval = setInterval(() => {
        fetchTaskDetail(selectedTask.id);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [selectedTask]);
  
  return (
    <main className="min-h-screen bg-gray-100">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            JANコード価格比較検索
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            JANコードを入力してタスクを作成し、複数のプラットフォームで最安値を見つけましょう
          </p>
        </div>
        
        {/* JANコード検索フォーム */}
        <div className="max-w-2xl mx-auto mb-8">
          <form onSubmit={handleCreateTask} className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-4">
              <label htmlFor="janCode" className="block text-sm font-medium text-gray-700 mb-2">
                JANコード
              </label>
              <input
                type="text"
                id="janCode"
                value={janCode}
                onChange={(e) => setJanCode(e.target.value)}
                placeholder="例: 4901777300446"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isCreatingTask}
              />
              <p className="text-sm text-gray-500 mt-1">
                8桁または13桁の数字を入力してください
              </p>
            </div>
            
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={isCreatingTask}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isCreatingTask && (
                  <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {isCreatingTask ? 'タスク作成中...' : '検索タスクを作成'}
              </button>
            </div>
          </form>
        </div>
        
        {/* エラーメッセージ */}
        {error && (
          <div className="max-w-2xl mx-auto mb-6">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </div>
        )}
        
        {/* メインコンテンツ */}
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* 左側: タスク一覧 */}
            <div className="space-y-6">
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-medium text-gray-900">検索タスク一覧</h2>
                  <div className="text-sm text-gray-500">
                    {tasks.length > 0 && `${tasks.length}件のタスク`}
                  </div>
                </div>
                <TaskList
                  tasks={tasks}
                  isLoading={isLoading}
                  onTaskClick={fetchTaskDetail}
                  onCancelTask={cancelTask}
                  onDeleteTask={deleteTask}
                />
              </div>
            </div>

            {/* 右側: タスク詳細 */}
            <div className="lg:sticky lg:top-8">
              {selectedTask ? (
                <TaskDetail
                  task={selectedTask}
                  isLoading={isTaskDetailLoading}
                  onClose={() => setSelectedTask(null)}
                  onCancelTask={cancelTask}
                />
              ) : (
                <div className="bg-white shadow rounded-lg p-6">
                  <div className="text-center py-12">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">タスクが選択されていません</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      左側のタスク一覧からタスクを選択して詳細を確認してください
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* 使い方の説明 */}
        {tasks.length === 0 && !isLoading && (
          <div className="max-w-4xl mx-auto mt-12">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">使い方</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium mb-2">1. JANコードを入力</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    商品のJANコード（バーコード）を入力してください。8桁または13桁の数字です。
                  </p>
                  
                  <h3 className="font-medium mb-2">2. 検索タスクを作成</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    「検索タスクを作成」ボタンをクリックすると、バックグラウンドで検索が開始されます。
                  </p>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">3. 進捗を確認</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    タスク一覧で検索の進捗状況を確認できます。完了したタスクをクリックして結果を確認してください。
                  </p>
                  
                  <h3 className="font-medium mb-2">4. 複数タスクの管理</h3>
                  <p className="text-sm text-gray-600">
                    複数のJANコードを同時に検索できます。各タスクは独立して実行され、結果は個別に確認できます。
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
