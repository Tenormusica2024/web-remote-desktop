$token = "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"
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent" = "PowerShell-GitHubAPI/1.0"
}
$body = '{"private": true}'

Write-Output "Attempting to change repository to private..."

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/Tenormusica2024/web-remote-desktop" -Method PATCH -Headers $headers -Body $body -ContentType "application/json"
    Write-Output "SUCCESS: Repository successfully changed to private"
    Write-Output "Private status: $($response.private)"
    Write-Output "Repository: $($response.full_name)"
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Output "Response Body: $responseBody"
        Write-Output "Status Code: $($_.Exception.Response.StatusCode)"
    }
}