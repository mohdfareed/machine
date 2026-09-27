"""PC machine manifest for Windows and WSL."""

from pathlib import Path

from app.configuration.models import Machine, Package, Platform
from app.runtime.env import PLATFORM
from config import dev, onepass, shell, ssh, system, terminal

sib_script_install_path = '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\steam-input-bridge"'
sib_script_url = (
    "https://raw.githubusercontent.com/mohdfareed/steam-input-bridge/main/Scripts/Bootstrap-App.ps1"
)

manifest = Machine(
    env={
        "DEV": Path.home() / "Dev",
        "ICLOUD": Path.home() / "iCloudDrive",
        # Shared media storage
        "MC_HOMELAB_MEDIA_DIR": Path("D:/Media"),
    },
    modules=(
        [
            system,
            shell,
            dev,
        ]
        if PLATFORM == Platform.WSL
        else [
            system,
            onepass,
            shell,
            ssh,
            terminal,
            dev,
        ]
    ),
    packages=[
        # Networking
        Package(name="tailscale", winget="Tailscale.Tailscale"),
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
