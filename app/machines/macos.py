"""macOS machine."""

from functools import partial
from pathlib import Path

import typer

from app import config, pkg_managers, utils
from app.plugins import git, private_files, shell, ssh, tailscale, tools, vscode

PAM_SUDO = Path("/") / "etc" / "pam.d" / "sudo_local"
PAM_SUDO_MODULE = "pam_tid.so"
PAM_SUDO_CONTENT = f"""
auth       sufficient     {PAM_SUDO_MODULE}
""".strip()
VSCODE_TUNNELS_NAME = "macbook"

configuration = config.MacOS()
plugins = [
    utils.create_plugin(git, partial(git.setup, configuration)),
    utils.create_plugin(private_files),
    utils.create_plugin(shell, partial(shell.setup, configuration)),
    utils.create_plugin(ssh, partial(ssh.setup, configuration.ssh_config)),
    utils.create_plugin(
        vscode,
        partial(vscode.setup, configuration),
        partial(vscode.setup_tunnels, VSCODE_TUNNELS_NAME),
    ),
    utils.create_plugin(tailscale),
    utils.create_plugin(tools),
]

machine_app = typer.Typer(name="macos", help="macOS machine configuration.")
for plugin in plugins:
    machine_app.add_typer(plugin)


@machine_app.command()
def setup(private_dir: private_files.PrivateDirArg) -> None:
    """Setup macOS on a new machine."""
    utils.LOGGER.debug("Configurations: %s", configuration)

    # setup package managers
    brew = pkg_managers.Brew()
    brew.setup()
    mas = pkg_managers.MAS()
    mas.setup()

    # setup private files
    private_files.setup(private_dir)

    # setup shell
    shell.setup(configuration)
    tools.install_btop()
    tools.install_nvim()

    # setup ssh
    ssh.setup(configuration.ssh_config)
    ssh.setup_server()

    # setup core machine
    git.setup(configuration)
    vscode.setup(configuration)
    vscode.setup_tunnels(VSCODE_TUNNELS_NAME)
    tailscale.setup()
    tools.setup_fonts()
    brew.install_brewfile(configuration.brewfile)

    # setup dev tools
    tools.install_powershell(configuration)
    tools.setup_python()
    tools.setup_node()
    tools.setup_docker()
    brew.install("go")
    brew.install("dotnet-sdk", cask=True)
    brew.install("godot-mono", cask=True)

    system_preferences()
    enable_touch_id()


@machine_app.command()
def system_preferences() -> None:
    """Open macOS System Preferences."""
    utils.LOGGER.info("Opening System Preferences...")
    utils.Shell().execute(f". {configuration.system_preferences}")


@machine_app.command()
def enable_touch_id() -> None:
    """Enable Touch ID for sudo on macOS."""
    utils.LOGGER.info("Enabling Touch ID for sudo...")
    if not PAM_SUDO.exists():
        PAM_SUDO.parent.mkdir(parents=True, exist_ok=True)
        utils.Shell().execute(f"sudo touch {PAM_SUDO}")

    pam_sudo_contents = PAM_SUDO.read_text()
    if PAM_SUDO_MODULE in pam_sudo_contents:
        utils.LOGGER.info("Touch ID for sudo already enabled.")
        return

    utils.Shell().execute(
        f"echo '{PAM_SUDO_CONTENT}' | sudo tee {PAM_SUDO} > /dev/null"
    )
    utils.LOGGER.info("Touch ID for sudo enabled.")


@machine_app.command()
def accept_xcode_license() -> None:
    """Accept the Xcode license."""
    utils.LOGGER.info("Authenticate to accept Xcode license.")

    try:  # ensure xcode license is accepted
        utils.Shell().execute("sudo xcodebuild -license accept", info=True)
    except utils.shell.ShellError as ex:
        utils.LOGGER.error("Failed to accept Xcode license: %s", ex)
        utils.LOGGER.error("Ensure Xcode is installed using: xcode-select --install")
        raise typer.Abort()
