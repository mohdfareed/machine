"""SSH server setup module."""

from app.models import Module

module = Module(depends=["ssh"])
