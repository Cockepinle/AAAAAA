$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$backupFile = "$PSScriptRoot\backup_shopurpro_$timestamp.dump"
pg_dump -U postgres -d shopurpro -F c -f $backupFile
Write-Host "Backup created at $backupFile"
