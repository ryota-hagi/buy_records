#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/hagiryouta/records/src')

try:
    from supabase import create_client, Client
    
    # Supabase接続（実際の認証情報）
    url = "https://ggvuuixcswldxfeygxvy.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdndnV1aXhjc3dsZHhmZXlneHZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczMTcxMzAsImV4cCI6MjA2Mjg5MzEzMH0.s-P9q19IqqZDotGeZlrbsBcpHFGxbfH_okZ78MpjdR8"
    supabase: Client = create_client(url, key)
    
    # 最新のタスクIDを取得
    task_response = supabase.table('search_tasks').select('*').order('created_at', desc=True).limit(1).execute()
    if task_response.data:
        task_id = task_response.data[0]['id']
        print(f'最新タスクID: {task_id}')
        print(f'JANコード: {task_response.data[0].get("jan_code", "不明")}')
        print(f'ステータス: {task_response.data[0].get("status", "不明")}')
        print()
        
        # プラットフォーム別の検索結果件数を確認
        platforms = ['yahoo_shopping', 'mercari', 'ebay']
        total_by_platform = {}
        
        for platform in platforms:
            response = supabase.table('search_results').select('*').eq('task_id', task_id).eq('platform', platform).execute()
            count = len(response.data)
            total_by_platform[platform] = count
            print(f'{platform}: {count}件')
            
            # 最初の3件のタイトルを表示
            if response.data:
                print(f'  サンプル:')
                for i, item in enumerate(response.data[:3]):
                    title = item.get('title', 'タイトルなし')
                    price = item.get('price', 'N/A')
                    print(f'    {i+1}. {title} - ¥{price}')
            else:
                print(f'  データなし')
            print()
        
        # 全体の件数も確認
        total_response = supabase.table('search_results').select('*').eq('task_id', task_id).execute()
        total_count = len(total_response.data)
        print(f'全体の検索結果: {total_count}件')
        print()
        
        # 各プラットフォームの詳細分析
        print('=== プラットフォーム別詳細分析 ===')
        for platform, count in total_by_platform.items():
            if count > 0:
                print(f'{platform}: {count}件取得済み ✅')
            else:
                print(f'{platform}: データなし ❌')
        
        # 目標達成状況
        print()
        print('=== 目標達成状況 ===')
        target_per_platform = 20
        all_platforms_success = True
        
        for platform, count in total_by_platform.items():
            if count >= target_per_platform:
                print(f'{platform}: {count}件 (目標{target_per_platform}件達成) ✅')
            else:
                print(f'{platform}: {count}件 (目標{target_per_platform}件未達成) ❌')
                all_platforms_success = False
        
        if all_platforms_success:
            print('\n🎉 全プラットフォームで目標達成！')
        else:
            print('\n⚠️  一部プラットフォームで目標未達成')
            
    else:
        print('タスクが見つかりません')
        
except Exception as e:
    print(f'エラーが発生しました: {e}')
    import traceback
    traceback.print_exc()
