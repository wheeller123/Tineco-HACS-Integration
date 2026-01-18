#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy Tineco HACS integration to Home Assistant
.DESCRIPTION
    Copies the custom_components folder to Home Assistant and restarts the service
.NOTES
    Requires: SSH access to Home Assistant
    Username: jack
#>

# Configuration
$SourcePath = "C:\Users\jwhel\Documents\Projects\Tineco\HACS\custom_components"
$DestinationPath = "\\192.168.0.101\config\custom_components"
$HomeAssistantHost = "192.168.0.101"
$SSHUsername = "jack"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tineco HACS Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify source folder exists
Write-Host "[1/4] Verifying source folder..." -ForegroundColor Yellow
if (-not (Test-Path $SourcePath)) {
    Write-Host "ERROR: Source folder not found: $SourcePath" -ForegroundColor Red
    exit 1
}
Write-Host "      Source folder verified: $SourcePath" -ForegroundColor Green
Write-Host ""

# Step 2: Get password once for both operations
Write-Host "[2/4] Authentication..." -ForegroundColor Yellow
$SecurePassword = Read-Host "      Enter password for Home Assistant access" -AsSecureString
$Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
)
Write-Host ""

# Step 3: Copy files using robocopy
Write-Host "[3/4] Copying files to Home Assistant..." -ForegroundColor Yellow
Write-Host "      Source: $SourcePath" -ForegroundColor Gray
Write-Host "      Destination: $DestinationPath" -ForegroundColor Gray
Write-Host ""

# Map network drive with credentials
$netUsePath = "\\192.168.0.101\config"
$netUseOutput = net use $netUsePath /user:$SSHUsername $Password 2>&1
if ($LASTEXITCODE -ne 0 -and $netUseOutput -notmatch "already") {
    Write-Host "      Warning: Could not authenticate to network share" -ForegroundColor Yellow
}

# Robocopy parameters:
# /MIR = Mirror (copy all, delete extras in destination)
# /R:3 = Retry 3 times on failed copies
# /W:5 = Wait 5 seconds between retries
# /NP = No progress (cleaner output)
# /NFL = No file list
# /NDL = No directory list
$robocopyArgs = @(
    $SourcePath,
    $DestinationPath,
    "/MIR",
    "/R:3",
    "/W:5",
    "/NP"
)

$robocopyResult = & robocopy @robocopyArgs

# Robocopy exit codes:
# 0 = No files copied
# 1 = Files copied successfully
# 2 = Extra files/directories detected
# 3 = Files copied + extra files/dirs
# 4+ = Error
$exitCode = $LASTEXITCODE
if ($exitCode -ge 8) {
    Write-Host "ERROR: Robocopy failed with exit code $exitCode" -ForegroundColor Red
    exit 1
} elseif ($exitCode -eq 0) {
    Write-Host "      No changes detected - files already up to date" -ForegroundColor Yellow
} else {
    Write-Host "      Files copied successfully!" -ForegroundColor Green
}
Write-Host ""

# Step 4: Reboot Home Assistant via SSH (using same password)
Write-Host "[4/4] Rebooting Home Assistant..." -ForegroundColor Yellow

try {
    Write-Host "      Connecting to $HomeAssistantHost..." -ForegroundColor Gray
    
    # Use native ssh command with password via sshpass-like method
    $rebootCommand = "reboot"
    
    # Create a temporary script to pass password to ssh
    $tempScript = @"
`$Password = '$Password'
`$Password | & ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${SSHUsername}@${HomeAssistantHost} '$rebootCommand' 2>&1
"@
    
    $sshOutput = powershell -Command $tempScript
    
    if ($sshOutput) {
        Write-Host "      Output: $sshOutput" -ForegroundColor Gray
    }
    Write-Host "      Home Assistant reboot command sent!" -ForegroundColor Green
    Write-Host "      (Reboot may take 30-60 seconds to complete)" -ForegroundColor Gray
} catch {
    Write-Host "      ERROR: Failed to execute SSH command: $_" -ForegroundColor Red
    Write-Host "      Please reboot Home Assistant manually via: Settings > System > Reboot" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Wait 1-2 minutes for Home Assistant to restart" -ForegroundColor Gray
Write-Host "  2. Go to Settings > Devices & Services" -ForegroundColor Gray
Write-Host "  3. Your Tineco integration should be updated" -ForegroundColor Gray
Write-Host "  4. Check logs if there are any issues" -ForegroundColor Gray
Write-Host ""

# Clean up password from memory
$Password = $null
$SecurePassword = $null
[System.GC]::Collect()
