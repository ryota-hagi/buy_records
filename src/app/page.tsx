'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import Filters, { FilterOptions } from '@/components/Filters';
import DataTable, { ProfitResult } from '@/components/DataTable';
import Pagination from '@/components/Pagination';

export default function Home() {
  // 状態管理
  const [data, setData] = useState<ProfitResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // ページネーション
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [limit] = useState<number>(50);
  
  // ソートとフィルター
  const [sortBy, setSortBy] = useState<string>('profit_amount');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState<FilterOptions>({});

  // データ取得関数
  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // URLパラメータを構築
      const params = new URLSearchParams();
      params.append('page', currentPage.toString());
      params.append('limit', limit.toString());
      params.append('sortBy', sortBy);
      params.append('sortOrder', sortOrder);
      
      // フィルターパラメータを追加
      if (filters.platform) {
        params.append('platform', filters.platform);
      }
      
      if (filters.minProfit !== undefined) {
        params.append('minProfit', filters.minProfit.toString());
      }
      
      if (filters.maxProfit !== undefined) {
        params.append('maxProfit', filters.maxProfit.toString());
      }
      
      if (filters.search) {
        params.append('search', filters.search);
      }
      
      // APIリクエスト
      const response = await fetch(`/api/items?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      
      const result = await response.json();
      
      // データを設定
      setData(result.data);
      setTotalPages(result.pagination.totalPages);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('データの取得中にエラーが発生しました。後でもう一度お試しください。');
      setData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 初回レンダリング時とパラメータ変更時にデータを取得
  useEffect(() => {
    fetchData();
  }, [currentPage, sortBy, sortOrder, filters]);

  // ソート変更ハンドラー
  const handleSortChange = (newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1); // ソート変更時は1ページ目に戻る
  };

  // フィルター変更ハンドラー
  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
    setCurrentPage(1); // フィルター変更時は1ページ目に戻る
  };

  // ページ変更ハンドラー
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        {/* フィルター */}
        <Filters onFilterChange={handleFilterChange} />
        
        {/* エラーメッセージ */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {/* データテーブル */}
        <DataTable 
          data={data} 
          isLoading={isLoading} 
          onSortChange={handleSortChange} 
        />
        
        {/* ページネーション */}
        {!isLoading && data.length > 0 && (
          <Pagination 
            currentPage={currentPage} 
            totalPages={totalPages} 
            onPageChange={handlePageChange} 
          />
        )}
        
        {/* データがない場合のメッセージ */}
        {!isLoading && data.length === 0 && !error && (
          <div className="text-center py-8 text-gray-500">
            データが見つかりませんでした。フィルター条件を変更してみてください。
          </div>
        )}
      </div>
    </main>
  );
}
