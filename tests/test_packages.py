"""Resolved package execution, exact presence, and failure handling."""

import json
import subprocess

import pytest

from app import managers as machine_managers
from app.models import Package, PkgManager
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


@pytest.mark.parametrize("source", ["brew", "cask", "mas", "apt", "snap", "scoop", "winget"])
@pytest.mark.parametrize("installed", [False, True])
def test_install_only_when_selected_manager_lacks_package(monkeypatch, commands, source, installed):
    identity = 123 if source == "mas" else "example"
    package = Package.model_validate({"name": "example", source: identity})
    package.selected_source = source
    queries = []

    def query(command, **kwargs):
        queries.append(command)
        assert kwargs["env"] == {"PATH": "chosen"}
        if source == "mas":
            output = "123 Example App\n" if installed else "456 Other\n"
        elif source == "apt":
            status = "install ok installed" if installed else "deinstall ok config-files"
            output = f"example\t{status}\n"
        elif source == "scoop":
            output = json.dumps({"apps": [{"Name": "example" if installed else "example-extra"}]})
        elif source in {"snap", "winget"}:
            output = "Name Id Version\n" + ("example 1.0\n" if installed else "example-extra 1.0\n")
        else:
            key = "formulae" if source == "brew" else "casks"
            output = json.dumps({key: [{"installed": ["1.0"] if installed else []}]})
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(machine_managers, "query", query)
    manager = PkgManager.BREW if source == "cask" else PkgManager(source)
    skipped = machine_packages.install_packages(
        [package, package], env={"PATH": "chosen"}, dry_run=False
    )
    assert skipped == (["example", "example"] if installed else ["example"])
    assert len(queries) == 1
    assert len(commands) == (0 if installed else 1)


def test_snap_classic_is_only_an_install_argument(monkeypatch, commands):
    queries = []
    monkeypatch.setattr(
        machine_managers,
        "query",
        lambda command, **kwargs: (
            queries.append(command)
            or subprocess.CompletedProcess(
                command, 0, stdout="\n".join(["Name Version", "other 1.0"])
            )
        ),
    )
    package = Package(name="powershell", snap="powershell", snap_classic=True)
    package.selected_source = "snap"
    machine_packages.install_packages([package], env={}, dry_run=False)
    assert queries == [["snap", "list"]]
    assert commands == [["sudo", "snap", "install", "powershell", "--classic"]]


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
    with pytest.raises(RuntimeError, match="Selected manager is unavailable: winget"):
        machine_packages.install_packages([package], env={}, dry_run=False)
    assert commands == []


def test_preview_missing_manager_skips_presence_queries(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "find_executable", lambda name, **kwargs: None)
    monkeypatch.setattr(
        machine_managers, "query", lambda *args, **kwargs: pytest.fail("queried absent manager")
    )
    package = Package(name="example", brew="example")
    package.selected_source = "brew"
    assert machine_packages.install_packages([package], env={}, dry_run=True) == []
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
    with pytest.raises(RuntimeError) as caught:
        machine_packages.install_packages([package, package], env={}, dry_run=False)
    assert caught.value.__cause__ is error
    assert commands == []


def test_winget_absence_is_distinct_from_query_failure(monkeypatch):
    for code, absent in ((0x8A150014, True), (1, False)):
        monkeypatch.setattr(
            machine_managers,
            "query",
            lambda command, **kwargs: subprocess.CompletedProcess(command, code, stdout=""),
        )
        if absent:
            assert not machine_managers.source_installed("winget", "Example.App", env={})
        else:
            with pytest.raises(subprocess.CalledProcessError):
                machine_managers.source_installed("winget", "Example.App", env={})


@pytest.mark.parametrize("success", [False, True])
def test_winget_install_interprets_its_nonzero_result(monkeypatch, success):
    output = (
        b"Found an existing package already installed. No available upgrade found"
        if success
        else b"failed"
    )

    def run(command, **kwargs):
        assert kwargs["capture_output"] and kwargs["echo_output"]
        return subprocess.CompletedProcess(command, 1, stdout=output)

    monkeypatch.setattr(machine_managers, "run", run)
    package = Package(name="example", winget="Example.App")
    package.selected_source = "winget"
    if success:
        machine_managers.install_package(package, env={}, dry_run=False)
    else:
        with pytest.raises(RuntimeError):
            machine_managers.install_package(package, env={}, dry_run=False)


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
    assert machine_packages.install_packages([first, later], env=env, dry_run=False) == ["later"]
    assert seen == [("setup-first", {"DEV": "selected-machine"})]
    assert machine_packages.upgrade_packages([first, later], env=env, dry_run=False) == ["later"]
    assert seen[-1] == ("setup-first", env)


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


@pytest.mark.parametrize("operation", ["install", "custom-upgrade", "manager-upgrade"])
def test_first_command_failure_stops_remaining_work(monkeypatch, commands, operation):
    monkeypatch.setattr(machine_managers, "source_installed", lambda *args, **kwargs: False)

    def fail(command, **kwargs):
        commands.append(command)
        raise RuntimeError("command failed")

    monkeypatch.setattr(machine_packages, "run", fail)
    monkeypatch.setattr(machine_managers, "run", fail)
    with pytest.raises(RuntimeError):
        if operation == "install":
            package = Package(name="example", brew="example")
            package.selected_source = "brew"
            machine_packages.install_packages([package, package], env={}, dry_run=False)
        elif operation == "custom-upgrade":
            package = Package(name="example", cmd="setup", up_cmd=True)
            machine_packages.upgrade_packages([package, package], env={}, dry_run=False)
        else:
            machine_managers.upgrade_managers(
                [PkgManager.BREW, PkgManager.SNAP], env={}, dry_run=False
            )
    assert len(commands) == 1


def test_preflight_checks_only_live_prerequisites(monkeypatch):
    monkeypatch.setattr(machine_managers, "find_executable", lambda name, **kwargs: None)
    machine_managers.validate_managers([PkgManager.BREW, PkgManager.MAS, PkgManager.SCOOP], env={})
    for managers in ([PkgManager.WINGET], [PkgManager.APT], [PkgManager.SNAP]):
        with pytest.raises(FileNotFoundError):
            machine_managers.validate_managers(managers, env={})
    with pytest.raises(FileNotFoundError):
        machine_managers.validate_managers([PkgManager.BREW], env={}, for_upgrade=True)
    monkeypatch.setattr(
        machine_managers, "find_executable", lambda name, **kwargs: name if name == "apt" else None
    )
    machine_managers.validate_managers([PkgManager.APT, PkgManager.SNAP], env={})
