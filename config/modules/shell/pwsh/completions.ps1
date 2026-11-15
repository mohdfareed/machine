#!/usr/bin/env pwsh

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment
# ═════════════════════════════════════════════════════════════════════════════

# Configure completions.
$env:CARAPACE_BRIDGES = 'zsh,fish,bash,inshellisense'
$env:CARAPACE_TOOLTIP = '1'

# Configure fuzzy search.
$env:FZF_ALT_C_COMMAND = 'fd --type directory --color=never'
$env:FZF_CTRL_T_COMMAND = 'fd --color=never'

# Configure file and directory previews.
$env:FZF_DEFAULT_OPTS += ' --ansi --preview-window=right:50%'
$env:FZF_ALT_C_OPTS = '--preview "ls --color=always -TL=2 -- {}"'
$env:FZF_CTRL_T_OPTS = @(
    '--with-shell "pwsh -NonInteractive -Command"'
    '--preview "$p = Get-Content -LiteralPath {f} -TotalCount 1;'
    'if (Test-Path -LiteralPath $p -PathType Container) {'
    'ls --color=always -TL=2 -- $p'
    '} else { cat --color=always -- $p }"'
) -join ' '

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Completions
# ═════════════════════════════════════════════════════════════════════════════

# Enable command history (50ms).
Import-Module PSReadLine
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineKeyHandler -Key Alt+k -Function ShowKeyBindings

# Enable fuzzy search (150ms).
Import-Module PSFzf
Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t'
Set-PsFzfOption -PSReadlineChordSetLocation 'Alt+c'
Set-PsFzfOption -PSReadlineChordReverseHistory 'Ctrl+r'
Set-PsFzfOption -PSReadlineChordReverseHistoryArgs 'Alt+a'

# Load carapace completions (150ms).
carapace _carapace powershell | Out-String | Invoke-Expression

# Load user completions.
Get-ChildItem "$ConfigHome/Completions/*.ps1" -ErrorAction Ignore |
ForEach-Object { . $_.FullName }

# Enable tab completions (50ms).
Import-Module PSCompletions

# ═════════════════════════════════════════════════════════════════════════════
# MARK: TabExpansion2 wrapper
# ═════════════════════════════════════════════════════════════════════════════

# Preserve the original once, including across profile reloads.
if (-not (Test-Path Function:OriginalTabExpansion2)) {
    Copy-Item Function:TabExpansion2 Function:global:OriginalTabExpansion2
}

& {
    $original = Get-Command OriginalTabExpansion2
    $metadata = [System.Management.Automation.CommandMetadata]::new($original)
    $proxy = [System.Management.Automation.ProxyCommand]
    $binding = $proxy::GetCmdletBindingAttribute($metadata)
    $parameters = $proxy::GetParamBlock($metadata)

    $body = @'
    $result = & $original @PSBoundParameters
    $parameterCommand = $null

    # Find the command that owns the parameter being completed.
    try {
        if ($result.CompletionMatches.ResultType -contains 'ParameterName') {
            $syntax = if ($PSBoundParameters.ContainsKey('ast')) { $ast } else {
                [System.Management.Automation.Language.Parser]::ParseInput(
                    $inputScript, [ref]$null, [ref]$null
                )
            }

            $start = $result.ReplacementIndex
            $end = $start + $result.ReplacementLength
            $node = $syntax.FindAll({
                param($n)
                $n -is [System.Management.Automation.Language.CommandAst] -and
                    $n.Extent.StartOffset -le $start -and
                    $n.Extent.EndOffset -ge $end
            }, $true) |
                Sort-Object { $_.Extent.EndOffset - $_.Extent.StartOffset } |
                Select-Object -First 1

            if ($node -and ($name = $node.GetCommandName())) {
                $parameterCommand = Get-Command $name -ErrorAction Stop
                if ($parameterCommand.CommandType -eq 'Alias') {
                    $parameterCommand = $parameterCommand.ResolvedCommand
                }
            }
        }
    } catch { }

    for ($i = 0; $i -lt $result.CompletionMatches.Count; $i++) {
        $item = $result.CompletionMatches[$i]
        try {
            if ($item.ResultType -eq 'Command') {
                $command = Get-Command $item.ListItemText -ErrorAction Stop
                if ($command.CommandType -eq 'Alias') {
                    $command = $command.ResolvedCommand
                }
                if ($command.CommandType -notin 'Cmdlet', 'Function', 'Filter') {
                    continue
                }
            } elseif ($item.ResultType -eq 'ParameterName') {
                $command = $parameterCommand
                if (-not $command) { continue }
            } else {
                continue
            }

            $name = $command.Name
            if ($command.ModuleName) {
                $name = "$($command.ModuleName)\$name"
            }

            if ($item.ResultType -eq 'ParameterName') {
                $parameter = $item.CompletionText.TrimStart('-').TrimEnd(':')
                $metadata = $command.Parameters.Values | Where-Object {
                    $_.Name -eq $parameter -or $_.Aliases -contains $parameter
                } | Select-Object -First 1

                if (-not $metadata) { continue }
                $help = Get-Help $name -Parameter $metadata.Name -ErrorAction Stop
            } else {
                $help = Get-Help $name -ErrorAction Stop
            }

            $tip = ($help | Out-String -Width 80).TrimEnd()
            $result.CompletionMatches[$i] =
                [System.Management.Automation.CompletionResult]::new(
                    $item.CompletionText, $item.ListItemText,
                    $item.ResultType, $tip
                )
        } catch {
            # Keep the original completion when help is unavailable.
        }
    }

    $result
'@

    $wrapper = [scriptblock]::Create(
        "$binding`nparam($parameters)`n$body"
    ).GetNewClosure()

    Set-Item Function:global:TabExpansion2 $wrapper
}
