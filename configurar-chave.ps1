$ErrorActionPreference = 'Stop'
$nomusBaseUrl = (Read-Host 'URL da API HTTPS, terminada em /rest').Trim().TrimEnd('/')
$nomusUri = $null
if (-not [Uri]::TryCreate($nomusBaseUrl, [UriKind]::Absolute, [ref]$nomusUri)) { throw 'URL invalida.' }
if ($nomusUri.Scheme -ne 'https' -or $nomusUri.UserInfo -or $nomusUri.Query -or $nomusUri.Fragment -or -not $nomusUri.AbsolutePath.EndsWith('/rest')) { throw 'Use uma URL HTTPS terminada em /rest, sem credenciais ou parametros.' }
$secretDirectory = Join-Path $PSScriptRoot '.secrets'
$secretPath = Join-Path $secretDirectory 'nomus-key.dpapi'
Write-Host 'No Nomus: Configuracao Geral > Chave de acesso para integracao com o ERP via REST.'
Write-Host 'Cole a chave exatamente como fornecida pelo Nomus. Ela nao sera exibida.'
$nomusSecureKey = Read-Host 'Chave de integracao' -AsSecureString
if ($nomusSecureKey.Length -eq 0) { throw 'A chave nao pode estar vazia.' }
New-Item -ItemType Directory -Path $secretDirectory -Force | Out-Null
$nomusSecureKey | ConvertFrom-SecureString | Set-Content -LiteralPath $secretPath -Encoding ASCII
@{ base_url = $nomusBaseUrl } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'nomus.local.json') -Encoding UTF8
Write-Host 'Chave salva criptografada pelo Windows. Avise ao Codex que a chave foi configurada.'
