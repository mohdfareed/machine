"""PC machine manifest for Windows and WSL."""

from app.env import PLATFORM
from app.models import Machine, Package, PkgManager, Platform
from config import system
from config.development import agents, python, vscode
from config.terminal import emulators, git, shell, ssh
from config.terminal.ssh import client

sib_script_install_path = '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\steam-input-bridge"'
sib_script_url = (
    "https://raw.githubusercontent.com/mohdfareed/steam-input-bridge/main/Scripts/Bootstrap-App.ps1"
)

manifest = Machine(
    pkg_managers=(
        [PkgManager.APT, PkgManager.BREW]
        if PLATFORM == Platform.WSL
        else [PkgManager.WINGET, PkgManager.SCOOP]
    ),
    modules=(
        [
            git,
            shell,
            client,
            python,
            agents,
        ]
        if PLATFORM == Platform.WSL
        else [
            system,
            git,
            shell,
            ssh,
            emulators,
            python,
            agents,
            vscode,
        ]
    ),
    packages=[
        # Dev tools
        Package(name="tailscale", winget="tailscale.tailscale"),
        Package(name="dotnet", winget="Microsoft.DotNet.SDK.10"),
        Package(name="sys-internals", winget="Microsoft.Sysinternals.Suite"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        Package(name="go", brew="go", winget="golang.Go"),
        # File Processing
        Package(brew="rsync"),  # file sync
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        Package(brew="pandoc", winget="JohnMacFarlane.Pandoc"),  # documents
        Package(brew="imagemagick", winget="ImageMagick.Q16-HDRI"),  # images
        Package(brew="sox", winget="ChrisBagwell.SoX"),  # audio
        Package(brew="ffmpeg", winget="Gyan.FFmpeg"),  # video
        Package(brew="yt-dlp", winget="yt-dlp.yt-dlp"),  # video downloader
        Package(brew="tesseract", winget="tesseract-ocr.tesseract"),  # ocr
        # Utilities
        Package(name="Raycast", winget="9PFXXSHC64H3"),
        Package(name="CPU-Z", winget="CPUID.CPU-Z"),
        Package(name="Craft Docs", winget="LukiLabs.Craft"),
        Package(name="UniGetUI", winget="Devolutions.UniGetUI"),
        Package(name="iCloud", winget="9PKTQ5699M62"),
        Package(name="Spotify", winget="Spotify.Spotify"),
        Package(name="Plex", winget="Plex.Plex"),
        # Gaming
        Package(name="Discord", winget="Discord.Discord"),
        Package(name="Steam", winget="valve.Steam"),
        Package(name="Riot Games", winget="RiotGames.Valorant.NA"),
        Package(name="Battle.net", winget="Blizzard.BattleNet"),
        Package(name="Epic Games", winget="EpicGames.EpicGamesLauncher"),
        # Gaming Utilities
        Package(name="8BitDo Ultimate Software", winget="8BitDo.UltimateSoftwareV2"),
        Package(name="Razer Synapse", winget="RazerInc.RazerInstaller.Synapse4"),
        Package(name="Steam Rom Manager", winget="SteamGridDB.RomManager"),
        Package(
            name="Steam Input Bridge",
            platforms=[Platform.WIN],
            cmd=f"{sib_script_install_path}; irm {sib_script_url} | iex",
        ),
    ],
)
