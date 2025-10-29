#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code音声通知統合スクリプト（MCP直接呼び出し版）
VOICEVOX MCPサーバーを直接呼び出して音声通知を実行
"""

import subprocess
import sys
import json
import os
from pathlib import Path
import http.client
import urllib.parse

class ClaudeVoiceNotifier:
    """Claude Code音声通知クラス（MCP直接呼び出し）"""
    
    def __init__(self):
        self.root = Path(__file__).resolve().parent
        self.voicevox_api = "localhost:50021"
        self.speaker_id = 3  # ずんだもん ノーマル
    
    def notify(self, message: str, status: str = "progress"):
        """
        音声通知を実行（VOICEVOX API直接呼び出し）
        
        Args:
            message: 通知メッセージ（100文字以内）
            status: タスク状態 (start/progress/complete/error)
        
        Returns:
            bool: 成功時True、失敗時False
        """
        if len(message) > 100:
            message = message[:97] + "..."
        
        try:
            # VOICEVOX API直接呼び出し
            return self._synthesize_and_play(message)
                
        except Exception as e:
            print(f"⚠️ 音声通知失敗（フォールバック試行）: {e}")
            # フォールバック: GitHub Issue経由
            return self._fallback_issue_notification(message, status)
    
    def _synthesize_and_play(self, text: str) -> bool:
        """
        VOICEVOX APIで音声合成・再生
        
        Args:
            text: 読み上げるテキスト
        
        Returns:
            bool: 成功時True
        """
        try:
            # 1. 音声クエリ生成
            conn = http.client.HTTPConnection(self.voicevox_api, timeout=5)
            query_path = f"/audio_query?text={urllib.parse.quote(text)}&speaker={self.speaker_id}"
            
            conn.request("POST", query_path)
            response = conn.getresponse()
            
            if response.status != 200:
                print(f"❌ 音声クエリ生成失敗: HTTP {response.status}")
                return False
            
            audio_query = response.read().decode('utf-8')
            conn.close()
            
            # 2. 音声合成
            conn = http.client.HTTPConnection(self.voicevox_api, timeout=10)
            synthesis_path = f"/synthesis?speaker={self.speaker_id}"
            headers = {"Content-Type": "application/json; charset=utf-8"}
            
            # UTF-8でエンコード
            audio_query_bytes = audio_query.encode('utf-8')
            
            conn.request("POST", synthesis_path, audio_query_bytes, headers)
            response = conn.getresponse()
            
            if response.status != 200:
                print(f"❌ 音声合成失敗: HTTP {response.status}")
                return False
            
            audio_data = response.read()
            conn.close()
            
            # 3. 一時ファイルに保存
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            
            # 4. 音声再生（Windows）
            if sys.platform == "win32":
                powershell_cmd = f"(New-Object System.Media.SoundPlayer '{temp_file.name}').PlaySync()"
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True,
                    timeout=15
                )
                
                # 再生完了後にファイル削除
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                
                if result.returncode == 0:
                    print(f"✅ 音声通知成功: {text}")
                    return True
                else:
                    print(f"⚠️ 音声再生失敗: {result.stderr.decode('utf-8', errors='ignore')}")
                    return False
            else:
                print("⚠️ Windows以外のOSは未対応")
                return False
                
        except Exception as e:
            print(f"❌ 音声合成エラー: {e}")
            return False
    
    def _fallback_issue_notification(self, message: str, status: str) -> bool:
        """
        フォールバック: GitHub Issue経由で通知
        
        Args:
            message: 通知メッセージ
            status: タスク状態
        
        Returns:
            bool: 成功時True
        """
        try:
            cmd = [
                "python",
                str(self.root / "task_complete_private.py"),
                f"🔊 音声通知（フォールバック）: {message} (status: {status})"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.root)
            )
            
            if result.returncode == 0:
                print(f"✅ フォールバック通知成功: {message}")
                return True
            else:
                print(f"⚠️ フォールバック通知失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ フォールバック通知エラー: {e}")
            return False
    
    def notify_task_start(self, task_name: str):
        """
        タスク開始通知（具体的なタスク名を読み上げ）
        
        Args:
            task_name: 開始するタスクの具体的な名前
        """
        return self.notify(f"{task_name}を開始します", "start")
    
    def notify_deploy_start(self, target: str = ""):
        """
        デプロイ開始通知
        
        Args:
            target: デプロイ対象（例: "sound-platform"）
        """
        message = f"{target}のデプロイを開始します" if target else "デプロイを開始します"
        return self.notify(message, "start")
    
    def notify_deploy_complete(self, target: str = ""):
        """
        デプロイ完了通知
        
        Args:
            target: デプロイ対象（例: "sound-platform"）
        """
        message = f"{target}のデプロイが完了しました" if target else "デプロイが完了しました"
        return self.notify(message, "complete")
    
    def notify_error(self, error_detail: str):
        """
        エラー発生通知（具体的なエラー内容を読み上げ）
        
        Args:
            error_detail: エラーの具体的な内容
        """
        return self.notify(f"{error_detail}が発生しました", "error")
    
    def notify_task_complete(self, task_detail: str):
        """
        タスク完了通知（具体的な完了内容を読み上げ）
        
        Args:
            task_detail: 完了した作業の具体的な内容
        """
        return self.notify(f"{task_detail}が完了しました", "complete")
    
    def notify_git_push(self, branch: str = "main"):
        """
        Git push完了通知
        
        Args:
            branch: プッシュしたブランチ名
        """
        return self.notify(f"{branch}ブランチへのプッシュが完了しました", "complete")
    
    def notify_file_edit(self, filename: str):
        """
        ファイル編集完了通知
        
        Args:
            filename: 編集したファイル名
        """
        return self.notify(f"{filename}の編集が完了しました", "complete")
    
    def notify_question(self, question: str):
        """
        質問通知（Claudeからユーザーへの質問を読み上げ）
        
        Args:
            question: 質問内容
        """
        return self.notify(question, "progress")
    
    def notify_answer(self, answer: str):
        """
        回答通知（ユーザーの質問への回答を読み上げ）
        
        Args:
            answer: 回答内容
        """
        return self.notify(answer, "progress")
    
    def notify_response(self, response: str):
        """
        一般的な応答通知（確認・報告などを読み上げ）
        
        Args:
            response: 応答内容
        """
        return self.notify(response, "progress")

def main():
    """メイン実行関数"""
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    notifier = ClaudeVoiceNotifier()
    
    if len(sys.argv) < 2:
        print("使用方法: python claude_voice_notification.py <コマンド> <具体的な内容>")
        print()
        print("コマンド:")
        print("  task_start <タスク名>          - タスク開始通知")
        print("  deploy_start [対象]            - デプロイ開始通知")
        print("  deploy_complete [対象]         - デプロイ完了通知")
        print("  error <エラー詳細>             - エラー発生通知")
        print("  task_complete <完了内容>       - タスク完了通知")
        print("  git_push [ブランチ名]          - Git push完了通知")
        print("  file_edit <ファイル名>         - ファイル編集完了通知")
        print("  question <質問内容>            - 質問通知")
        print("  answer <回答内容>              - 回答通知")
        print("  response <応答内容>            - 一般応答通知")
        print("  custom <メッセージ> [status]   - カスタム通知")
        print()
        print("例:")
        print("  python claude_voice_notification.py task_complete 'UI修正とデプロイ'")
        print("  python claude_voice_notification.py deploy_complete 'sound-platform'")
        print("  python claude_voice_notification.py git_push 'feature-branch'")
        print("  python claude_voice_notification.py question 'どちらのサービスにデプロイしますか？'")
        print("  python claude_voice_notification.py answer '現在のリビジョンは100です'")
        print("  python claude_voice_notification.py response '承知しました。実装を開始します'")
        return
    
    command = sys.argv[1]
    
    if command == "task_start":
        if len(sys.argv) < 3:
            print("❌ タスク名を指定してください")
            return
        task_name = sys.argv[2]
        notifier.notify_task_start(task_name)
    
    elif command == "deploy_start":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        notifier.notify_deploy_start(target)
    
    elif command == "deploy_complete":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        notifier.notify_deploy_complete(target)
    
    elif command == "error":
        if len(sys.argv) < 3:
            print("❌ エラー詳細を指定してください")
            return
        error_detail = sys.argv[2]
        notifier.notify_error(error_detail)
    
    elif command == "task_complete":
        if len(sys.argv) < 3:
            print("❌ 完了内容を指定してください")
            return
        task_detail = sys.argv[2]
        notifier.notify_task_complete(task_detail)
    
    elif command == "git_push":
        branch = sys.argv[2] if len(sys.argv) > 2 else "main"
        notifier.notify_git_push(branch)
    
    elif command == "file_edit":
        if len(sys.argv) < 3:
            print("❌ ファイル名を指定してください")
            return
        filename = sys.argv[2]
        notifier.notify_file_edit(filename)
    
    elif command == "question":
        if len(sys.argv) < 3:
            print("❌ 質問内容を指定してください")
            return
        question = sys.argv[2]
        notifier.notify_question(question)
    
    elif command == "answer":
        if len(sys.argv) < 3:
            print("❌ 回答内容を指定してください")
            return
        answer = sys.argv[2]
        notifier.notify_answer(answer)
    
    elif command == "response":
        if len(sys.argv) < 3:
            print("❌ 応答内容を指定してください")
            return
        response = sys.argv[2]
        notifier.notify_response(response)
    
    elif command == "custom":
        if len(sys.argv) < 3:
            print("❌ カスタム通知にはメッセージが必要です")
            return
        message = sys.argv[2]
        status = sys.argv[3] if len(sys.argv) > 3 else "progress"
        notifier.notify(message, status)
    
    else:
        print(f"❌ 不明なコマンド: {command}")

if __name__ == "__main__":
    main()
