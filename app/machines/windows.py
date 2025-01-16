"""Windows machine."""

__all__ = ["Windows"]


from app import config, env, plugins, utils
from app.machine import MachinePlugin
from app.models import PluginProtocol
from app.plugins.pkg_managers import Scoop, Winget

VSCODE_TUNNELS_NAME = "pc"


class Windows(MachinePlugin[config.Windows, env.Windows]):
    """Windows machine configuration."""

    shell = utils.Shell()

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [
            plugins.Fonts,
            plugins.Git,
            plugins.PowerShell,
            plugins.NeoVim,
            plugins.Btop,
            plugins.VSCode,
            plugins.Tailscale,
            plugins.Python,
            plugins.Docker,
            plugins.SSH,
        ]

    def __init__(self) -> None:
        self.config = config.Windows()
        self.env = env.Windows(env_file=self.config.ps_profile)
        super().__init__()

    @classmethod
    def is_supported(cls) -> bool:
        return utils.WINDOWS

    def setup(self) -> None:
        super().setup()
        plugins.SSH(self.config, self.env).generate_key_pair("personal")
        plugins.SSH(self.config, self.env).setup_server()
        plugins.VSCode(self.config, self.env).setup_tunnels(VSCODE_TUNNELS_NAME)

        Winget().install("GoLang.Go Microsoft.DotNet.SDK")
        Scoop().add_bucket("extras")
        Scoop().install("extras/godot")


# def setup_wsl(wsl_module: _ModuleType, setup_args: str = "") -> None:
#     """Setup WSL on a new machine."""

#     _LOGGER.info("Setting up WSL...")
#     _utils.shell.execute("wsl --install", info=True)
#     current_shell = _utils.shell.EXECUTABLE
#     _utils.shell.EXECUTABLE = _utils.shell.SupportedExecutables.WSL
#     _utils.shell.execute(f"{_sys.executable} {wsl_module.__name__} {setup_args}")
#     _utils.shell.EXECUTABLE = current_shell
#     _LOGGER.info("WSL setup complete.")


# @core.machine_setup
# def wsl_setup() -> None:
#     """Setup WSL on a new Windows machine."""

#     # package managers
#     brew = package_managers.HomeBrew.safe_setup()
#     apt = package_managers.APT()
#     snap = package_managers.SnapStore(apt)

#     # setup core machine
#     scripts.shell.setup(brew or apt)
#     scripts.tools.install_nvim(brew or snap)
#     scripts.tools.install_btop(brew or snap)
#     scripts.git.setup(brew or apt)
#     scripts.tools.setup_fonts(brew or apt)

#     # setup dev tools
#     scripts.setup_python(brew or apt)
#     scripts.setup_node(brew)


# if __name__ == "__main__":
#     config.report(None)
#     setup()
