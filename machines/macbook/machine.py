"""Personal laptop (macOS) machine manifest."""

from app.models import Machine, Package, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "system",
        "terminal.git",
        "terminal.shell",
        "terminal.ssh.client",
        "terminal.emulators",
        "development.python",
        "development.agents",
        "development.vscode",
        "development.zed",
    ],
    files=[],
    packages=[
        # Dev languages
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
        # Apps
        Package(cask="raycast"),
        Package(cask="iina"),
        Package(cask="mos"),
        Package(cask="monitorcontrol"),
        Package(cask="swish"),
        Package(cask="tailscale"),
        Package(cask="craft"),
        Package(cask="figma"),
        Package(cask="sf-symbols"),
        Package(cask="betterzip"),
        Package(cask="tablepro"),
        # Fonts
        Package(cask="font-computer-modern"),
        # Mac App Store
        Package(name="Xcode", mas=497799835),
        Package(name="Keynote", mas=409183694),
        Package(name="Numbers", mas=409203825),
        Package(name="Pages", mas=409201541),
        Package(name="Infuse", mas=1136220934),
        Package(name="Noir", mas=1592917505),
        Package(name="AdGuard", mas=1440147259),
        Package(name="Peek", mas=1554235898),
    ],
)
