# setup.ps1 - Installer for Bit Unix Trading MCP
# Run this script to configure your environment and generate the launcher.

$ErrorActionPreference = "Stop"

Write-Host "--- Bit Unix Trading MCP Setup ---" -ForegroundColor Cyan

# 1. Check for Dependencies
Write-Host "`n[1/5] Checking dependencies..." -ForegroundColor Yellow

function Install-SystemDependency {
    param([string]$Name, [string]$Id, [string]$Command)
    
    if (!(Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "$Name not found." -ForegroundColor Magenta
        $choice = Read-Host "Would you like to install $Name via winget? (y/n) [y]"
        if ($choice -eq "" -or $choice -eq "y") {
            winget install --id $Id --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$Name installation started successfully. You may need to restart the terminal after it finishes." -ForegroundColor Green
            } else {
                Write-Host "Failed to install $Name via winget. Please install it manually from the official website." -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Found $Name: $(Get-Command $Command | Select-Object -ExpandProperty Source)" -ForegroundColor Gray
    }
}

# Check System Dependencies
Install-SystemDependency -Name "Node.js" -Id "OpenJS.NodeJS" -Command "node"
Install-SystemDependency -Name "Python" -Id "Python.Python.3" -Command "python"

# Check Project Dependencies (Node.js)
$tvMcpDir = "tradingview-mcp-jackson"
if (Test-Path $tvMcpDir) {
    if (!(Test-Path "$tvMcpDir\node_modules")) {
        Write-Host "`nNode.js modules missing for TradingView MCP." -ForegroundColor Magenta
        $choice = Read-Host "Run 'npm install' now? (y/n) [y]"
        if ($choice -eq "" -or $choice -eq "y") {
            Push-Location $tvMcpDir
            npm install
            Pop-Location
        }
    }
}

# Check Project Dependencies (Python)
$bitunixDir = "Bitunix-trading-mcp"
if (Test-Path $bitunixDir) {
    $reqFile = "$bitunixDir\requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "`nChecking Python packages for BitUnix MCP..." -ForegroundColor Yellow
        $choice = Read-Host "Install/Update Python dependencies from requirements.txt? (y/n) [y]"
        if ($choice -eq "" -or $choice -eq "y") {
            python -m pip install -r $reqFile
        }
    }
}

# 2. Search for TradingView
Write-Host "`n[2/5] Searching for TradingView Desktop..." -ForegroundColor Yellow

$tvSource = $null
$tvExe = $null
$tvType = "Unknown"

# A. Try Standard Paths & Desktop (Highest Priority for Automation)
$tvPaths = @(
    "$env:USERPROFILE\TVPortable",
    "$env:USERPROFILE\Desktop",
    "$env:LocalAppData\Programs\TradingView",
    "$env:ProgramFiles\TradingView",
    "$env:ProgramFiles(x86)\TradingView"
)

foreach ($p in $tvPaths) {
    if (Test-Path $p) {
        # Check if the path itself is the EXE
        if ($p -like "*.exe") {
            $tvExe = $p
            $tvSource = Split-Path $p -Parent
            $tvType = "Standalone EXE"
            break
        }
        # Search for EXE inside
        $exeSearch = Get-ChildItem -Path $p -Filter "TradingView.exe" -Recurse -Depth 1 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($exeSearch) {
            $tvExe = $exeSearch.FullName
            $tvSource = $exeSearch.DirectoryName
            $tvType = "Standard Installation"
            break
        }
    }
}

if ($tvExe) {
    Write-Host "Found TradingView ($tvType) at: $tvExe" -ForegroundColor Green
}

# B. Try PWA / Browser App Shortcuts
if (!$tvExe) {
    $shortcutPaths = @(
        "$env:AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\TradingView*",
        "$env:AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Edge Apps\TradingView*",
        "$env:LocalAppData\Microsoft\Windows\Start Menu\Programs\Firefox PWAs\TradingView*"
    )
    
    foreach ($sp in $shortcutPaths) {
        $match = Get-Item $sp -ErrorAction SilentlyContinue
        if ($match) {
            $tvSource = $match.FullName
            $tvExe = $match.FullName 
            $tvType = "PWA / Browser App"
            Write-Host "Found TradingView ($tvType) shortcut at: $tvSource" -ForegroundColor Green
            break
        }
    }
}

# C. Try Microsoft Store Version (Fallback - WARNING: Often blocks CDP port)
if (!$tvExe) {
    try {
        $package = Get-AppxPackage -Name "TradingView.Desktop" -ErrorAction SilentlyContinue
        if ($package) {
            $tvSource = $package.InstallLocation
            $tvExe = Join-Path $tvSource "TradingView.exe"
            if (Test-Path $tvExe) {
                $tvType = "Microsoft Store"
                Write-Host "Found TradingView (Microsoft Store) at: $tvSource" -ForegroundColor Yellow
                Write-Host "WARNING: Microsoft Store apps often block remote debugging ports (Access Denied). Standalone version is recommended." -ForegroundColor Gray
            } else {
                $tvExe = $null
            }
        }
    } catch {}
}

if (!$tvExe) {
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
    Write-Host "Notice: Microsoft Store version detected. Portable mode is not possible and CDP port may be blocked." -ForegroundColor Gray
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
