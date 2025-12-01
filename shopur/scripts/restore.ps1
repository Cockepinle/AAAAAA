param(
    [string]$FilePath = "$PSScriptRoot\backup_shopurpro_latest.dump"
)

$env:PGPASSWORD = "1"
$database = "shopurpro"
$user = "postgres"
$dbhost = "localhost"

psql -U $user -h $dbhost -c "DROP DATABASE IF EXISTS $database;"
psql -U $user -h $dbhost -c "CREATE DATABASE $database;"
pg_restore -U $user -h $dbhost -d $database $FilePath

Write-Host "Database restored from $FilePath"
