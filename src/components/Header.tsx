import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Header() {
  const pathname = usePathname();
  
  return (
    <header className="bg-blue-600 text-white p-4 shadow-md">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center">
          <div>
            <h1 className="text-2xl font-bold">レコード販売データ分析ダッシュボード</h1>
            <p className="text-sm mt-1">複数プラットフォームの価格比較と利益計算結果</p>
          </div>
          
          <nav className="mt-4 md:mt-0">
            <ul className="flex space-x-6">
              <li>
                <Link 
                  href="/" 
                  className={`hover:text-blue-200 ${pathname === '/' ? 'font-bold border-b-2 border-white pb-1' : ''}`}
                >
                  ホーム
                </Link>
              </li>
              <li>
                <Link 
                  href="/search" 
                  className={`hover:text-blue-200 ${pathname === '/search' ? 'font-bold border-b-2 border-white pb-1' : ''}`}
                >
                  検索
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}
