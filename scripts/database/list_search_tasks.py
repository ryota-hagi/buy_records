#!/usr/bin/env python
"""
検索タスクのリストや詳細を表示するスクリプト

使用方法:
    python scripts/list_search_tasks.py [オプション]
    python scripts/list_search_tasks.py --task-id TASK_ID

オプション:
    --task-id TASK_ID      特定のタスクの詳細を表示
    --status STATUS        ステータスでフィルタリング（pending, running, completed, failed, cancelled）
                           カンマ区切りで複数指定可能
    --limit LIMIT          表示する最大件数（デフォルト: 10）
    --offset OFFSET        オフセット（ページネーション用、デフォルト: 0）
    --format FORMAT        出力フォーマット（text, json, デフォルト: text）
"""

import argparse
import json
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.search.task_manager import SearchTaskManager, TaskStatus

def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description='検索タスクのリストや詳細を表示するスクリプト')
    
    parser.add_argument(
        '--task-id',
        type=str,
        help='特定のタスクの詳細を表示'
    )
    
    parser.add_argument(
        '--status',
        type=str,
        help='ステータスでフィルタリング（pending, running, completed, failed, cancelled）'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='表示する最大件数（デフォルト: 10）'
    )
    
    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help='オフセット（ページネーション用、デフォルト: 0）'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='出力フォーマット（text, json, デフォルト: text）'
    )
    
    return parser.parse_args()

def format_task_for_display(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    表示用にタスク情報をフォーマットする
    
    Args:
        task: タスク情報
        
    Returns:
        Dict[str, Any]: フォーマットされたタスク情報
    """
    # 表示用にコピーを作成
    display_task = task.copy()
    
    # 検索パラメータを整形
    if 'search_params' in display_task and display_task['search_params']:
        # 検索クエリの概要を作成
        search_summary = []
        
        params = display_task['search_params']
        
        if 'query' in params:
            search_summary.append(f"クエリ: {params['query']}")
        
        if 'artist' in params:
            search_summary.append(f"アーティスト: {params['artist']}")
        
        if 'title' in params:
            search_summary.append(f"タイトル: {params['title']}")
        
        if 'release_id' in params:
            search_summary.append(f"リリースID: {params['release_id']}")
        
        if 'platforms' in params:
            platforms = ', '.join(params['platforms'])
            search_summary.append(f"プラットフォーム: {platforms}")
        
        display_task['search_summary'] = ' | '.join(search_summary)
    
    # 結果の概要を作成
    if 'result' in display_task and display_task['result']:
        result = display_task['result']
        
        if 'integrated_results' in result:
            integrated = result['integrated_results']
            count = integrated.get('count', 0)
            display_task['result_summary'] = f"{count}件の結果"
        else:
            display_task['result_summary'] = "結果なし"
    else:
        display_task['result_summary'] = "結果なし"
    
    # 実行時間を計算
    if display_task.get('completed_at') and display_task.get('created_at'):
        created = datetime.fromisoformat(display_task['created_at'].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(display_task['completed_at'].replace('Z', '+00:00'))
        execution_time = (completed - created).total_seconds()
        display_task['execution_time'] = f"{execution_time:.2f}秒"
    else:
        display_task['execution_time'] = "未完了"
    
    return display_task

def display_task_list(tasks: List[Dict[str, Any]], format_type: str) -> None:
    """
    タスクリストを表示する
    
    Args:
        tasks: タスクのリスト
        format_type: 出力フォーマット（text, json）
    """
    if not tasks:
        print("タスクが見つかりませんでした")
        return
    
    if format_type == 'json':
        # JSON形式で出力
        formatted_tasks = [format_task_for_display(task) for task in tasks]
        print(json.dumps(formatted_tasks, indent=2, default=str))
        return
    
    # テキスト形式で出力
    print(f"検索タスク一覧（{len(tasks)}件）:")
    print("-" * 100)
    print(f"{'ID':<36} | {'名前':<20} | {'ステータス':<10} | {'作成日時':<19} | {'概要'}")
    print("-" * 100)
    
    for task in tasks:
        formatted_task = format_task_for_display(task)
        
        # 日時のフォーマット
        created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        
        # 検索概要
        search_summary = formatted_task.get('search_summary', '')
        if len(search_summary) > 40:
            search_summary = search_summary[:37] + '...'
        
        print(f"{task['id']:<36} | {task['name']:<20} | {task['status']:<10} | {created_at} | {search_summary}")
    
    print("-" * 100)

def display_task_detail(task: Dict[str, Any], format_type: str) -> None:
    """
    タスク詳細を表示する
    
    Args:
        task: タスク情報
        format_type: 出力フォーマット（text, json）
    """
    if not task:
        print("タスクが見つかりませんでした")
        return
    
    if format_type == 'json':
        # JSON形式で出力
        print(json.dumps(task, indent=2, default=str))
        return
    
    # テキスト形式で出力
    formatted_task = format_task_for_display(task)
    
    print(f"タスク詳細: {task['id']}")
    print("=" * 100)
    print(f"名前: {task['name']}")
    print(f"ステータス: {task['status']}")
    print(f"作成日時: {task['created_at']}")
    print(f"更新日時: {task['updated_at']}")
    
    if task.get('completed_at'):
        print(f"完了日時: {task['completed_at']}")
    
    print(f"実行時間: {formatted_task['execution_time']}")
    
    # 検索パラメータ
    print("\n検索パラメータ:")
    print("-" * 100)
    
    if task.get('search_params'):
        for key, value in task['search_params'].items():
            print(f"{key}: {value}")
    else:
        print("検索パラメータなし")
    
    # 結果
    print("\n検索結果:")
    print("-" * 100)
    
    if task.get('result'):
        # 統合結果の概要
        if 'integrated_results' in task['result']:
            integrated = task['result']['integrated_results']
            count = integrated.get('count', 0)
            print(f"統合結果: {count}件")
            
            # 上位5件の結果を表示
            if count > 0 and 'items' in integrated:
                print("\n上位5件の結果:")
                for i, item in enumerate(integrated['items'][:5], 1):
                    print(f"\n{i}. {item.get('title', 'タイトルなし')}")
                    if 'artist' in item:
                        print(f"   アーティスト: {item['artist']}")
                    print(f"   プラットフォーム: {item.get('platform', '不明')}")
                    print(f"   価格: {item.get('price', '不明')}")
                    if 'profit_amount' in item:
                        print(f"   利益: {item['profit_amount']}")
                    if 'score' in item:
                        print(f"   スコア: {item['score']}")
        
        # プラットフォーム別結果
        if 'platform_results' in task['result']:
            print("\nプラットフォーム別結果:")
            for platform, result in task['result']['platform_results'].items():
                if 'error' in result:
                    print(f"  {platform}: エラー - {result['error']}")
                else:
                    count = result.get('count', 0)
                    print(f"  {platform}: {count}件")
    else:
        print("結果なし")
    
    # エラー
    if task.get('error'):
        print("\nエラー:")
        print("-" * 100)
        print(task['error'])
    
    print("=" * 100)

def main():
    """メイン関数"""
    args = parse_args()
    
    # タスクマネージャーを初期化
    task_manager = SearchTaskManager()
    
    # 特定のタスクの詳細を表示
    if args.task_id:
        task = task_manager.get_task(args.task_id)
        display_task_detail(task, args.format)
        return
    
    # ステータスでフィルタリング
    status_filter = None
    if args.status:
        status_values = [s.strip() for s in args.status.split(',')]
        status_filter = [TaskStatus(s) for s in status_values if s in [e.value for e in TaskStatus]]
    
    # タスクリストを取得
    tasks = task_manager.list_tasks(
        limit=args.limit,
        offset=args.offset,
        status=status_filter
    )
    
    # タスクリストを表示
    display_task_list(tasks, args.format)

if __name__ == '__main__':
    main()
