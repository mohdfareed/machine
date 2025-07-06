# Inputs
$env:MACHINE = "{{ .machinePath }}"
$env:MACHINE_ID = "{{ .machine }}"
$env:MACHINE_PRIVATE = "{{ .privatePath }}"

# Convenience
$env:MACHINE_SHARED = "{{ .configPath }}"
$env:MACHINE_CONFIG = "{{ .machineConfigPath }}"
$env:MACHINE_SCRIPTS = "{{ .scriptsPath }}"

if (Test-Path -Path "$env:MACHINE_PRIVATE") {
    . "$env:MACHINE_PRIVATE/profile.ps1"
}

. "$env:MACHINE_SHARED/shell/profile.ps1"

if (Test-Path -Path "$env:MACHINE_CONFIG/profile.ps1") {
    . "$env:MACHINE_CONFIG/profile.ps1"
}
