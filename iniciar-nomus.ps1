param([switch]$Diagnostico)
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Ambiente Python ausente. Execute python -m venv .venv e instale requirements.txt conforme README.md.'
}
$configPath = Join-Path $PSScriptRoot 'nomus.local.json'
if (Test-Path -LiteralPath $configPath) {
    $nomusConfig = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $env:NOMUS_BASE_URL = $nomusConfig.base_url
}
$secretPath = Join-Path $PSScriptRoot '.secrets\nomus-key.dpapi'
if (Test-Path -LiteralPath $secretPath) {
    try { $nomusSecureKey = (Get-Content -LiteralPath $secretPath -Raw).Trim() | ConvertTo-SecureString }
    catch { throw 'Nao foi possivel ler a chave. Execute configurar-chave.ps1 com o mesmo usuario Windows que executa o Codex.' }
    $nomusPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($nomusSecureKey)
    try { $env:NOMUS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($nomusPointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($nomusPointer) }
}
try {
    $serverPath = Join-Path $PSScriptRoot 'nomus_server.py'
    if ($Diagnostico) { & $pythonPath $serverPath --diagnostico }
    else { & $pythonPath $serverPath }
    $nomusExitCode = $LASTEXITCODE
} finally { Remove-Item Env:\NOMUS_API_KEY -ErrorAction SilentlyContinue }
exit $nomusExitCode
