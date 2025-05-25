'use client';

import React, { useState } from 'react';

export interface SearchFormData {
  jan_code: string;
}

interface SearchFormProps {
  onSubmit: (data: SearchFormData) => void;
  isSubmitting: boolean;
}

export default function SearchForm({ onSubmit, isSubmitting }: SearchFormProps) {
  const [formData, setFormData] = useState<SearchFormData>({
    jan_code: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateJANCode = (janCode: string): boolean => {
    // JANコードのバリデーション（8桁または13桁の数字）
    const cleanCode = janCode.replace(/\D/g, ''); // 数字以外をすべて除去
    return /^\d{8}$|^\d{13}$/.test(cleanCode);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newErrors: Record<string, string> = {};
    
    // JANコードのバリデーション
    if (!formData.jan_code.trim()) {
      newErrors.jan_code = 'JANコードを入力してください';
    } else if (!validateJANCode(formData.jan_code)) {
      newErrors.jan_code = 'JANコードは8桁または13桁の数字で入力してください';
    }
    
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length === 0) {
      // スペースとハイフンを除去してクリーンなJANコードを送信
      const cleanJanCode = formData.jan_code.replace(/\D/g, '');
      onSubmit({ jan_code: cleanJanCode });
    }
  };

  const handleJANCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, jan_code: value }));
    
    // リアルタイムバリデーション
    if (errors.jan_code && value.trim()) {
      if (validateJANCode(value)) {
        setErrors(prev => ({ ...prev, jan_code: '' }));
      }
    }
  };

  const formatJANCode = (value: string) => {
    // 数字のみを抽出
    const numbers = value.replace(/\D/g, '');
    
    // 13桁の場合は区切りを入れる（例：4901234567890 → 4-901234-567890）
    if (numbers.length === 13) {
      return `${numbers.slice(0, 1)}-${numbers.slice(1, 7)}-${numbers.slice(7, 13)}`;
    }
    // 8桁の場合はそのまま
    else if (numbers.length === 8) {
      return numbers;
    }
    // それ以外はそのまま返す
    return numbers;
  };

  const handleJANCodeBlur = () => {
    // フォーカスが外れた時にフォーマット
    if (formData.jan_code) {
      const formatted = formatJANCode(formData.jan_code);
      setFormData(prev => ({ ...prev, jan_code: formatted }));
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">JANコード価格比較検索</h2>
      <p className="text-gray-600 mb-6">
        JANコードを入力すると、eBay、メルカリ、Yahoo!ショッピングから最安値を検索します。
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* JANコード入力 */}
        <div>
          <label htmlFor="jan_code" className="block text-sm font-medium text-gray-700 mb-1">
            JANコード <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="jan_code"
            value={formData.jan_code}
            onChange={handleJANCodeChange}
            onBlur={handleJANCodeBlur}
            placeholder="例: 4901234567890 または 12345678"
            className={`w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.jan_code ? 'border-red-500' : 'border-gray-300'
            }`}
            required
            disabled={isSubmitting}
            maxLength={15} // ハイフン込みで最大15文字
          />
          {errors.jan_code && (
            <p className="mt-1 text-sm text-red-600">{errors.jan_code}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            8桁または13桁の数字を入力してください。ハイフンは自動で挿入されます。
          </p>
        </div>

        {/* 検索対象プラットフォーム表示 */}
        <div className="bg-gray-50 p-4 rounded-md">
          <h3 className="text-sm font-medium text-gray-700 mb-2">検索対象プラットフォーム</h3>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">eBay</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">メルカリ</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">Yahoo!ショッピング</span>
            </div>
          </div>
        </div>

        {/* 注意事項 */}
        <div className="bg-blue-50 p-4 rounded-md">
          <h3 className="text-sm font-medium text-blue-800 mb-1">ご注意</h3>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• 検索には数分かかる場合があります</li>
            <li>• 表示価格には送料・手数料が含まれます</li>
            <li>• 検索結果は7日間保存されます</li>
            <li>• 最大20件の最安値商品を表示します</li>
          </ul>
        </div>

        {/* 送信ボタン */}
        <button
          type="submit"
          disabled={isSubmitting || !formData.jan_code.trim()}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isSubmitting ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              検索中...
            </div>
          ) : (
            '価格比較検索を開始'
          )}
        </button>
      </form>
    </div>
  );
}
