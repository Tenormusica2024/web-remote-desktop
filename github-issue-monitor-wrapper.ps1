# GitHub Issue Monitor PowerShell Wrapper
# GITHUB_TOKEN環境変数の影響を受けずにGitHub APIにアクセス

param (
    [string]$Action = "get-comments"
)

# 環境変数をクリア
Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue

# GitHub CLIのフルパス
$GH_PATH = "C:\Program Files\GitHub CLI\gh.exe"
$OWNER = "Tenormusica2024"
$REPO = "Private"
$ISSUE = 5

if ($Action -eq "get-comments") {
    # コメントを取得してJSON形式で返す
    & $GH_PATH api "repos/$OWNER/$REPO/issues/$ISSUE/comments" --paginate
    exit $LASTEXITCODE
}
elseif ($Action -eq "post-comment") {
    # 標準入力からコメント本文を読む
    $body = [Console]::In.ReadToEnd()
    $escapedBody = $body -replace '"', '\"' -replace "`n", '\n' -replace "`r", ''
    
    # コメント投稿
    $json = "{`"body`":`"$escapedBody`"}"
    $json | & $GH_PATH api "repos/$OWNER/$REPO/issues/$ISSUE/comments" --method POST --input -
    exit $LASTEXITCODE
}