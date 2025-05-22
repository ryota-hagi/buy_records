import React, { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table';

// 利益計算結果の型定義
export interface ProfitResult {
  id: string;
  release_id: number;
  title: string;
  artist: string;
  best_source_platform: string;
  best_source_price: number;
  best_source_currency: string;
  best_target_platform: string;
  best_target_price: number;
  best_target_currency: string;
  profit_amount: number;
  profit_percentage: number;
  score: number;
  thumbnail?: string;
  genre?: string[];
  year?: number;
  country?: string;
}

interface DataTableProps {
  data: ProfitResult[];
  isLoading: boolean;
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
}

export default function DataTable({ data, isLoading, onSortChange }: DataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'profit_amount', desc: true },
  ]);

  const columnHelper = createColumnHelper<ProfitResult>();

  const columns = [
    // サムネイル列
    columnHelper.accessor('thumbnail', {
      header: '',
      cell: (info) => 
        info.getValue() ? (
          <img 
            src={info.getValue()} 
            alt={info.row.original.title} 
            className="w-12 h-12 object-cover rounded"
          />
        ) : (
          <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
            <span className="text-gray-400">No image</span>
          </div>
        ),
      enableSorting: false,
    }),
    
    // タイトル列
    columnHelper.accessor('title', {
      header: '商品名',
      cell: (info) => (
        <div>
          <div className="font-medium">{info.getValue()}</div>
          {info.row.original.artist && (
            <div className="text-sm text-gray-500">{info.row.original.artist}</div>
          )}
          {info.row.original.year && (
            <div className="text-xs text-gray-400">{info.row.original.year}</div>
          )}
        </div>
      ),
    }),
    
    // 仕入れ情報列
    columnHelper.accessor('best_source_platform', {
      header: '仕入れ元',
      cell: (info) => (
        <div>
          <div className="font-medium">{info.getValue()}</div>
          <div className="text-sm">
            {new Intl.NumberFormat('ja-JP', {
              style: 'currency',
              currency: info.row.original.best_source_currency,
            }).format(info.row.original.best_source_price)}
          </div>
        </div>
      ),
    }),
    
    // 販売先情報列
    columnHelper.accessor('best_target_platform', {
      header: '販売先',
      cell: (info) => (
        <div>
          <div className="font-medium">{info.getValue()}</div>
          <div className="text-sm">
            {new Intl.NumberFormat('ja-JP', {
              style: 'currency',
              currency: info.row.original.best_target_currency,
            }).format(info.row.original.best_target_price)}
          </div>
        </div>
      ),
    }),
    
    // 利益額列
    columnHelper.accessor('profit_amount', {
      header: '利益額',
      cell: (info) => (
        <div className="font-medium text-green-600">
          {new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: 'JPY',
          }).format(info.getValue())}
        </div>
      ),
    }),
    
    // 利益率列
    columnHelper.accessor('profit_percentage', {
      header: '利益率',
      cell: (info) => (
        <div className="font-medium">
          {info.getValue().toFixed(1)}%
        </div>
      ),
    }),
    
    // スコア列
    columnHelper.accessor('score', {
      header: 'スコア',
      cell: (info) => {
        const score = info.getValue();
        let colorClass = 'text-gray-600';
        
        if (score >= 80) {
          colorClass = 'text-green-600';
        } else if (score >= 60) {
          colorClass = 'text-blue-600';
        } else if (score >= 40) {
          colorClass = 'text-yellow-600';
        } else if (score >= 20) {
          colorClass = 'text-orange-600';
        } else {
          colorClass = 'text-red-600';
        }
        
        return (
          <div className={`font-bold ${colorClass}`}>
            {score.toFixed(1)}
          </div>
        );
      },
    }),
  ];

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
    },
    onSortingChange: (newSorting) => {
      const newSortingState = newSorting as SortingState;
      setSorting(newSortingState);
      
      if (newSortingState.length > 0) {
        const { id, desc } = newSortingState[0];
        onSortChange(id, desc ? 'desc' : 'asc');
      } else {
        // デフォルトのソート順に戻す
        onSortChange('profit_amount', 'desc');
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center space-x-1">
                      <span>
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                      </span>
                      <span>
                        {header.column.getIsSorted() ? (
                          header.column.getIsSorted() === 'asc' ? (
                            '🔼'
                          ) : (
                            '🔽'
                          )
                        ) : (
                          ''
                        )}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-4 text-center text-gray-500"
                >
                  データがありません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
