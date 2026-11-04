@echo off
rem Runs once, at the end of the Windows install: an SSH server with PowerShell as its shell, so the checks can be
rem driven from the host. The log is C:\OEM\install.log.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0;" ^
  "Set-Service sshd -StartupType Automatic; Start-Service sshd;" ^
  "New-NetFirewallRule -Name sshd-tars -DisplayName 'OpenSSH for the TARS checks' -Protocol TCP -LocalPort 22 -Action Allow -Direction Inbound;" ^
  "New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell -Value 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -PropertyType String -Force" ^
  > C:\OEM\install.log 2>&1
