"""Personal laptop (macOS) machine manifest."""

from pathlib import Path

from app.config.models import Machine, Package

from config import dev, onepass, shell, system, terminal

_dev = Path.home() / "Developer"

manifest = Machine(
    env={
        "DEV": _dev,
        "DEV_BIN": _dev / "bin",
        "ICLOUD": Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
        "GODOT": Path("/Applications/Godot_mono.app/Contents/MacOS/Godot"),
        "MC_HOSTNAME": "mohd-macbook",
    },
    modules=[
        system,
        shell,
        onepass,
        terminal,
        dev,
    ],
    files=[],
    packages=[
        # Development
        Package(brew="gh"),
        Package(name="xcode", mas=497799835),
        Package(cask="docker-desktop"),
        Package(brew="gnu-time"),  # benchmarking/profiling
        # Files
        Package(brew="rsync"),  # file sync
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        Package(cask="macpacker"),  # archives
        Package(cask="tablepro"),  # databases
        # Processing
        Package(brew="pandoc", winget="JohnMacFarlane.Pandoc"),  # documents
        Package(brew="imagemagick", winget="ImageMagick.Q16-HDRI"),  # images
        Package(brew="sox", winget="ChrisBagwell.SoX"),  # audio
        Package(brew="ffmpeg", winget="Gyan.FFmpeg"),  # video
        Package(brew="yt-dlp", winget="yt-dlp.yt-dlp"),  # video downloader
        Package(brew="tesseract", winget="tesseract-ocr.tesseract"),  # ocr
        # Productivity
        Package(cask="craft"),
        Package(name="keynote", mas=409183694),
        Package(name="numbers", mas=409203825),
        Package(name="pages", mas=409201541),
        # Design
        Package(cask="figma"),
        Package(cask="sf-symbols"),
        Package(cask="font-computer-modern"),
        # System
        Package(cask="tailscale"),  # vpn
        Package(cask="windows-app"),  # win remote desktop
        Package(name="unfold", mas=6760872758),  # quickLook plugin
        Package(cask="swish"),  # trackpad gestures
        Package(cask="vorssaint"),  # utilities
        # Browser
        Package(name="noir", mas=1592917505),  # web dark mode
        Package(cask="adguard"),  # ad blocker
        # Media
        Package(cask="iina"),  # local media player
        Package(name="infuse", mas=1136220934),  # media player
    ],
)
