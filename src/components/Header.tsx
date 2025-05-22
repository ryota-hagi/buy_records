import React from 'react';

export default function Header() {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-md">
      <div className="container mx-auto">
        <h1 className="text-2xl font-bold">レコード販売データ分析ダッシュボード</h1>
        <p className="text-sm mt-1">複数プラットフォームの価格比較と利益計算結果</p>
      </div>
    </header>
  );
}
