$Env:MACHINE = "{MACHINE}"
$Env:MACHINE_ID = "{MACHINE_ID}"

. "$Env:MACHINE/config/base/zshenv.ps1"
. "$Env:MACHINE/config/$Env:MACHINE_ID/zshenv.ps1"
