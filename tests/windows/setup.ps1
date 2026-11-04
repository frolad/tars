# Installs what the TARS checks need in the Windows VM of compose.yml; safe to run again. From the host:
#   ssh -p 2222 Docker@127.0.0.1 powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\tests\windows\setup.ps1
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$wingetArgs = "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"
function Update-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}

# Git for Windows: Claude Code's Bash tool
if (-not (Test-Path "C:\Program Files\Git\bin\bash.exe")) { winget install --id Git.Git @wingetArgs }

# Python through python.org's install manager; until it runs, python3 is only the Microsoft Store's shortcut
if (-not (Get-Command pymanager -ErrorAction SilentlyContinue)) { winget install --id Python.PythonInstallManager @wingetArgs }
Update-Path
py install --yes default

if (-not (Test-Path "$env:USERPROFILE\.local\bin\claude.exe")) { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression }
# Claude Code's installer leaves its folder off the user's PATH, so a new terminal would not find `claude`
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$env:USERPROFILE\.local\bin*") {
  [Environment]::SetEnvironmentVariable("Path", "$env:USERPROFILE\.local\bin;$userPath", "User")
}
if (-not (Test-Path "$env:LOCALAPPDATA\Programs\OpenAI\Codex\bin\codex.exe")) {
  Invoke-RestMethod https://chatgpt.com/codex/install.ps1 | Invoke-Expression
}

# The desktop app: Windows refuses an MSIX install over SSH (access denied), so a scheduled task runs it in the
# logged-in desktop session
if (-not (Get-AppxPackage Claude)) {
  $msix = "$env:TEMP\Claude.msix"
  Invoke-WebRequest "https://claude.ai/api/desktop/win32/x64/msix/latest/redirect" -OutFile $msix `
    -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command Add-AppxPackage -Path $msix"
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
  Register-ScheduledTask -TaskName tars-desktop -Action $action -Principal $principal -Force | Out-Null
  Start-ScheduledTask -TaskName tars-desktop
  while ((Get-ScheduledTask -TaskName tars-desktop).State -eq "Running") { Start-Sleep 5 }
  Unregister-ScheduledTask -TaskName tars-desktop -Confirm:$false
}

Update-Path

# TARS from the checkout. Claude Code refuses a marketplace on a network share (\\host.lan\Data, or a drive mapped
# to it), so the checkout is copied to C:\tars first; run this script again to take the host's latest edits.
robocopy \\host.lan\Data C:\tars /MIR /XD .git node_modules __pycache__ results /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
$claude = "$env:USERPROFILE\.local\bin\claude.exe"
if (-not (& $claude plugin list | Select-String "tars@tars")) {
  & $claude plugin marketplace add C:\tars
  & $claude plugin install tars@tars
  & $claude plugin install tars-mod@tars
}
codex plugin marketplace add C:\tars
codex plugin add tars@tars

"python3: " + (python3 --version)
"claude: " + (& "$env:USERPROFILE\.local\bin\claude.exe" --version)
"codex: " + (codex --version)
"desktop app: " + (Get-AppxPackage Claude).Version
