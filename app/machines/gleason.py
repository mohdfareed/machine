"""Gleason work machine."""

__all__ = ["Gleason"]


from app import config, env, plugins, utils
from app.machine import MachinePlugin
from app.models import PluginProtocol
from app.plugins.pkg_managers.windows import Winget


class Gleason(MachinePlugin[config.Gleason, env.Windows]):
    """Gleason machine configuration."""

    shell = utils.Shell()

    @property
    def _config(self) -> config.Gleason:
        return config.Gleason()

    @property
    def _env(self) -> env.Windows:
        return env.Windows(env_file=self._config.ps_profile)

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [
            plugins.Fonts,
            plugins.Git,
            plugins.PowerShell,
            plugins.NeoVim,
            plugins.Btop,
            plugins.Git,
            plugins.VSCode,
            plugins.Btop,
            plugins.Docker,
            plugins.Python,
        ]

    @classmethod
    def is_supported(cls) -> bool:
        return utils.WINDOWS

    def setup(self) -> None:
        super().setup()
        self.set_shell()
        Winget().install("GoLang.Go Microsoft.DotNet.SDK")

    def set_shell(self, shell: str = "/usr/bin/zsh") -> None:
        """Set the machine's default shell."""
        utils.LOGGER.info("Setting the default shell to: %s", shell)
        self.shell.execute(f'sudo chsh "$(id -un)" --shell "{shell}"')


# @core.machine_setup
# def wsl_setup() -> None:
#     """Setup WSL on a new Gleason Windows machine."""

#     # package managers
#     brew = package_managers.HomeBrew.safe_setup()
#     apt = package_managers.APT()
#     snap = package_managers.SnapStore(apt)

#     # setup core machine
#     scripts.git.setup(brew or apt, gitconfig=gleason.gitconfig)
#     scripts.shell.setup(brew or apt)
#     scripts.tools.install_nvim(brew or snap)
#     scripts.tools.install_btop(brew or snap)
#     scripts.tools.setup_fonts(brew or apt)

#     # setup dev tools
#     scripts.setup_python(brew or apt)
#     scripts.setup_node(brew)
