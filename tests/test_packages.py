"""Resolved package execution, exact presence, and failure handling."""

import json
import subprocess

import pytest
from app.config import validation
from app.config.models import Package, PkgManager, Platform
from app.deployment import managers as machine_managers
from app.deployment import packages as machine_packages
from app.runtime import env as machine_env


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
    identity = {"mas": 123, "scoop": "extras/example"}.get(source, "example")
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
            output = "123 Example App\n" if installed else "1234 Other App\n"
        elif source == "scoop":
            output = json.dumps({"apps": [{"Name": "EXAMPLE" if installed else "example-extra"}]})
        else:
            key = "formulae" if source == "brew" else "casks"
            output = json.dumps(
                {key: [{"name": "canonical-example", "installed": ["1.0"] if installed else []}]}
            )
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(machine_managers, "query", query)

    machine_packages.install_packages([package, package], env={"PATH": "chosen"}, dry_run=False)
    expected_query = {
        "brew": ["brew", "info", "--json=v2", "--formula", identity],
        "cask": ["brew", "info", "--json=v2", "--cask", identity],
        "mas": ["mas", "list"],
        "scoop": ["scoop", "export"],
    }[source]
    expected_install = {
        "brew": ["brew", "install", identity],
        "cask": ["brew", "install", "--cask", identity],
        "mas": ["mas", "install", str(identity)],
        "scoop": ["scoop", "install", identity],
    }[source]
    assert queries == [expected_query]
    assert commands == ([] if installed else [expected_install])


def test_source_choice_does_not_fall_back_to_an_available_manager(monkeypatch, commands):
    monkeypatch.setattr(
        machine_packages,
        "find_executable",
        lambda name, **kwargs: name if name == "scoop" else None,
    )
    package = Package(name="example", winget="Example.App", scoop="example", cmd="setup")
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


def test_query_failure_stops_before_installing(monkeypatch, commands):
    error = subprocess.CalledProcessError(1, ["brew", "info"])

    def query(command, **kwargs):
        raise error

    monkeypatch.setattr(machine_managers, "query", query)
    package = Package(name="example", brew="example")
    package.selected_source = "brew"
    with pytest.raises(type(error)) as caught:
        machine_packages.install_packages(
            [package, Package(name="later", cmd="setup-later")], env={}, dry_run=False
        )
    assert caught.value is error
    assert commands == []


@pytest.mark.parametrize("code", [0, 0x8A150061, 0x8A150061 - 2**32, 0x8A15002B])
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


def test_custom_packages_check_availability_again_after_install(monkeypatch):
    env = {"DEV": "selected-machine"}
    installed = set()

    def find_executable(name, **kwargs):
        assert kwargs["env"] == env
        return name if name in installed else None

    monkeypatch.setattr(machine_packages, "find_executable", find_executable)
    seen = []

    def run(command, **kwargs):
        assert kwargs["env"] == env
        seen.append(command)
        installed.add("later")

    monkeypatch.setattr(machine_packages, "run", run)
    first = Package(name="first", cmd="setup-first")
    later = Package(name="later", cmd="setup-later")
    machine_packages.install_packages([first, later], env=env, dry_run=False)
    assert seen == ["setup-first"]


@pytest.mark.parametrize("dry_run", [False, True])
def test_upgrade_commands_and_manual_maintenance_selection(monkeypatch, dry_run):
    managed = [
        Package(name="custom-upgrade", brew="first", up_cmd="upgrade-first"),
        Package(name="reuse-setup", brew="second", cmd="setup-second", up_cmd=True),
        Package(name="manager-only", brew="third"),
    ]
    for package in managed:
        package.selected_source = "brew"
    packages = [
        *managed,
        Package(name="custom", cmd="setup-custom", up_cmd=True),
        Package(name="manual", cmd="setup-manual"),
    ]
    env = {"MC_ID": "test"}
    seen = []

    def run(command, **kwargs):
        assert kwargs["env"] == env
        assert kwargs["dry_run"] is dry_run
        assert kwargs["check"] is True
        seen.append(command)

    monkeypatch.setattr(machine_packages, "run", run)
    assert machine_packages.upgrade_packages(packages, env=env, dry_run=dry_run) == ["manual"]
    assert seen == ["upgrade-first", "setup-second", "setup-custom"]


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
            packages = [Package(name="first", brew="first"), Package(name="later", brew="later")]
            for package in packages:
                package.selected_source = "brew"
            machine_packages.install_packages(packages, env={}, dry_run=False)
        elif operation == "custom-install":
            monkeypatch.setattr(machine_packages, "find_executable", lambda *args, **kwargs: None)
            machine_packages.install_packages(
                [
                    Package(name="first", cmd="setup-first"),
                    Package(name="later", cmd="setup-later"),
                ],
                env={},
                dry_run=False,
            )
        elif operation == "custom-upgrade":
            machine_packages.upgrade_packages(
                [
                    Package(name="first", cmd="setup-first", up_cmd=True),
                    Package(name="later", cmd="setup-later", up_cmd=True),
                ],
                env={},
                dry_run=False,
            )
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
        assert env == selected_env
        checked.append(name)
        return name

    monkeypatch.setattr(validation, "find_executable", find_executable)
    validation.validate_managers(list(PkgManager), env=selected_env)
    assert set(checked) == set(PkgManager)

    monkeypatch.setattr(
        validation,
        "find_executable",
        lambda name, **kwargs: None if name == PkgManager.MAS else name,
    )
    with pytest.raises(FileNotFoundError):
        validation.validate_managers([PkgManager.BREW, PkgManager.MAS], env=selected_env)


@pytest.mark.parametrize(
    "managers,installed,dry_run",
    [
        ([PkgManager.BREW, PkgManager.MAS], False, False),
        ([PkgManager.WINGET, PkgManager.SCOOP], False, False),
        ([PkgManager.BREW, PkgManager.MAS], True, False),
        ([PkgManager.WINGET, PkgManager.SCOOP], True, False),
        ([PkgManager.WINGET, PkgManager.SCOOP], False, True),
        ([PkgManager.BREW], False, False),
    ],
)
def test_manager_setup_installs_only_missing_native_managers(
    monkeypatch, managers, installed, dry_run
):
    selected_env = {"MC_ID": "test"}
    commands = []
    checked = []

    def find_executable(name, *, env):
        assert env == selected_env
        checked.append(name)
        return name if installed else None

    def run(command, **kwargs):
        assert kwargs["env"] == selected_env
        assert kwargs["dry_run"] is dry_run
        assert kwargs["check"] is True
        commands.append(command)

    monkeypatch.setattr(machine_managers, "find_executable", find_executable)
    monkeypatch.setattr(machine_managers, "run", run)
    machine_managers.setup_managers(managers, env=selected_env, dry_run=dry_run)
    assert checked == managers[1:]
    if installed or len(managers) == 1:
        assert commands == []
        return
    assert len(commands) == 1
    if PkgManager.MAS in managers:
        assert commands[0] == ["brew", "install", "mas"]
        return
    assert commands[0] == (
        "$installer = Invoke-RestMethod -Uri https://get.scoop.sh\n"
        "& ([scriptblock]::Create($installer))"
    )


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
