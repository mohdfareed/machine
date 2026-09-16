"""Homelab (macOS) machine manifest."""

from app.models import FileMapping, Machine, Package, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "system",
        "homelab",
        "terminal.git",
        "terminal.shell",
        "terminal.ssh",
        "terminal.emulators",
        "development.python",
        "development.agents",
        "development.vscode",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
    ],
    packages=[
        Package(brew="go"),
        Package(brew="rsync"),  # file sync
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        Package(brew="pandoc", winget="JohnMacFarlane.Pandoc"),  # documents
        Package(brew="imagemagick", winget="ImageMagick.Q16-HDRI"),  # images
        Package(brew="sox", winget="ChrisBagwell.SoX"),  # audio
        Package(brew="ffmpeg", winget="Gyan.FFmpeg"),  # video
        Package(brew="yt-dlp", winget="yt-dlp.yt-dlp"),  # video downloader
        Package(brew="tesseract", winget="tesseract-ocr.tesseract"),  # ocr
    ],
)
