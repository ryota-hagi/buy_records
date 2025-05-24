#!/usr/bin/env python
"""
タスク処理プロセスを起動するスクリプト
"""

import subprocess
import sys
import os
import time

def start_task_processor():
    """タスク処理プロセスを起動する"""
    script_path = os.path.join(os.path.dirname(__file__), 'simple_task_runner.py')
    
    print("Starting task processor...")
    
    # バックグラウンドでタスク処理プロセスを起動
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Task processor started with PID: {process.pid}")
        
        # プロセスが正常に起動したかチェック
        time.sleep(2)
        if process.poll() is None:
            print("✓ Task processor is running")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Task processor failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to start task processor: {e}")
        return False

if __name__ == '__main__':
    success = start_task_processor()
    sys.exit(0 if success else 1)
