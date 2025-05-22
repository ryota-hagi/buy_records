import React, { useState, useEffect } from 'react';
import { getAvailablePlatforms } from '../lib/supabase';

interface FiltersProps {
  onFilterChange: (filters: FilterOptions) => void;
}

export interface FilterOptions {
  platform?: string;
  minProfit?: number;
  maxProfit?: number;
  search?: string;
}

export default function Filters({ onFilterChange }: FiltersProps) {
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [minProfit, setMinProfit] = useState<string>('');
  const [maxProfit, setMaxProfit] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // プラットフォームのリストを取得
  useEffect(() => {
    async function fetchPlatforms() {
      try {
        const platformList = await getAvailablePlatforms();
        setPlatforms(platformList);
      } catch (error) {
        console.error('Error fetching platforms:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchPlatforms();
  }, []);

  // フィルター変更時にコールバックを呼び出す
  const handleFilterChange = () => {
    const filters: FilterOptions = {};
    
    if (selectedPlatform) {
      filters.platform = selectedPlatform;
    }
    
    if (minProfit) {
      filters.minProfit = Number(minProfit);
    }
    
    if (maxProfit) {
      filters.maxProfit = Number(maxProfit);
    }
    
    if (search) {
      filters.search = search;
    }
    
    onFilterChange(filters);
  };

  // フィルターをリセット
  const handleReset = () => {
    setSelectedPlatform('');
    setMinProfit('');
    setMaxProfit('');
    setSearch('');
    onFilterChange({});
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md mb-4">
      <h2 className="text-lg font-semibold mb-3">フィルター</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* プラットフォーム選択 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            プラットフォーム
          </label>
          <select
            className="w-full p-2 border border-gray-300 rounded-md"
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            disabled={loading}
          >
            <option value="">すべて</option>
            {platforms.map((platform) => (
              <option key={platform} value={platform}>
                {platform}
              </option>
            ))}
          </select>
        </div>
        
        {/* 最小利益 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            最小利益 (円)
          </label>
          <input
            type="number"
            className="w-full p-2 border border-gray-300 rounded-md"
            value={minProfit}
            onChange={(e) => setMinProfit(e.target.value)}
            placeholder="例: 1000"
          />
        </div>
        
        {/* 最大利益 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            最大利益 (円)
          </label>
          <input
            type="number"
            className="w-full p-2 border border-gray-300 rounded-md"
            value={maxProfit}
            onChange={(e) => setMaxProfit(e.target.value)}
            placeholder="例: 10000"
          />
        </div>
        
        {/* 検索 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            検索
          </label>
          <input
            type="text"
            className="w-full p-2 border border-gray-300 rounded-md"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="タイトル、アーティスト..."
          />
        </div>
      </div>
      
      {/* ボタン */}
      <div className="mt-4 flex justify-end space-x-2">
        <button
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          onClick={handleReset}
        >
          リセット
        </button>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          onClick={handleFilterChange}
        >
          適用
        </button>
      </div>
    </div>
  );
}
