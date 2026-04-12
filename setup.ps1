# setup.ps1 - Installer for Bit Unix Trading MCP
# Run this script to configure your environment and generate the launcher.

$ErrorActionPreference = "Stop"

Write-Host "--- Bit Unix Trading MCP Setup ---" -ForegroundColor Cyan

# 1. Check for Dependencies
Write-Host "`n[1/5] Checking dependencies..." -ForegroundColor Yellow
$node = Get-Command node -ErrorAction SilentlyContinue
$python = Get-Command python -ErrorAction SilentlyContinue
if (!$node) { Write-Error "Node.js is not installed or not in PATH." }
if (!$python) { Write-Host "Warning: 'python' command not found. Searching for 'py' or 'python3'..." -ForegroundColor Gray }

# 2. Search for TradingView
Write-Host "`n[2/5] Searching for TradingView Desktop..." -ForegroundColor Yellow

$tvSource = $null
$tvExe = $null
$tvType = "Unknown"

# A. Try Microsoft Store Version (Get-AppxPackage)
try {
    $package = Get-AppxPackage -Name "TradingView.Desktop" -ErrorAction SilentlyContinue
    if ($package) {
        $tvSource = $package.InstallLocation
        $tvExe = Join-Path $tvSource "TradingView.exe"
        if (Test-Path $tvExe) {
            $tvType = "Microsoft Store"
            Write-Host "Found TradingView (Microsoft Store) at: $tvSource" -ForegroundColor Green
        } else {
            $tvSource = $null # Reset if exe not found
        }
    }
} catch {}

# B. Try Standard Paths
if (!$tvSource) {
    $tvPaths = @(
        "$env:LocalAppData\Programs\TradingView",
        "$env:ProgramFiles\TradingView",
        "$env:ProgramFiles(x86)\TradingView",
        "$env:LocalAppData\Packages\TradingView.Desktop_n534cwy3pjxzj\LocalCache\Roaming\TradingView" # User specific data path
    )
    
    foreach ($p in $tvPaths) {
        if (Test-Path $p) {
            $tvSource = $p
            $exeSearch = Get-ChildItem -Path $p -Filter "TradingView.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($exeSearch) {
                $tvExe = $exeSearch.FullName
                $tvType = "Standard Installation"
                Write-Host "Found TradingView (Standard) at: $tvSource" -ForegroundColor Green
                break
            }
        }
    }
}

# C. Try PWA / Browser App Shortcuts
if (!$tvSource) {
    $shortcutPaths = @(
        "$env:AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\TradingView*",
        "$env:AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Edge Apps\TradingView*",
        "$env:LocalAppData\Microsoft\Windows\Start Menu\Programs\Firefox PWAs\TradingView*"
    )
    
    foreach ($sp in $shortcutPaths) {
        $match = Get-Item $sp -ErrorAction SilentlyContinue
        if ($match) {
            $tvSource = $match.FullName
            $tvExe = $match.FullName # For PWAs, the "Exe" is the shortcut itself or we launch via browser
            $tvType = "PWA / Browser App"
            Write-Host "Found TradingView ($tvType) shortcut at: $tvSource" -ForegroundColor Green
            break
        }
    }
}

if (!$tvSource) {
    Write-Host "TradingView not found automatically." -ForegroundColor Magenta
    $tvSource = Read-Host "Please enter the path to TradingView installation folder or EXE"
    if (Test-Path $tvSource) {
        if ((Get-Item $tvSource).PSIsContainer) {
            $tvExe = Join-Path $tvSource "TradingView.exe"
        } else {
            $tvExe = $tvSource
            $tvSource = Split-Path $tvExe -Parent
        }
    }
}

$usePortable = "n"
if ($tvType -eq "Microsoft Store") {
    Write-Host "Notice: Microsoft Store version detected. Portable mode (copying files) is not recommended due to folder protection." -ForegroundColor Gray
    $usePortable = "n"
} else {
    $usePortableInput = Read-Host "Do you want to use a Portable version of TradingView (TVPortable)? (y/n) [y]"
    if ($usePortableInput -eq "" -or $usePortableInput -eq "y") {
        $usePortable = "y"
    }
}

if ($usePortable -eq "y") {
    $tvPortableDir = Join-Path $HOME "TVPortable"
    Write-Host "TradingView will be copied to: $tvPortableDir" -ForegroundColor Gray
} else {
    $tvPortableDir = $tvSource
}

# 3. Browser Selection
Write-Host "`n[3/5] Configuring Browser..." -ForegroundColor Yellow
Write-Host "1) Mozilla Firefox"
Write-Host "2) Google Chrome"
$browserChoice = Read-Host "Which browser do you want to use? (1/2) [1]"

if ($browserChoice -eq "2") {
    $browserExe = "C:\Program Files\Google\Chrome\Application\chrome.exe"
} else {
    $browserExe = "C:\Program Files\Mozilla Firefox\firefox.exe"
}
Write-Host "Using browser: $browserExe" -ForegroundColor Gray

# 4. API Keys
Write-Host "`n[4/5] Configuring BitUnix API Keys..." -ForegroundColor Yellow
$apiKey = Read-Host "Enter your BitUnix API Key"
$secretKey = Read-Host "Enter your BitUnix Secret Key"

$envContent = "BITUNIX_API_KEY=$apiKey`nBITUNIX_SECRET_KEY=$secretKey"
Set-Content -Path "Bitunix-trading-mcp\.env" -Value $envContent
Write-Host "API keys saved to Bitunix-trading-mcp\.env" -ForegroundColor Green

# 5. Generate Launcher
Write-Host "`n[5/5] Generating launcher script..." -ForegroundColor Yellow
$templatePath = "start-trading.template.bat"
if (Test-Path $templatePath) {
    $content = Get-Content $templatePath -Raw
    $content = $content.Replace("[[TRADINGVIEW_EXE]]", $tvExe)
    $content = $content.Replace("[[TV_PORTABLE_DIR]]", $tvPortableDir)
    $content = $content.Replace("[[TV_SOURCE_DIR]]", $tvSource)
    $content = $content.Replace("[[BROWSER_EXE]]", $browserExe)
    
    Set-Content -Path "start-trading.bat" -Value $content
    Write-Host "Launcher generated: start-trading.bat" -ForegroundColor Green
} else {
    Write-Error "Template file not found: $templatePath"
}

Write-Host "`nSetup Successful!" -ForegroundColor Green
Write-Host "You can now start the environment by running 'start-trading.bat'."
pause
