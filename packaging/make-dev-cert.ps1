# Creates a LOCAL development code-signing certificate (free).
# Trusts it for the current Windows user only.
# This does NOT buy public SmartScreen reputation and will not
# silence Defender/SmartScreen on other people's PCs.

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$outDir = Join-Path $root "packaging"
$pfx = Join-Path $outDir "keygen-dev.pfx"
$passwordPlain = "keygen-dev-local"
$secure = ConvertTo-SecureString -String $passwordPlain -Force -AsPlainText

$existing = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -eq "CN=KEYGEN Local Dev" } |
    Select-Object -First 1

if (-not $existing) {
    $existing = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject "CN=KEYGEN Local Dev" `
        -KeyAlgorithm RSA `
        -KeyLength 2048 `
        -HashAlgorithm SHA256 `
        -CertStoreLocation Cert:\CurrentUser\My `
        -NotAfter (Get-Date).AddYears(3) `
        -KeyExportPolicy Exportable
    Write-Host "Created cert $($existing.Thumbprint)"
} else {
    Write-Host "Reusing cert $($existing.Thumbprint)"
}

# Local trust: same user, this machine only
$stores = @(
    "Cert:\CurrentUser\TrustedPublisher",
    "Cert:\CurrentUser\Root"
)
foreach ($storePath in $stores) {
    $store = Get-Item $storePath
    $open = New-Object System.Security.Cryptography.X509Certificates.X509Store $store.Name, $store.Location
    $open.Open("ReadWrite")
    if (-not $open.Certificates.Find("FindByThumbprint", $existing.Thumbprint, $false).Count) {
        $open.Add($existing)
        Write-Host "Installed cert into $storePath"
    }
    $open.Close()
}

Export-PfxCertificate -Cert $existing -FilePath $pfx -Password $secure | Out-Null
Write-Host "PFX: $pfx"
Write-Host "Password (local only): $passwordPlain"
Write-Output $pfx
