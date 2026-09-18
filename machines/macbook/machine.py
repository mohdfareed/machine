"""Personal laptop (macOS) machine manifest."""

from app.models import Machine, Package, PkgManager
from config import system
from config.development import agents, python, vscode, zed
from config.terminal import emulators, git, shell
from config.terminal.ssh import client

manifest = Machine(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        system,
        git,
        shell,
        client,
        emulators,
        python,
        agents,
        vscode,
        zed,
    ],
    files=[],
    packages=[
        # ─────────────────────────────────────────────────────────────────────
        # System
        # ─────────────────────────────────────────────────────────────────────
        # Dev tools
        Package(name="xcode", mas=497799835),
        Package(cask="docker-desktop"),
        Package(cask="dotnet-sdk"),
        Package(brew="go"),
        # Utilities
        Package(brew="gnu-time"),  # benchmarking/profiling
        # File Processing
        Package(brew="rsync"),  # file sync
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        Package(brew="pandoc", winget="JohnMacFarlane.Pandoc"),  # documents
        Package(brew="imagemagick", winget="ImageMagick.Q16-HDRI"),  # images
        Package(brew="sox", winget="ChrisBagwell.SoX"),  # audio
        Package(brew="ffmpeg", winget="Gyan.FFmpeg"),  # video
        Package(brew="yt-dlp", winget="yt-dlp.yt-dlp"),  # video downloader
        Package(brew="tesseract", winget="tesseract-ocr.tesseract"),  # ocr
        # ─────────────────────────────────────────────────────────────────────
        # Apps
        # ─────────────────────────────────────────────────────────────────────
        # System
        Package(cask="tailscale"),  # vpn
        # Productivity
        Package(cask="craft"),  # notes
        Package(name="keynote", mas=409183694),
        Package(name="numbers", mas=409203825),
        Package(name="pages", mas=409201541),
        # Design
        Package(cask="figma"),
        Package(cask="sf-symbols"),
        Package(cask="font-computer-modern"),
        # Tools
        Package(cask="raycast"),  # spotlight
        Package(cask="macpacker"),  # archives
        Package(cask="tablepro"),  # databases
        Package(cask="iina"),  # local media player
        Package(name="infuse", mas=1136220934),  # media player
        # Utilities
        Package(cask="mos"),  # mouse settings
        Package(cask="swish"),  # trackpad gestures
        Package(cask="monitorcontrol"),  # external monitors
        Package(cask="adguard"),
        Package(name="noir", mas=1592917505),
        # QuickLook
        Package(name="unfold", cask="flewgg/tap/unfold"),  # plain files
        Package(name="folder-preview", mas=6698876601),  # folders
        # Package(cask="betterzip"), # archives
    ],
)
