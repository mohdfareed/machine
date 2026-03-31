"""Package installation edge-case tests."""

from importlib import import_module

from machine.manifest import Package

machine_app = import_module("machine.app")


def test_install_succeeded_accepts_winget_noop() -> None:
    """Winget reports already-installed packages with a non-zero no-op exit."""
    output = (
        "Found an existing package already installed. Trying to upgrade the installed package...\n"
        "No available upgrade found.\n"
        "No newer package versions are available from the configured sources.\n"
    ).encode()

    assert machine_app._install_succeeded("winget", 1, output)


def test_install_packages_records_winget_noop_as_installed(monkeypatch) -> None:
    """No-op winget upgrades should not be surfaced as apply failures."""
    package = Package(name="steam", winget="Valve.Steam")
    saved: dict = {}

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.WINDOWS)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(
        machine_app.shutil, "which", lambda name: "winget.exe" if name == "winget" else None
    )
    monkeypatch.setattr(machine_app, "_winget_installed", lambda package_id: False)
    monkeypatch.setattr(
        machine_app,
        "run_collect",
        lambda *args, **kwargs: (
            1,
            (
                "Found an existing package already installed. Trying to upgrade the installed "
                "package...\nNo available upgrade found.\n"
                "No newer package versions are available from the configured sources.\n"
            ).encode(),
        ),
    )

    failures = machine_app.install_packages([package], owners={"steam": "pc"})

    assert failures == []
    assert saved["packages"] == ["steam"]


def test_install_packages_skips_when_winget_already_manages_package(monkeypatch) -> None:
    """Apply should not attempt upgrades for packages already managed by winget."""
    package = Package(name="steam", winget="Valve.Steam")
    saved: dict = {}

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.WINDOWS)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(
        machine_app.shutil, "which", lambda name: "winget.exe" if name == "winget" else None
    )
    monkeypatch.setattr(
        machine_app, "_winget_installed", lambda package_id: package_id == "Valve.Steam"
    )

    called = False

    def _unexpected_install(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(machine_app, "_install", _unexpected_install)

    failures = machine_app.install_packages([package], owners={"steam": "pc"})

    assert failures == []
    assert not called
    assert saved["packages"] == ["steam"]


def test_install_packages_reinstalls_when_state_is_stale_for_winget(monkeypatch) -> None:
    """Apply should install with winget when the cache says installed but winget does not."""
    package = Package(name="steam", winget="Valve.Steam")
    saved: dict = {}

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.WINDOWS)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {"packages": ["steam"]})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(
        machine_app.shutil, "which", lambda name: "winget.exe" if name == "winget" else None
    )
    monkeypatch.setattr(machine_app, "_winget_installed", lambda package_id: False)

    calls = 0

    def _fake_install(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return None

    monkeypatch.setattr(machine_app, "_install", _fake_install)

    failures = machine_app.install_packages([package], owners={"steam": "pc"})

    assert failures == []
    assert calls == 1
    assert saved["packages"] == ["steam"]


def test_install_packages_skips_non_applicable_sources(monkeypatch) -> None:
    """Packages with only foreign-platform sources should be skipped cleanly."""
    package = Package(name="zsh", brew="zsh")
    saved: dict = {}

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.WINDOWS)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(
        machine_app.shutil, "which", lambda name: "winget.exe" if name == "winget" else None
    )

    called = False

    def _unexpected_install(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(machine_app, "_install", _unexpected_install)

    failures = machine_app.install_packages([package], owners={"zsh": "shell"})

    assert failures == []
    assert not called
    assert saved["packages"] == []


def test_install_packages_uses_cask_source_on_macos(monkeypatch) -> None:
    """macOS should install casks via brew install --cask."""
    package = Package(name="zed", cask="zed", winget="ZedIndustries.Zed")
    saved: dict = {}
    commands: list[str] = []

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.MACOS)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(
        machine_app.shutil,
        "which",
        lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None,
    )
    monkeypatch.setattr(machine_app, "_winget_installed", lambda package_id: False)

    def _fake_run_collect(cmd, **kwargs):  # type: ignore[no-untyped-def]
        commands.append(cmd)
        return 0, bytearray()

    monkeypatch.setattr(machine_app, "run_collect", _fake_run_collect)

    failures = machine_app.install_packages([package], owners={"zed": "zed"})

    assert failures == []
    assert commands == ["brew install --cask zed"]
    assert saved["packages"] == ["zed"]


def test_install_packages_uses_script_when_no_native_source_applies(monkeypatch) -> None:
    """Script installs should be used when no manager source applies on this platform."""
    package = Package(name="tailscale", cask="tailscale", script="install tailscale")
    saved: dict = {}
    commands: list[str] = []

    monkeypatch.setattr(machine_app, "PLATFORM", machine_app.Platform.LINUX)
    monkeypatch.setattr(machine_app, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_app, "_load_state", lambda: {})
    monkeypatch.setattr(machine_app, "_save_state", lambda state: saved.update(state))
    monkeypatch.setattr(machine_app.shutil, "which", lambda name: None)

    def _fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        commands.append(cmd)
        return 0

    monkeypatch.setattr(machine_app, "run", _fake_run)

    failures = machine_app.install_packages([package], owners={"tailscale": "homelab"})

    assert failures == []
    assert commands == ["install tailscale"]
    assert saved["packages"] == ["tailscale"]
