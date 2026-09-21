"""Homelab (macOS) machine manifest."""

from app.models import Machine, Package, PkgManager
from config import homelab, system
from config.development import agents, python, vscode
from config.terminal import emulators, git, shell, ssh

manifest = Machine(
    pkg_managers=[PkgManager.MAS],
    modules=[
        system,
        homelab,
        git,
        shell,
        ssh,
        emulators,
        python,
        agents,
        vscode,
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
