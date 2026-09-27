"""Homelab (macOS) machine manifest."""

from pathlib import Path

from app.config.models import Machine, Package

from config import onepass, shell, ssh, system, terminal

manifest = Machine(
    env={
        # Homelab
        "MC_HOMELAB_TIMEZONE": "America/New_York",
        "HOMEPAGE_TITLE": "Homelab Dashboard",
        "HOMEPAGE_FAVICON": "mdi-home-analytics",
        # Local state and shared media
        "MC_HOMELAB_STORAGE_DIR": Path.home() / ".homelab",
        "MC_HOMELAB_MEDIA_DIR": Path("/Volumes/Media"),
    },
    modules=[system, onepass, shell, ssh, terminal],
    packages=[
        Package(name="tailscale", cask="tailscale"),
        Package(name="docker", cask="docker-desktop"),
        Package(brew="rsync"),  # file sync
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
