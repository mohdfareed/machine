Remove-Item Alias:cat, Alias:ls -ErrorAction Ignore
function cat { bat --paging=never @args }
function ls { eza --group-directories-first --git --icons @args }

# macOS
if ($IsMacOS) {
    function hide  {
        param(
            [ValidateSet('On', 'Off')]
            [string]$State = 'On',
            [string]$Path = '.',
            [switch]$Recursive
        )

        if ($Recursive) { $flags += '-R' }
        if ($State -eq 'On') { $flags += 'hidden' }
        if ($State -eq 'Off') { $flags += 'nohidden' }
        chflags -h @flags $Path
    }
}

# WSL
if ($env:WSL_DISTRO_NAME) {
    Set-Alias ssh ssh.exe
    Set-Alias ssh-add ssh-add.exe
}

# VSCode
if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}

# PowerShell

function pwsh::reload {
    Stop-Process -Id $PID -PassThru
    pwsh
}

function pwsh::time {
    $time = (Measure-Command { pwsh -Command "Exit" }).TotalMilliseconds
    Write-Host "Elapsed time: $time ms"
}

function pwsh::check {
    param([string]$Path)
    $code = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    $null = [scriptblock]::Create($code)
}
