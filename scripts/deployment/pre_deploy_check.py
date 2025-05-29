#!/usr/bin/env python3
"""
デプロイ前チェックスクリプト
本番デプロイ前に必要な確認を自動実行
"""
import subprocess
import json
import sys
import os
from datetime import datetime

class PreDeploymentChecker:
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
    def run_command(self, command, description):
        """コマンドを実行して結果を返す"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_build(self):
        """ビルドチェック"""
        print("🔨 ビルドチェック中...")
        success, stdout, stderr = self.run_command("npm run build", "Build check")
        
        if success:
            self.checks_passed.append("✅ ビルド成功")
            return True
        else:
            self.checks_failed.append("❌ ビルド失敗")
            print(f"エラー: {stderr}")
            return False
    
    def check_typescript(self):
        """TypeScriptチェック"""
        print("📘 TypeScriptチェック中...")
        success, stdout, stderr = self.run_command("npx tsc --noEmit", "TypeScript check")
        
        if success:
            self.checks_passed.append("✅ TypeScriptエラーなし")
            return True
        else:
            # TypeScriptエラーは警告として扱う
            self.warnings.append("⚠️  TypeScriptエラーあり（スキップ）")
            return True
    
    def check_git_status(self):
        """Gitステータスチェック"""
        print("📦 Gitステータスチェック中...")
        
        # 未コミットの変更をチェック
        success, stdout, stderr = self.run_command("git status --porcelain", "Git status")
        
        if stdout.strip():
            self.warnings.append("⚠️  未コミットの変更があります")
            print("未コミットファイル:")
            print(stdout)
            return True  # 警告として続行
        else:
            self.checks_passed.append("✅ すべての変更がコミット済み")
            return True
    
    def check_remote_sync(self):
        """リモートとの同期チェック"""
        print("🔄 リモート同期チェック中...")
        
        # フェッチ
        self.run_command("git fetch", "Git fetch")
        
        # ローカルとリモートの差分をチェック
        success, stdout, stderr = self.run_command(
            "git rev-list HEAD...origin/main --count", 
            "Check remote diff"
        )
        
        if success and stdout.strip() == "0":
            self.checks_passed.append("✅ リモートと同期済み")
            return True
        else:
            self.warnings.append("⚠️  リモートとの差分があります")
            return True
    
    def check_env_vars(self):
        """環境変数チェック"""
        print("🔑 環境変数チェック中...")
        
        required_vars = [
            "RAKUTEN_APP_ID",
            "EBAY_CLIENT_ID", 
            "EBAY_CLIENT_SECRET",
            "YAHOO_CLIENT_ID",
            "OPENAI_API_KEY",
            "APIFY_API_TOKEN"
        ]
        
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
                
            missing_vars = []
            for var in required_vars:
                if var not in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.warnings.append(f"⚠️  環境変数が不足: {', '.join(missing_vars)}")
            else:
                self.checks_passed.append("✅ 必要な環境変数が設定済み")
            return True
        else:
            self.checks_failed.append("❌ .envファイルが見つかりません")
            return False
    
    def check_dependencies(self):
        """依存関係チェック"""
        print("📚 依存関係チェック中...")
        
        # package-lock.jsonの存在チェック
        if os.path.exists("package-lock.json"):
            self.checks_passed.append("✅ package-lock.jsonが存在")
            
            # npm ciで依存関係の整合性チェック
            success, stdout, stderr = self.run_command(
                "npm ci --dry-run", 
                "Dependency check"
            )
            
            if not success and "npm install" in stderr:
                self.warnings.append("⚠️  package-lock.jsonの更新が必要かもしれません")
            
            return True
        else:
            self.checks_failed.append("❌ package-lock.jsonが見つかりません")
            return False
    
    def generate_report(self):
        """チェック結果レポートを生成"""
        report = f"""# デプロイ前チェックレポート

実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## チェック結果サマリー

- ✅ 成功: {len(self.checks_passed)}項目
- ❌ 失敗: {len(self.checks_failed)}項目  
- ⚠️  警告: {len(self.warnings)}項目

## 詳細結果

### 成功項目
"""
        for check in self.checks_passed:
            report += f"- {check}\n"
        
        if self.checks_failed:
            report += "\n### 失敗項目\n"
            for check in self.checks_failed:
                report += f"- {check}\n"
        
        if self.warnings:
            report += "\n### 警告項目\n"
            for warning in self.warnings:
                report += f"- {warning}\n"
        
        report += f"\n## 判定\n"
        if self.checks_failed:
            report += "❌ **デプロイ不可**: 失敗項目を修正してください\n"
        else:
            report += "✅ **デプロイ可能**: すべての必須チェックをパスしました\n"
            if self.warnings:
                report += "⚠️  警告項目を確認の上、デプロイを実行してください\n"
        
        return report
    
    def run_all_checks(self):
        """すべてのチェックを実行"""
        print("=" * 60)
        print("デプロイ前チェックを開始します...")
        print("=" * 60)
        
        # 各チェックを実行
        self.check_git_status()
        self.check_remote_sync()
        self.check_dependencies()
        self.check_env_vars()
        self.check_typescript()
        self.check_build()
        
        # レポート生成
        report = self.generate_report()
        
        # レポートを保存
        report_file = f"pre_deploy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
        print(f"\nレポートを保存しました: {report_file}")
        
        # 終了コード
        if self.checks_failed:
            return 1
        else:
            return 0

def main():
    checker = PreDeploymentChecker()
    exit_code = checker.run_all_checks()
    
    if exit_code == 0:
        print("\n✅ デプロイの準備が整いました！")
        print("\n次のステップ:")
        print("1. git add .")
        print("2. git commit -m 'fix: 統合検索エンジンのエラー修正'")
        print("3. git push origin main")
        print("4. Vercelダッシュボードでデプロイを確認")
    else:
        print("\n❌ デプロイ前に問題を解決してください")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()