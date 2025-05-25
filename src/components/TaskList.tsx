import React from 'react';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onTaskClick: (taskId: string) => void;
  onCancelTask: (taskId: string) => void;
  onDeleteTask: (taskId: string) => void;
}

export interface Task {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  search_params: any;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  processing_logs?: Array<{
    timestamp: string;
    step: string;
    status: string;
    message?: string;
    platform?: string;
    count?: number;
  }>;
}

export default function TaskList({ tasks, isLoading, onTaskClick, onCancelTask, onDeleteTask }: TaskListProps) {
  // ステータスに応じたバッジの色を取得
  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // ステータスの日本語表示を取得
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '待機中';
      case 'running':
        return '実行中';
      case 'completed':
        return '完了';
      case 'failed':
        return '失敗';
      case 'cancelled':
        return 'キャンセル';
      default:
        return status;
    }
  };

  // ローディングアニメーションコンポーネント
  const LoadingSpinner = () => (
    <svg className="animate-spin h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );

  // 検索パラメータの概要を取得
  const getSearchSummary = (params: any) => {
    if (!params) return '検索条件なし';

    if (params.jan_code) {
      return `JANコード: ${params.jan_code}`;
    }

    if (params.query) {
      return `クエリ: ${params.query}`;
    }

    return '詳細検索条件';
  };

  // 結果の概要を取得
  const getResultSummary = (task: Task) => {
    if (task.status === 'pending') {
      return '待機中...';
    }

    if (task.status === 'running') {
      return '実行中...';
    }

    if (task.status === 'cancelled') {
      return 'キャンセルされました';
    }

    if (task.status === 'failed') {
      return `エラー: ${task.error || '不明なエラー'}`;
    }

    if (task.status === 'completed' && task.result) {
      if (task.result.integrated_results) {
        const count = task.result.integrated_results.count || 0;
        return `${count}件の結果`;
      }
    }

    return '結果なし';
  };

  // 実行時間を計算
  const getExecutionTime = (task: Task) => {
    if (!task.completed_at || !task.created_at) {
      return '';
    }

    try {
      const created = parseISO(task.created_at);
      const completed = parseISO(task.completed_at);
      const diffSeconds = Math.round((completed.getTime() - created.getTime()) / 1000);

      if (diffSeconds < 60) {
        return `${diffSeconds}秒`;
      } else {
        const minutes = Math.floor(diffSeconds / 60);
        const seconds = diffSeconds % 60;
        return `${minutes}分${seconds}秒`;
      }
    } catch (e) {
      return '';
    }
  };

  // 日時をフォーマット
  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'yyyy/MM/dd HH:mm:ss', { locale: ja });
    } catch (e) {
      return dateString;
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <p className="text-gray-500">検索タスクがありません。新しいタスクを作成してください。</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                タスク名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ステータス
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                検索条件
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                作成日時
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                結果
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                アクション
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tasks.map((task) => (
              <tr key={task.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => onTaskClick(task.id)}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{task.name}</div>
                  <div className="text-xs text-gray-500">ID: {task.id.substring(0, 8)}...</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span
                      className={`px-2 inline-flex items-center text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(
                        task.status
                      )}`}
                    >
                      {(task.status === 'pending' || task.status === 'running') && (
                        <LoadingSpinner />
                      )}
                      <span className={task.status === 'pending' || task.status === 'running' ? 'ml-1' : ''}>
                        {getStatusText(task.status)}
                      </span>
                    </span>
                  </div>
                  {task.completed_at && (
                    <div className="text-xs text-gray-500 mt-1">
                      実行時間: {getExecutionTime(task)}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs truncate">
                    {getSearchSummary(task.search_params)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{formatDate(task.created_at)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    {(task.status === 'pending' || task.status === 'running') && (
                      <LoadingSpinner />
                    )}
                    <span className={task.status === 'pending' || task.status === 'running' ? 'ml-2' : ''}>
                      {getResultSummary(task)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onTaskClick(task.id);
                    }}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    詳細
                  </button>
                  {(task.status === 'pending' || task.status === 'running') && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onCancelTask(task.id);
                      }}
                      className="text-red-600 hover:text-red-900 mr-3"
                    >
                      キャンセル
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('このタスクを完全に削除しますか？この操作は取り消せません。')) {
                        onDeleteTask(task.id);
                      }
                    }}
                    className="text-red-600 hover:text-red-900"
                    title="タスクを削除"
                  >
                    削除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
