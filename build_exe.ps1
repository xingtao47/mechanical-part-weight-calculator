$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDirectory

$pythonCommand = Get-Command python -ErrorAction Stop
$pythonPath = $pythonCommand.Source
$sourceFile = Join-Path $projectDirectory "weight_calculator.py"
$entryFile = Join-Path $projectDirectory "weight_calculator_gui.py"
$versionLine = Select-String -LiteralPath $sourceFile -Pattern '^VERSION = "([^"]+)"$'

if (-not $versionLine) {
    throw "无法从 weight_calculator.py 读取版本号。"
}

$version = $versionLine.Matches[0].Groups[1].Value
$programName = "机械零件重量计算器-V$version"

& $pythonPath -m PyInstaller --version | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "未找到 PyInstaller，请先运行：python -m pip install pyinstaller"
}

& $pythonPath -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $programName `
    $entryFile

if ($LASTEXITCODE -ne 0) {
    throw "EXE 打包失败。"
}

$exePath = Join-Path $projectDirectory "dist\$programName.exe"
Write-Host "打包完成：$exePath"
