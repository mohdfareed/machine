"""Resolved package execution, exact presence, and failure handling."""

import json
import subprocess

import pytest
from app import env as machine_env
from app import managers as machine_managers
from app import validation
from app.models import Package, PkgManager, Platform
from app.ops import packages as machine_packages


@pytest.fixture
def commands(monkeypatch):
    calls = []
    monkeypatch.setattr(machine_packages, "find_executable", lambda name, **kwargs: name)

    def run(command, **kwargs):
        calls.append(command)
        if kwargs["dry_run"]:
            return None
        return subprocess.CompletedProcess(command, 0, stdout=b"")

    monkeypatch.setattr(machine_packages, "run", run)
    monkeypatch.setattr(machine_managers, "run", run)
    return calls


@pytest.mark.parametrize("source", ["brew", "cask", "mas", "scoop"])
@pytest.mark.parametrize("installed", [False, True])
def test_install_only_when_selected_manager_lacks_package(monkeypatch, commands, source, installed):
    identity = 123 if source == "mas" else "example"
    package = Package.model_validate({"name": "example", source: identity})
    package.selected_source = source
    queries = []
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda *args, **kwargs: pytest.fail("rechecked manager readiness per package"),
    )

    def query(command, **kwargs):
        queries.append(command)
        assert kwargs["env"] == {"PATH": "chosen"}
        if source == "mas":
            output = "123 Example App\n" if installed else "456 Other\n"

        elif source == "scoop":
            output = json.dumps({"apps": [{"Name": "example" if installed else "example-extra"}]})
        else:
            key = "formulae" if source == "brew" else "casks"
            output = json.dumps({key: [{"installed": ["1.0"] if installed else []}]})
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(machine_managers, "query", query)

    machine_packages.install_packages([package, package], env={"PATH": "chosen"}, dry_run=False)
    assert len(queries) == 1
    assert len(commands) == (0 if installed else 1)


def test_brew_presence_resolves_aliases_through_brew(monkeypatch):
    commands = []

    def query(command, **kwargs):
        commands.append(command)
        output = {"formulae": [{"name": "python@3.14", "installed": [{"version": "3.14"}]}]}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(output))

    monkeypatch.setattr(machine_managers, "query", query)
    assert machine_managers.source_installed("brew", "python", env={})
    assert commands == [["brew", "info", "--json=v2", "--formula", "python"]]


def test_source_choice_does_not_fall_back_to_an_available_manager(monkeypatch, commands):
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda name, **kwargs: name if name == "scoop" else None,
    )
    package = Package(name="example", winget="Example.App", scoop="example")
    package.selected_source = "winget"
    machine_packages.install_packages([package], env={}, dry_run=False)
    assert len(commands) == 1
    assert commands[0][:4] == ["winget", "install", "--id", "Example.App"]


def test_preview_shows_installation_without_presence_checks(monkeypatch, commands):
    managed = Package(name="managed", brew="managed")
    managed.selected_source = "brew"
    custom = Package(name="custom", cmd="setup-custom")
    monkeypatch.setattr(
        machine_managers,
        "source_installed",
        lambda *args, **kwargs: pytest.fail("queried package presence during preview"),
    )
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda *args, **kwargs: pytest.fail("queried executable during preview"),
    )

    def preview(command, **kwargs):
        assert kwargs["dry_run"] is True
        commands.append(command)

    monkeypatch.setattr(machine_managers, "run", preview)
    monkeypatch.setattr(machine_packages, "run", preview)

    machine_packages.install_packages([managed, custom], env={}, dry_run=True)
    assert commands == [["brew", "install", "managed"], "setup-custom"]


def test_preview_missing_manager_skips_presence_queries(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "find_executable", lambda name, **kwargs: None)
    monkeypatch.setattr(
        machine_managers, "query", lambda *args, **kwargs: pytest.fail("queried absent manager")
    )
    package = Package(name="example", brew="example")
    package.selected_source = "brew"
    machine_packages.install_packages([package], env={}, dry_run=True)
    assert commands == [["brew", "install", "example"]]


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, ["brew", "list"]),
        subprocess.TimeoutExpired(["brew", "list"], 30),
        FileNotFoundError("brew disappeared"),
    ],
)
def test_query_failure_stops_before_installing(monkeypatch, commands, error):
    def query(command, **kwargs):
        raise error

    monkeypatch.setattr(machine_managers, "query", query)
    package = Package(name="example", brew="example")
    package.selected_source = "brew"
    with pytest.raises(type(error)) as caught:
        machine_packages.install_packages([package, package], env={}, dry_run=False)
    assert caught.value is error
    assert commands == []


@pytest.mark.parametrize("code", [0, 0x8A150061, 0x8A150061 - 2**32, 1, 0x8A15002B])
def test_winget_install_interprets_its_status_without_presence_queries(monkeypatch, code):
    monkeypatch.setattr(
        machine_managers, "query", lambda *args, **kwargs: pytest.fail("queried WinGet presence")
    )
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda *args, **kwargs: pytest.fail("rechecked WinGet readiness per package"),
    )
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        assert "--no-upgrade" in command
        assert not kwargs.get("capture_output")
        assert not kwargs["check"]
        return subprocess.CompletedProcess(command, code)

    monkeypatch.setattr(machine_managers, "run", run)
    package = Package(name="example", winget="Example.App")
    package.selected_source = "winget"
    if code in (0, 0x8A150061, 0x8A150061 - 2**32):
        machine_packages.install_packages([package, package], env={}, dry_run=False)
    else:
        with pytest.raises(RuntimeError):
            machine_packages.install_packages([package, package], env={}, dry_run=False)
    assert len(calls) == 1


def test_custom_packages_check_availability_again_after_install(monkeypatch, commands):
    env = {"DEV": "selected-machine"}
    installed = set()
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda name, **kwargs: name if name in installed else None,
    )
    seen = []

    def run(command, **kwargs):
        assert kwargs["env"] is env
        seen.append((command, dict(kwargs["env"])))
        installed.add("later")

    monkeypatch.setattr(machine_packages, "run", run)
    first = Package(name="first", cmd="setup-first", up_cmd=True)
    later = Package(name="later", cmd="setup-later")
    machine_packages.install_packages([first, later], env=env, dry_run=False)
    assert seen == [("setup-first", {"DEV": "selected-machine"})]
    assert machine_packages.upgrade_packages([first, later], env=env, dry_run=False) == ["later"]
    assert seen[-1] == ("setup-first", env)


@pytest.mark.parametrize("dry_run", [False, True])
def test_managed_packages_run_declared_upgrade_commands(monkeypatch, dry_run):
    packages = [
        Package(name="custom-upgrade", brew="first", up_cmd="upgrade-first"),
        Package(name="reuse-setup", brew="second", cmd="setup-second", up_cmd=True),
        Package(name="manager-only", brew="third"),
    ]
    for package in packages:
        package.selected_source = "brew"
    env = {"MC_ID": "test"}
    seen = []

    def run(command, **kwargs):
        assert kwargs == {"env": env, "dry_run": dry_run, "check": True}
        seen.append(command)

    monkeypatch.setattr(machine_packages, "run", run)
    assert machine_packages.upgrade_packages(packages, env=env, dry_run=dry_run) == []
    assert seen == ["upgrade-first", "setup-second"]


@pytest.mark.parametrize("platform", [Platform.MAC, Platform.WSL])
def test_homebrew_upgrades_casks_only_on_macos(monkeypatch, commands, platform):
    monkeypatch.setattr(machine_env, "PLATFORM", platform)

    machine_managers.upgrade_managers([PkgManager.BREW], env={}, dry_run=False)

    assert ["brew", "upgrade"] in commands
    assert (["brew", "upgrade", "--cask", "--greedy-latest"] in commands) == (
        platform == Platform.MAC
    )


def test_presence_cache_does_not_survive_an_invocation(monkeypatch, commands):
    queries = []
    monkeypatch.setattr(
        machine_managers, "source_installed", lambda *args, **kwargs: queries.append(args) or False
    )
    package = Package(name="example", brew="example")
    package.selected_source = "brew"
    for _ in range(2):
        machine_packages.install_packages([package, package], env={}, dry_run=False)
    assert len(queries) == len(commands) == 2


@pytest.mark.parametrize(
    "operation", ["install", "custom-install", "custom-upgrade", "manager-upgrade"]
)
def test_first_command_failure_stops_remaining_work(monkeypatch, commands, operation):
    monkeypatch.setattr(machine_managers, "source_installed", lambda *args, **kwargs: False)

    failure = subprocess.CalledProcessError(1, ["installer"])

    def fail(command, **kwargs):
        commands.append(command)
        raise failure

    monkeypatch.setattr(machine_packages, "run", fail)
    monkeypatch.setattr(machine_managers, "run", fail)
    with pytest.raises(subprocess.CalledProcessError) as caught:
        if operation == "install":
            package = Package(name="example", brew="example")
            package.selected_source = "brew"
            machine_packages.install_packages([package, package], env={}, dry_run=False)
        elif operation == "custom-install":
            monkeypatch.setattr(machine_packages, "find_executable", lambda *args, **kwargs: None)
            package = Package(name="example", cmd="setup")
            machine_packages.install_packages([package, package], env={}, dry_run=False)
        elif operation == "custom-upgrade":
            package = Package(name="example", cmd="setup", up_cmd=True)
            machine_packages.upgrade_packages([package, package], env={}, dry_run=False)
        else:
            machine_managers.upgrade_managers(
                [PkgManager.BREW, PkgManager.MAS], env={}, dry_run=False
            )
    assert caught.value is failure
    assert len(commands) == 1


def test_preflight_checks_all_resolved_managers(monkeypatch):
    selected_env = {"MC_ID": "test"}
    checked = []

    def find_executable(name, *, env):
        assert env is selected_env
        checked.append(name)
        return name

    monkeypatch.setattr(validation, "find_executable", find_executable)
    validation.validate_managers(list(PkgManager), env=selected_env)
    assert checked == list(PkgManager)

    monkeypatch.setattr(validation, "find_executable", lambda name, **kwargs: None)
    for manager in PkgManager:
        with pytest.raises(FileNotFoundError):
            validation.validate_managers([manager], env=selected_env)


@pytest.mark.parametrize(
    "managers,installer",
    [
        ([PkgManager.BREW, PkgManager.MAS], ["brew", "install", "mas"]),
        (
            [PkgManager.WINGET, PkgManager.SCOOP],
            "$installer = Invoke-RestMethod -Uri https://get.scoop.sh\n"
            "& ([scriptblock]::Create($installer))",
        ),
        ([PkgManager.BREW], None),
    ],
)
@pytest.mark.parametrize("installed", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_manager_setup_installs_only_missing_native_managers(
    monkeypatch, managers, installer, installed, dry_run
):
    selected_env = {"MC_ID": "test"}
    commands = []
    checked = []

    def find_executable(name, *, env):
        assert env is selected_env
        checked.append(name)
        return installed

    def run(command, **kwargs):
        assert kwargs == {"env": selected_env, "dry_run": dry_run, "check": True}
        commands.append(command)

    monkeypatch.setattr(machine_managers, "find_executable", find_executable)
    monkeypatch.setattr(machine_managers, "run", run)
    machine_managers.setup_managers(managers, env=selected_env, dry_run=dry_run)
    assert commands == ([installer] if installer is not None and not installed else [])
    assert checked == (managers[1:] if installer is not None else [])


def test_manager_setup_stops_on_native_installation_failure(monkeypatch):
    monkeypatch.setattr(machine_managers, "find_executable", lambda *args, **kwargs: None)
    commands = []
    failure = subprocess.CalledProcessError(1, ["brew", "install", "mas"])

    def fail(command, **kwargs):
        commands.append(command)
        raise failure

    monkeypatch.setattr(machine_managers, "run", fail)
    with pytest.raises(subprocess.CalledProcessError) as caught:
        machine_managers.setup_managers([PkgManager.MAS, PkgManager.SCOOP], env={}, dry_run=False)
    assert caught.value is failure
    assert commands == [["brew", "install", "mas"]]
