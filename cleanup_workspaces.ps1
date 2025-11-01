# PowerShell script to clean up old workspace directories

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Cleaning up old workspace directories" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Find all workspace directories
$workspaceDirs = Get-ChildItem -Path "." -Directory | Where-Object { $_.Name -match "^workspace" }

if ($workspaceDirs.Count -eq 0) {
    Write-Host "`n✅ No workspace directories found to clean" -ForegroundColor Green
    exit 0
}

Write-Host "`n📋 Found $($workspaceDirs.Count) workspace directory(ies):" -ForegroundColor Yellow
foreach ($dir in $workspaceDirs) {
    Write-Host "   - $($dir.Name)" -ForegroundColor White
}

Write-Host "`nCleaning up..." -ForegroundColor Yellow

# Remove each directory
$cleaned = 0
$failed = 0

foreach ($dir in $workspaceDirs) {
    try {
        Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Cleaned: $($dir.Name)" -ForegroundColor Green
        $cleaned++
    }
    catch {
        Write-Host "❌ Failed to clean: $($dir.Name) - $_" -ForegroundColor Red
        $failed++
        
        # Try renaming as last resort
        try {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupName = "$($dir.Name)_cleanup_$timestamp"
            Rename-Item -Path $dir.FullName -NewName $backupName -ErrorAction Stop
            Write-Host "   ⚠️  Renamed to: $backupName" -ForegroundColor Yellow
        }
        catch {
            Write-Host "   ❌ Could not rename either" -ForegroundColor Red
        }
    }
}

# Summary
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "📊 Cleanup Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Cleaned: $cleaned directory(ies)" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "❌ Failed: $failed directory(ies)" -ForegroundColor Red
}
Write-Host "================================================`n" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host "✅ All workspaces cleaned successfully!`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some workspaces could not be cleaned`n" -ForegroundColor Yellow
    exit 1
}

