"""Package selection, presence checks, and failure handling."""

import subprocess

import pytest

from app.models import Failure, Package, PkgManager, Platform
from app.ops import managers as machine_managers
from app.ops import packages as machine_packages


@pytest.fixture
def commands(monkeypatch):
    calls = []
    monkeypatch.setattr(machine_packages.settings, "dry_run", False)
    monkeypatch.setattr(machine_packages, "refresh_path", lambda: None)
    monkeypatch.setattr(machine_packages.shutil, "which", lambda name: name)

    def run(cmd, *, env=None, label="", capture_output=False):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"" if capture_output else None)

    monkeypatch.setattr(machine_packages, "run", run)
    return calls


@pytest.mark.parametrize(
    "source,platform",
    [
        ("brew", Platform.MACOS),
        ("cask", Platform.MACOS),
        ("mas", Platform.MACOS),
        ("winget", Platform.WINDOWS),
        ("scoop", Platform.WINDOWS),
        ("apt", Platform.WSL),
        ("snap", Platform.LINUX),
    ],
)
@pytest.mark.parametrize("installed", [False, True])
def test_install_only_when_selected_manager_lacks_package(
    monkeypatch, commands, source, platform, installed
):
    monkeypatch.setattr(machine_packages, "PLATFORM", platform)
    queries = []
    value = 123 if source == "mas" else "example"
    package = Package.model_validate({"name": "example", source: value})

    def query(cmd, **kwargs):
        queries.append(cmd)
        if source == "mas":
            output = "123 Example App\n" if installed else ""
        elif source == "apt":
            output = "install ok installed" if installed else "deinstall ok config-files"
        else:
            output = "example\n" if installed else ""
        rc = 0 if installed or source in {"mas", "apt"} else 1
        return subprocess.CompletedProcess(cmd, rc, stdout=output)

    monkeypatch.setattr(machine_managers.subprocess, "run", query)
    manager = PkgManager.BREW if source == "cask" else PkgManager(source)
    assert machine_packages.install_packages([package, package], [manager]) == []
    expected = machine_managers.MANAGER_CONFIGS[source].install_cmd.format(value)
    if installed:
        assert commands == []
    else:
        assert commands and all(cmd == expected for cmd in commands)
    assert len(queries) == 1
    assert len(commands) == (0 if installed else 1)
    if source in {"brew", "cask"}:
        assert queries[0] == [
            "brew",
            "list",
            "--formula" if source == "brew" else "--cask",
            "example",
        ]
    if source == "winget":
        assert queries[0] == ["winget", "list", "--id", "example"]


@pytest.mark.parametrize(
    "declared,available,expected",
    [
        ([], {"winget", "scoop"}, "Manager not declared: winget, scoop"),
        ([PkgManager.SCOOP], {"winget"}, "No manager available"),
        ([PkgManager.SCOOP], {"winget", "scoop"}, None),
    ],
)
def test_source_selection_enforces_declarations(
    monkeypatch, commands, declared, available, expected
):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)
    monkeypatch.setattr(machine_packages.shutil, "which", lambda n: n if n in available else None)
    monkeypatch.setattr(machine_managers, "source_installed", lambda *args: False)
    package = Package(name="example", winget="Example.App", scoop="example", script="fallback")
    failures = machine_packages.install_packages([package], declared, owners={"example": "test"})
    assert failures == (
        [Failure(module="test", item="example", detail=expected)] if expected else []
    )
    assert commands == ([] if expected else ["scoop install example"])


def test_platform_skips_and_script_package_deploy_update(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.LINUX)
    monkeypatch.setattr(machine_packages.shutil, "which", lambda name: None)
    packages = [Package(cask="foreign"), Package(name="example", cask="example", script="setup")]
    assert machine_packages.install_packages(packages, []) == []
    assert commands == ["setup"]
    commands.clear()
    monkeypatch.setattr(machine_packages.shutil, "which", lambda name: name)
    assert machine_packages.install_packages(packages, []) == []
    assert commands == []
    assert machine_packages.install_packages(packages, [], rerun_script_packages=True) == []
    assert commands == ["setup"]


@pytest.mark.parametrize("source,platform", [("winget", Platform.WINDOWS), ("mas", Platform.MACOS)])
def test_dry_run_does_not_query_missing_manager(monkeypatch, commands, source, platform):
    monkeypatch.setattr(machine_packages, "PLATFORM", platform)
    monkeypatch.setattr(machine_packages.settings, "dry_run", True)
    monkeypatch.setattr(machine_packages.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        machine_managers.subprocess, "run", lambda *a, **kw: pytest.fail("queried missing manager")
    )
    package = Package.model_validate(
        {"name": "example", source: 123 if source == "mas" else "Example.App"}
    )
    assert machine_packages.install_packages([package], [PkgManager(source)]) == []
    assert len(commands) == 1


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, ["mas", "list"]),
        subprocess.TimeoutExpired(["mas", "list"], 30),
        FileNotFoundError("mas disappeared"),
    ],
)
def test_list_query_failure_blocks_affected_packages_only(monkeypatch, commands, error):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.MACOS)
    queries = []

    def query(cmd, **kwargs):
        queries.append(cmd)
        assert kwargs["check"]
        raise error

    monkeypatch.setattr(machine_managers.subprocess, "run", query)
    packages = [
        Package(name="first", mas=123),
        Package(name="second", mas=456),
        Package(name="script", script="setup"),
    ]
    failures = machine_packages.install_packages(
        packages, [PkgManager.MAS], rerun_script_packages=True
    )
    assert [failure.item for failure in failures] == ["first", "second"]
    assert len(queries) == 2
    assert commands == ["setup"]


def test_per_package_query_timeout_is_reported(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)

    def query(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 30)

    monkeypatch.setattr(machine_managers.subprocess, "run", query)
    failures = machine_packages.install_packages(
        [Package(winget="Example.App")], [PkgManager.WINGET]
    )
    assert len(failures) == 1
    assert commands == []


@pytest.mark.parametrize(
    "output,success",
    [
        (b"Found an existing package already installed. No available upgrade found", True),
        (b"installation failed", False),
    ],
)
def test_winget_noop_and_install_failure(monkeypatch, commands, output, success):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)
    monkeypatch.setattr(machine_managers, "source_installed", lambda *args: False)
    monkeypatch.setattr(
        machine_packages,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(
            cmd, 1, stdout=output if kw.get("capture_output") else None
        ),
    )
    failures = machine_packages.install_packages(
        [Package(winget="Example.App")], [PkgManager.WINGET]
    )
    assert failures == (
        [] if success else [Failure(module="?", item="Example.App", detail="winget exit 1")]
    )


def test_queries_resolve_windows_shims(monkeypatch):
    executable = r"C:\Users\test\scoop\shims\scoop.CMD"
    monkeypatch.setattr(machine_managers.shutil, "which", lambda name: executable)
    commands = []

    def query(cmd, **kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="")

    monkeypatch.setattr(machine_managers.subprocess, "run", query)
    assert machine_managers.source_installed("scoop", "7zip")
    assert commands == [[executable, "list", "7zip"]]


def test_manager_validation_checks_platform_and_dependencies(monkeypatch) -> None:
    cases = [
        (Platform.WINDOWS, [PkgManager.WINGET, PkgManager.SCOOP], set(), True),
        (Platform.WINDOWS, [PkgManager.BREW], set(), False),
        (Platform.MACOS, [PkgManager.BREW, PkgManager.MAS], set(), True),
        (Platform.MACOS, [PkgManager.MAS], {"brew"}, False),
        (Platform.MACOS, [PkgManager.SNAP], {"snap"}, False),
        (Platform.LINUX, [PkgManager.SNAP], set(), False),
        (Platform.LINUX, [PkgManager.SNAP], {"snap"}, True),
        (Platform.LINUX, [PkgManager.APT], set(), False),
        (Platform.WSL, [PkgManager.APT, PkgManager.SNAP], {"apt"}, True),
        (Platform.LINUX, [PkgManager.MAS, PkgManager.BREW], set(), False),
    ]
    for platform, managers, installed, valid in cases:
        monkeypatch.setattr(machine_managers, "PLATFORM", platform)
        monkeypatch.setattr(
            machine_managers.shutil, "which", lambda name: name if name in installed else None
        )
        if valid:
            machine_managers.validate_managers(managers)
        else:
            with pytest.raises(ValueError):
                machine_managers.validate_managers(managers)


def test_package_preview_uses_declared_platform_preference(monkeypatch):
    package = Package(
        name="example", brew="example", cask="example", winget="Example.App", scoop="example"
    )
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)
    managers = [PkgManager.WINGET, PkgManager.SCOOP]
    assert machine_packages.select_package_source(package, managers) == "winget"
    assert machine_packages.select_package_source(package, managers, {PkgManager.SCOOP}) == "scoop"
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.MACOS)
    assert machine_packages.select_package_source(package, [PkgManager.BREW]) == "cask"


@pytest.mark.parametrize(
    "listed_id,installed", [("Microsoft.App", True), ("Microsoft.App.Preview", False)]
)
def test_winget_presence_matches_full_id_case_insensitively(monkeypatch, listed_id, installed):
    monkeypatch.setattr(
        machine_managers,
        "_query",
        lambda cmd: subprocess.CompletedProcess(
            cmd, 0, stdout=f"Name Id Version Source\nApp {listed_id} 1.0 winget\n"
        ),
    )
    assert machine_managers.source_installed("winget", "microsoft.app") is installed


def test_presence_cache_is_local_to_each_install_run(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)
    queries = []
    monkeypatch.setattr(
        machine_managers, "source_installed", lambda *args: queries.append(args) or False
    )
    package = Package(winget="Example.App")
    for _ in range(2):
        assert machine_packages.install_packages([package, package], [PkgManager.WINGET]) == []
    assert len(queries) == 2
    assert len(commands) == 2


def test_failed_install_does_not_mark_package_installed(monkeypatch, commands):
    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WINDOWS)
    queries = []
    monkeypatch.setattr(
        machine_managers, "source_installed", lambda *args: queries.append(args) or False
    )
    monkeypatch.setattr(
        machine_packages,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd, 1, stdout=b"failed" if kwargs.get("capture_output") else None
        ),
    )
    package = Package(winget="Example.App")
    failures = machine_packages.install_packages([package, package], [PkgManager.WINGET])
    assert len(queries) == 1
    assert len(failures) == 2
