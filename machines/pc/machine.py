"""PC machine manifest for Windows and WSL."""

from pathlib import Path

from app.env import PLATFORM
from app.models import Machine, Package, PkgManager, Platform
from config import homelab
from config.development import agents, python, vscode, zed
from config.terminal import emulators, git, shell
from config.terminal.ssh import client as ssh_client

sib_script_install_path = '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\steam-input-bridge"'
sib_script_url = (
    "https://raw.githubusercontent.com/mohdfareed/steam-input-bridge/main/Scripts/Bootstrap-App.ps1"
)

manifest = Machine(
    env={
        "DEV": Path.home() / "Dev",
        "ICLOUD": Path.home() / "iCloudDrive",
        # Homelab
        "MC_HOMELAB_TIMEZONE": "America/New_York",
        "HOMEPAGE_TITLE": "PC Dashboard",
        "HOMEPAGE_FAVICON": "mdi-desktop-tower",
        # Mass Storage
        "MC_HOMELAB_STORAGE_DIR": Path("D:/Homelab"),
        "MC_HOMELAB_MEDIA_DIR": Path("D:/Media"),
    },
    pkg_managers=[] if PLATFORM == Platform.WSL else [PkgManager.SCOOP],
    modules=(
        [git, shell, ssh_client, python, agents]
        if PLATFORM == Platform.WSL
        else [
            homelab,
            emulators,
            python,
            agents,
            vscode,
            zed,
        ]
    ),
    packages=[
        # Development
        Package(name="dotnet", winget="Microsoft.DotNet.SDK.10"),
        Package(name="go", brew="go", winget="golang.Go"),
        # System Utilities
        Package(name="sys-internals", winget="Microsoft.Sysinternals.Suite"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        Package(name="cpu-z", winget="CPUID.CPU-Z"),
        Package(name="rufus", winget="Rufus.Rufus"),
        Package(name="UniGetUI", winget="Devolutions.UniGetUI"),
        # Files & Storage
        Package(brew="rsync"),  # file sync (wsl only)
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        Package(name="icloud", winget="9PKTQ5699M62"),
        # Utilities
        Package(name="raycast", winget="9PFXXSHC64H3"),
        Package(name="craft", winget="LukiLabs.Craft"),
        Package(name="spotify", winget="Spotify.Spotify"),
        Package(name="plex", winget="Plex.Plex"),
        Package(name="discord", winget="Discord.Discord"),
        # ─────────────────────────────────────────────────────────────────────
        # Gaming
        # ─────────────────────────────────────────────────────────────────────
        Package(name="steam", winget="valve.Steam"),
        # Clients
        Package(name="riot", winget="RiotGames.Valorant.NA"),
        Package(name="blizard", winget="Blizzard.BattleNet"),
        Package(name="epic", winget="EpicGames.EpicGamesLauncher"),
        # Peripherals
        Package(name="8bit-do", winget="8BitDo.UltimateSoftwareV2"),
        Package(name="razer", winget="RazerInc.RazerInstaller.Synapse4"),
        # Steam Utilities
        Package(name="steam-rom-manager", winget="SteamGridDB.RomManager"),
        Package(
            name="steam-input-bridge",
            platforms=[Platform.WIN],
            cmd=f"{sib_script_install_path}; irm {sib_script_url} | iex",
        ),
    ],
)
