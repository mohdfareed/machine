"""Homelab (macOS) machine manifest."""

from pathlib import Path

from app.config.models import Machine, Package

from config import onepass, shell, ssh, system, terminal

manifest = Machine(
    env={
        "MC_HOMELAB_TIMEZONE": "America/New_York",
        "MC_HOMELAB_STORAGE_DIR": Path.home() / ".homelab",
        "MC_HOMELAB_MEDIA_DIR": Path("/Volumes/External HD/Media"),
    },
    modules=[system, onepass, shell, ssh, terminal],
    packages=[
        Package(brew="gh"),
        Package(name="tailscale", cask="tailscale"),
        Package(name="docker", cask="docker-desktop"),
        Package(brew="go"),
        # Agents
        Package(name="remindctl", brew="steipete/tap/remindctl"),  # reminders
        # Utilities
        Package(brew="wakeonlan"),  # wake devices
        Package(brew="rsync"),  # file sync
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
