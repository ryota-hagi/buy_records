import React from 'react';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { Task } from './TaskList';

interface TaskDetailProps {
  task: Task | null;
  isLoading: boolean;
  onClose: () => void;
  onCancelTask?: (taskId: string) => void;
}

export default function TaskDetail({ task, isLoading, onClose, onCancelTask }: TaskDetailProps) {
  // プラットフォームフィルター用の状態
  const [selectedPlatform, setSelectedPlatform] = React.useState<string>('all');

  // デバッグ用のコンソールログ
  React.useEffect(() => {
    if (task) {
      console.log('Task data:', task);
      console.log('Task status:', task.status);
      console.log('Processing logs:', task.processing_logs);
      console.log('Processing logs type:', typeof task.processing_logs);
      console.log('Results:', (task as any).results);
      console.log('Results count:', (task as any).results_count);
      console.log('Results length:', (task as any).results?.length);
      console.log('Stats:', (task as any).stats);
      
      // 処理進捗ログの詳細チェック
      let logs = task.processing_logs;
      if (typeof logs === 'string') {
        try {
          logs = JSON.parse(logs);
          console.log('Parsed logs:', logs);
        } catch (e) {
          console.log('Failed to parse logs:', e);
          logs = [];
        }
      }
      console.log('Final logs:', logs);
      console.log('Logs length:', logs?.length);
      
      // 検索結果セクションの表示条件をチェック
      const isCompleted = task.status === 'completed';
      const hasResults = (task as any).results && (task as any).results.length > 0;
      console.log('Is completed:', isCompleted);
      console.log('Has results:', hasResults);
      console.log('Should show results section:', isCompleted && hasResults);
    }
  }, [task]);

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
  const LoadingSpinner = ({ size = 'h-4 w-4' }: { size?: string }) => (
    <svg className={`animate-spin ${size} text-current`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );

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

  // プラットフォーム名を日本語に変換
  const getPlatformName = (platform: string) => {
    switch (platform) {
      case 'discogs':
        return 'Discogs';
      case 'ebay':
        return 'eBay';
      case 'mercari':
        return 'メルカリ';
      case 'yahoo_auction':
        return 'Yahoo!オークション';
      default:
        return platform;
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded mb-2 w-1/4"></div>
            <div className="h-4 bg-gray-200 rounded mb-4 w-1/3"></div>
            <div className="h-32 bg-gray-200 rounded mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!task) {
    return null;
  }

  // 処理進捗ログの準備
  let logs = task.processing_logs;
  if (typeof logs === 'string') {
    try {
      logs = JSON.parse(logs);
    } catch (e) {
      logs = [];
    }
  }
  if (!Array.isArray(logs)) {
    logs = [];
  }

  // プラットフォーム別の結果を計算
  const results = (task as any).results || [];
  const platformCounts = results.reduce((acc: Record<string, number>, item: any) => {
    const platform = item.platform || 'unknown';
    acc[platform] = (acc[platform] || 0) + 1;
    return acc;
  }, {});

  // 利用可能なプラットフォームリストを取得
  const availablePlatforms = Object.keys(platformCounts);

  // 選択されたプラットフォームに基づいて結果をフィルタリング
  const filteredResults = selectedPlatform === 'all' 
    ? results 
    : results.filter((item: any) => item.platform === selectedPlatform);

  // 表示用の結果（最大20件）
  const displayResults = filteredResults.slice(0, 20);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-50 pt-10 pb-10">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold">{task.name}</h2>
            <p className="text-sm text-gray-500">ID: {task.id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="閉じる"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* ステータス情報 */}
        <div className="mb-6">
          <div className="flex items-center mb-2">
            <span
              className={`px-2 py-1 inline-flex items-center text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(
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
            {(task.status === 'pending' || task.status === 'running') && onCancelTask && (
              <button
                onClick={() => onCancelTask(task.id)}
                className="ml-4 text-sm text-red-600 hover:text-red-800"
              >
                タスクをキャンセル
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
            <div>
              <span className="font-medium">作成日時:</span> {formatDate(task.created_at)}
            </div>
            <div>
              <span className="font-medium">更新日時:</span> {formatDate(task.updated_at)}
            </div>
            {task.completed_at && (
              <>
                <div>
                  <span className="font-medium">完了日時:</span> {formatDate(task.completed_at)}
                </div>
                <div>
                  <span className="font-medium">実行時間:</span> {getExecutionTime(task)}
                </div>
              </>
            )}
          </div>
        </div>

        {/* 処理進捗 - 常に表示 */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2 flex items-center">
            処理進捗
            {(task.status === 'pending' || task.status === 'running') && (
              <LoadingSpinner size="h-5 w-5 ml-2" />
            )}
          </h3>
          <div className="bg-gray-50 p-4 rounded-md">
            {logs && logs.length > 0 ? (
              <div className="space-y-3">
                {logs.map((log: any, index: number) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {log.status === 'started' && (
                        <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                      )}
                      {log.status === 'completed' && (
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      )}
                      {log.status === 'failed' && (
                        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      )}
                      {!log.status && (
                        <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">
                          {log.timestamp ? formatDate(log.timestamp) : '時刻不明'}
                        </span>
                        {log.platform && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                            {getPlatformName(log.platform)}
                          </span>
                        )}
                        {log.count !== null && log.count !== undefined && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                            {log.count}件
                          </span>
                        )}
                        {log.status && (
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            log.status === 'started' ? 'bg-blue-100 text-blue-800' :
                            log.status === 'completed' ? 'bg-green-100 text-green-800' :
                            log.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {log.status}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {log.message || log.step || 'メッセージなし'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-500 text-sm">
                  {task.status === 'pending' ? 'タスクは待機中です。処理が開始されると進捗が表示されます。' :
                   task.status === 'running' ? 'タスクを実行中です。進捗情報を取得しています...' :
                   '処理進捗の履歴がありません。'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 待機中・実行中の場合の追加メッセージ */}
        {(task.status === 'pending' || task.status === 'running') && (
          <div className="mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex items-center">
                <LoadingSpinner size="h-5 w-5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    {task.status === 'pending' ? 'タスクは待機中です' : 'タスクを実行中です'}
                  </h3>
                  <p className="text-sm text-blue-700 mt-1">
                    {task.status === 'pending' 
                      ? '他のタスクの完了を待っています。しばらくお待ちください。'
                      : '検索処理を実行しています。完了までしばらくお待ちください。'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 検索パラメータ */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">検索パラメータ</h3>
          <div className="bg-gray-50 p-4 rounded-md">
            {task.search_params ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {task.search_params.jan_code && (
                  <div>
                    <span className="font-medium">JANコード:</span> {task.search_params.jan_code}
                  </div>
                )}
                {task.search_params.query && (
                  <div>
                    <span className="font-medium">検索クエリ:</span> {task.search_params.query}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">検索パラメータなし</p>
            )}

            {/* プラットフォーム */}
            {task.search_params?.platforms && task.search_params.platforms.length > 0 && (
              <div className="mt-3">
                <span className="font-medium">検索プラットフォーム:</span>{' '}
                {task.search_params.platforms.map(getPlatformName).join(', ')}
              </div>
            )}
          </div>
        </div>

        {/* 検索結果 */}
        {task.status === 'completed' && (
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-2">検索結果</h3>

            {/* 統計情報とプラットフォームタブ */}
            <div className="mb-4">
              <div className="bg-gray-50 p-4 rounded-md">
                <p className="mb-2">
                  <span className="font-medium">総件数:</span>{' '}
                  {(task as any).results_count || 0}件
                  {selectedPlatform !== 'all' && (
                    <span className="text-gray-600">
                      {' '}（{getPlatformName(selectedPlatform)}: {filteredResults.length}件を表示）
                    </span>
                  )}
                </p>

                {/* プラットフォームタブ */}
                {availablePlatforms.length > 0 && (
                  <div className="mt-4">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setSelectedPlatform('all')}
                        className={`px-3 py-1 text-sm rounded-md border transition-colors ${
                          selectedPlatform === 'all'
                            ? 'bg-blue-500 text-white border-blue-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        全て ({results.length})
                      </button>
                      {availablePlatforms.map((platform) => (
                        <button
                          key={platform}
                          onClick={() => setSelectedPlatform(platform)}
                          className={`px-3 py-1 text-sm rounded-md border transition-colors ${
                            selectedPlatform === platform
                              ? 'bg-blue-500 text-white border-blue-500'
                              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {getPlatformName(platform)} ({platformCounts[platform]})
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* 統計情報 */}
                {(task as any).stats && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                    <div>
                      <span className="font-medium">価格範囲:</span>{' '}
                      {(task as any).stats.min_price?.toLocaleString()}円 - {(task as any).stats.max_price?.toLocaleString()}円
                    </div>
                    <div>
                      <span className="font-medium">平均価格:</span>{' '}
                      {Math.round((task as any).stats.avg_price)?.toLocaleString()}円
                    </div>
                    <div>
                      <span className="font-medium">検索プラットフォーム:</span>{' '}
                      {(task as any).stats.platforms?.map(getPlatformName).join(', ')}
                    </div>
                    <div>
                      <span className="font-medium">プラットフォーム別件数:</span>{' '}
                      {Object.entries((task as any).stats.platform_counts || {}).map(([platform, count]) => 
                        `${getPlatformName(platform)}: ${count}件`
                      ).join(', ')}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 検索結果一覧 */}
            {displayResults && displayResults.length > 0 && (
              <div>
                <h4 className="text-md font-medium mb-2">
                  検索結果一覧
                  {selectedPlatform !== 'all' && (
                    <span className="text-sm font-normal text-gray-600 ml-2">
                      - {getPlatformName(selectedPlatform)}（最大20件表示）
                    </span>
                  )}
                  {selectedPlatform === 'all' && filteredResults.length > 20 && (
                    <span className="text-sm font-normal text-gray-600 ml-2">
                      - 最大20件表示
                    </span>
                  )}
                </h4>
                <div className="bg-gray-50 p-4 rounded-md">
                  <div className="space-y-4">
                    {displayResults.map((item: any, index: number) => (
                      <div key={index} className="bg-white p-4 rounded border border-gray-200">
                        <div className="flex items-start">
                          {item.image_url && (
                            <img
                              src={item.image_url}
                              alt={item.title || '商品画像'}
                              className="w-20 h-20 object-cover rounded mr-4"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          )}
                          <div className="flex-1">
                            <h6 className="font-medium text-lg mb-2">
                              {(item.item_url || item.url) ? (
                                <a 
                                  href={item.item_url || item.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                >
                                  {item.item_title || item.title || '不明なタイトル'}
                                </a>
                              ) : (
                                item.item_title || item.title || '不明なタイトル'
                              )}
                            </h6>
                            
                            <div className="flex flex-wrap gap-2 mb-3">
                              <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded">
                                {getPlatformName(item.platform || '')}
                              </span>
                              {(item.total_price || item.price) && (
                                <span className="text-sm bg-green-100 text-green-800 px-3 py-1 rounded font-medium">
                                  ¥{(item.total_price || item.price).toLocaleString()}
                                </span>
                              )}
                              {item.condition && (
                                <span className="text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded">
                                  {item.condition}
                                </span>
                              )}
                              {item.seller && (
                                <span className="text-sm bg-gray-100 text-gray-800 px-3 py-1 rounded">
                                  {item.seller}
                                </span>
                              )}
                              {item.location && (
                                <span className="text-sm bg-yellow-100 text-yellow-800 px-3 py-1 rounded">
                                  {item.location}
                                </span>
                              )}
                            </div>

                            {/* 価格詳細 */}
                            {(item.price || item.shipping_cost) && (
                              <div className="text-sm text-gray-600 mb-2">
                                {item.price && (
                                  <div>商品価格: ¥{item.price.toLocaleString()}</div>
                                )}
                                {item.shipping_cost && item.shipping_cost > 0 && (
                                  <div>送料: ¥{item.shipping_cost.toLocaleString()}</div>
                                )}
                                {item.shipping_cost === 0 && (
                                  <div>送料: 無料</div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 検索結果が0件の場合 */}
            {(!(task as any).results || (task as any).results.length === 0) && (
              <div className="bg-blue-50 p-4 rounded-md">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">
                      検索結果がありません
                    </h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <p>
                        現在、このタスクには検索結果がありません。これは以下の理由が考えられます：
                      </p>
                      <ul className="mt-2 list-disc list-inside space-y-1">
                        <li>検索がまだ実行されていない</li>
                        <li>検索条件に一致する商品が見つからなかった</li>
                        <li>検索処理でエラーが発生した</li>
                        <li>古いモックデータが削除された</li>
                      </ul>
                      <p className="mt-2">
                        新しい検索を実行するか、検索条件を変更してお試しください。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* エラー情報 */}
        {task.error && (
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-2">エラー情報</h3>
            <div className="bg-red-50 p-4 rounded-md text-red-700">
              <p>{task.error}</p>
            </div>
          </div>
        )}

        {/* フッター */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
