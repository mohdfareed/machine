"""Homelab (macOS) machine manifest."""

from pathlib import Path

from app.models import Machine, Package, PkgManager
from config import homelab
from config.development import agents, python, vscode
from config.terminal import emulators

manifest = Machine(
    env={
        # Homelab
        "MC_HOMELAB_TIMEZONE": "America/New_York",
        "HOMEPAGE_TITLE": "Homelab Dashboard",
        "HOMEPAGE_FAVICON": "mdi-home-analytics",
        # Mass Storage
        "MC_HOMELAB_STORAGE_DIR": Path("/Volumes/External HD/Homelab"),
        "MC_HOMELAB_MEDIA_DIR": Path("/Volumes/External HD/Media"),
    },
    pkg_managers=[PkgManager.MAS],
    modules=[
        homelab,
        emulators,
        python,
        agents,
        vscode,
    ],
    packages=[
        Package(brew="go"),
        Package(brew="7zip", winget="7zip.7zip"),  # archiving
        # Content Processing
        Package(brew="pandoc", winget="JohnMacFarlane.Pandoc"),  # documents
        Package(brew="imagemagick", winget="ImageMagick.Q16-HDRI"),  # images
        Package(brew="sox", winget="ChrisBagwell.SoX"),  # audio
        Package(brew="ffmpeg", winget="Gyan.FFmpeg"),  # video
        Package(brew="yt-dlp", winget="yt-dlp.yt-dlp"),  # video downloader
        Package(brew="tesseract", winget="tesseract-ocr.tesseract"),  # ocr
    ],
)
