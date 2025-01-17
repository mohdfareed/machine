"""Testing machine."""

__all__ = ["Test"]


from app import utils
from app.models import DebugCommandProtocol
from app.pkg_manager import PkgManagerPlugin


class Test(PkgManagerPlugin, DebugCommandProtocol):
    """Testbench package manager."""

    @utils.hidden
    def _setup(self) -> None: ...

    @utils.hidden
    def _update(self) -> None: ...

    @utils.hidden
    def _cleanup(self) -> None: ...

    @utils.hidden
    def _install(self, package: str) -> None: ...
