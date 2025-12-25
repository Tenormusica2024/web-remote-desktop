---
name: github-issue-reporter
description: |
  GitHub Issue報告の自動実行スキル。タスク完了時、確認・質問時、エラー発生時、待機時に必ずGitHub Issueへ報告する。
  Use this skill when: 作業完了、ユーザーへの質問、エラー報告、追加情報待ち、タスク状態変更など全ての状況で自動的に報告を実行する。
  CRITICAL: この報告は省略・延期・スキップできない。すべてのタスク状態変更で必ず実行する。
allowed-tools: Bash, Read
---

# GitHub Issue Reporter Skill

## Purpose

Claude Codeのすべての重要なアクションをGitHub Issueに自動報告するスキル。
ユーザーへの質問・確認・エラー報告などでも報告漏れが発生しないよう強制する。

## Mandatory Execution Triggers

以下の**すべての状況**で報告を実行する（例外なし）:

1. **タスク完了時** - 作業が完了した時
2. **ユーザーへの質問時** - 追加情報や確認が必要な時
3. **エラー発生時** - 処理中にエラーが発生した時
4. **待機時** - ユーザーの追加入力を待つ時
5. **作業中断時** - 何らかの理由で作業を停止する時
6. **重要な情報提供時** - 分析結果や調査結果を報告する時

## Execution Command

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "[報告内容]"
```

## Report Content Requirements

報告内容には以下を含める:

- 実施した作業の詳細
- 変更したファイル
- 実行結果
- エラー内容（該当する場合）
- ユーザーへの質問内容（該当する場合）
- 次のステップ

## ZERO TOLERANCE Policy

以下は完全禁止:

- 「後で報告する」→ 禁止
- 「まとめて報告する」→ 禁止
- 「報告しなくてもいいだろう」→ 禁止
- 「質問だから報告不要」→ 禁止
- 「エラーだから報告しない」→ 禁止

## Automatic Invocation Rule

このスキルはClaude Codeの回答生成時に自動的に呼び出される。
回答の最後に必ず報告コマンドを実行すること。
