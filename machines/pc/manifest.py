"""PC machine manifest for Windows and WSL."""

from machine.core import PLATFORM, Platform
from machine.manifest import MachineManifest, Package, PkgManager

sib_script_install_path = '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\steam-input-bridge"'
sib_script_url = (
    "https://raw.githubusercontent.com/mohdfareed/steam-input-bridge/main/Scripts/Bootstrap-App.ps1"
)

manifest = MachineManifest(
    pkg_managers=(
        [PkgManager.APT, PkgManager.SNAP, PkgManager.BREW]
        if PLATFORM == Platform.WSL
        else [PkgManager.WINGET, PkgManager.SCOOP]
    ),
    modules=(
        ["git", "shell", "ssh", "codex"]
        if PLATFORM == Platform.WSL
        else ["git", "shell", "ssh", "ssh-server", "vscode", "win-term", "codex", "system"]
    ),
    packages=[
        # Dev tools
        Package(name="tailscale", winget="tailscale.tailscale"),
        Package(name="dotnet", winget="Microsoft.DotNet.SDK.10"),
        Package(name="sys-internals", winget="Microsoft.Sysinternals.Suite"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        Package(name="go", winget="golang.Go", apt="golang-go"),
        Package(name="nodejs", winget="OpenJS.NodeJS.LTS"),  # cspell checks
        # Utilities
        Package(name="7zip", scoop="7zip"),
        Package(name="CPU-Z", winget="CPUID.CPU-Z"),
        Package(name="Craft Docs", winget="LukiLabs.Craft"),
        Package(name="UniGetUI", winget="Devolutions.UniGetUI"),
        Package(name="iCloud", winget="9PKTQ5699M62"),
        Package(name="Apple Music", winget="9pfhdd62mxs1"),
        Package(name="Spotify", winget="Spotify.Spotify"),
        Package(name="Plex", winget="Plex.Plex"),
        # Gaming
        Package(name="Steam", winget="valve.Steam"),
        Package(name="Riot Games", winget="RiotGames.Valorant.NA"),
        Package(name="Battle.net", winget="Blizzard.BattleNet"),
        Package(name="Epic Games", winget="EpicGames.EpicGamesLauncher"),
        Package(name="Steam Rom Manager", winget="SteamGridDB.RomManager"),
        Package(name="WowUp", winget="WowUp.CF"),
        Package(name="Discord", winget="Discord.Discord"),
        # Gaming utilities
        Package(name="Xbox Accessories", winget="9nblggh30xj3"),
        Package(name="8BitDo Ultimate Software", winget="8BitDo.UltimateSoftwareV2"),
        Package(name="Razer Synapse", winget="RazerInc.RazerInstaller.Synapse4"),
        Package(
            name="Steam Input Bridge",
            platforms=[Platform.WINDOWS],
            script=f"{sib_script_install_path}; irm {sib_script_url} | iex",
        ),
    ],
)
