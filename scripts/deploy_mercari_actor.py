#!/usr/bin/env python3
"""
Mercari Apify Actorのデプロイスクリプト
カスタムMercariスクレイピングActorをApifyにプッシュ
"""

import subprocess
import os
import sys
import json

def run_command(command, cwd=None):
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"コマンド実行エラー: {command}")
        print(f"エラー出力: {e.stderr}")
        return None

def check_apify_cli():
    """Apify CLIがインストールされているかチェック"""
    print("Apify CLIの確認中...")
    result = run_command("apify --version")
    if result:
        print(f"✅ Apify CLI バージョン: {result}")
        return True
    else:
        print("❌ Apify CLIがインストールされていません")
        return False

def check_apify_login():
    """Apifyにログインしているかチェック"""
    print("Apifyログイン状態の確認中...")
    result = run_command("apify info")
    if result and "User ID" in result:
        print("✅ Apifyにログイン済み")
        return True
    else:
        print("❌ Apifyにログインしていません")
        return False

def deploy_actor():
    """ActorをApifyにデプロイ"""
    actor_dir = "mercari-scraper-actor"
    
    if not os.path.exists(actor_dir):
        print(f"❌ Actorディレクトリが見つかりません: {actor_dir}")
        return False
    
    print(f"Actorのデプロイを開始: {actor_dir}")
    
    # Actorディレクトリに移動してプッシュ
    result = run_command("apify push", cwd=actor_dir)
    
    if result:
        print("✅ Actorのデプロイが完了しました")
        print(f"デプロイ結果: {result}")
        return True
    else:
        print("❌ Actorのデプロイに失敗しました")
        return False

def test_actor_locally():
    """Actorをローカルでテスト"""
    actor_dir = "mercari-scraper-actor"
    
    print("Actorのローカルテストを開始...")
    
    # テスト用の入力データを作成
    test_input = {
        "searchKeyword": "Nintendo Switch",
        "maxItems": 5,
        "includeImages": True
    }
    
    # 入力ファイルを作成
    input_file = os.path.join(actor_dir, "apify_storage", "key_value_stores", "default", "INPUT.json")
    os.makedirs(os.path.dirname(input_file), exist_ok=True)
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(test_input, f, ensure_ascii=False, indent=2)
    
    # Actorを実行
    result = run_command("apify run", cwd=actor_dir)
    
    if result:
        print("✅ Actorのローカルテストが完了しました")
        return True
    else:
        print("❌ Actorのローカルテストに失敗しました")
        return False

def main():
    print("=== Mercari Apify Actor デプロイスクリプト ===")
    
    # 1. Apify CLIの確認
    if not check_apify_cli():
        print("\nApify CLIをインストールしてください:")
        print("npm install -g apify-cli")
        sys.exit(1)
    
    # 2. ログイン状態の確認
    if not check_apify_login():
        print("\nApifyにログインしてください:")
        print("apify login")
        print("ブラウザが開くので、Apifyアカウントでログインしてください")
        sys.exit(1)
    
    # 3. ローカルテスト（オプション）
    print("\n=== ローカルテスト ===")
    test_choice = input("ローカルでActorをテストしますか？ (y/n): ").lower()
    if test_choice == 'y':
        if not test_actor_locally():
            print("ローカルテストに失敗しました。続行しますか？")
            continue_choice = input("続行する (y/n): ").lower()
            if continue_choice != 'y':
                sys.exit(1)
    
    # 4. Apifyにデプロイ
    print("\n=== Apifyデプロイ ===")
    deploy_choice = input("ActorをApifyにデプロイしますか？ (y/n): ").lower()
    if deploy_choice == 'y':
        if deploy_actor():
            print("\n🎉 デプロイが完了しました！")
            print("Apify Consoleでアクターを確認してください:")
            print("https://console.apify.com/actors")
        else:
            print("\n❌ デプロイに失敗しました")
            sys.exit(1)
    
    print("\n=== 次のステップ ===")
    print("1. Apify ConsoleでActorが正常にデプロイされたことを確認")
    print("2. Actorを実行してテスト")
    print("3. APIエンドポイントでActorを呼び出すように設定を更新")
    print("4. 本番環境でテスト")

if __name__ == "__main__":
    main()
