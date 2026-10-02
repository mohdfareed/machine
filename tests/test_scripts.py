"""Application script selection and sequential execution behavior."""

import subprocess
import sys
from pathlib import Path

import pytest
from app.config import loader as machine_loader
from app.config.models import Platform
from app.deployment import scripts as machine_scripts
from app.runtime import env as machine_env
from app.runtime import shell


@pytest.mark.parametrize("platform", [Platform.WIN, Platform.MAC])
def test_script_selection_excludes_shell_on_windows(monkeypatch, platform):
    monkeypatch.setattr(machine_env, "PLATFORM", platform)
    names = ["setup.py", "setup.ps1", "setup.sh", "setup.win.sh", "_helper.py", "setup.txt"]
    scripts = [Path(name) for name in names]
    expected = scripts[:2] if platform == Platform.WIN else scripts[:3]
    assert machine_loader._resolve_scripts(scripts) == expected


def test_scripts_preserve_order_and_stop_on_first_failure(tmp_path: Path) -> None:
    marker = tmp_path / "runs.txt"
    scripts = [tmp_path / name for name in ("setup.py", "init_failed.py", "last.py")]
    for script in scripts:
        script.write_text(
            "import os, sys\n"
            "with open(os.environ['SCRIPT_MARKER'], 'a') as marker:\n"
            f"    marker.write({script.name!r} + '\\n')\n"
            f"sys.exit({7 if script.name == 'init_failed.py' else 0})\n"
        )

    with pytest.raises(subprocess.CalledProcessError) as failure:
        machine_scripts.run_scripts(scripts, env={"SCRIPT_MARKER": str(marker)}, dry_run=False)

    assert failure.value.returncode == 7
    assert marker.read_text().splitlines() == ["setup.py", "init_failed.py"]


def test_scripts_run_each_time_with_spaced_paths(tmp_path: Path) -> None:
    directory = tmp_path / "script directory"
    directory.mkdir()
    marker = tmp_path / "runs.txt"
    scripts = [directory / name for name in ("once_setup.py", "watch_setup.py")]
    for script in scripts:
        script.write_text(
            "import os\n"
            "with open(os.environ['SCRIPT_MARKER'], 'a') as marker:\n"
            f"    marker.write({script.name!r} + '\\n')\n"
        )

    for _ in range(2):
        machine_scripts.run_scripts(
            scripts,
            env={"SCRIPT_MARKER": str(marker)},
            dry_run=False,
        )

    assert marker.read_text().splitlines() == [script.name for script in scripts] * 2


def test_script_preview_does_not_prepare_execute_or_repair_scripts(tmp_path, monkeypatch):
    scripts = [tmp_path / name for name in ("setup.py", "init_preview.sh", "setup.ps1")]
    for script in scripts:
        script.write_text("must not execute\n")
        script.chmod(0o600)
    modes = [script.stat().st_mode for script in scripts]
    monkeypatch.setattr(
        shell, "process_env", lambda *a: pytest.fail("preview prepared environment")
    )
    monkeypatch.setattr(
        shell.shutil, "which", lambda *a, **kw: pytest.fail("preview resolved an interpreter")
    )
    monkeypatch.setattr(
        shell.subprocess, "run", lambda *a, **kw: pytest.fail("preview executed a script")
    )

    machine_scripts.run_scripts(scripts, env={}, dry_run=True)

    assert [script.stat().st_mode for script in scripts] == modes


@pytest.mark.skipif(sys.platform == "win32", reason="Unix executable permissions")
def test_script_execution_does_not_repair_permissions(tmp_path):
    script = tmp_path / "not-executable.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o600)
    with pytest.raises(PermissionError):
        machine_scripts.run_scripts([script], env={}, dry_run=False)
    assert script.stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="Unix script execution")
def test_unix_scripts_use_declared_shebang_and_environment(tmp_path, monkeypatch):
    activation = tmp_path / "environment.sh"
    activation.write_text("")
    monkeypatch.setattr(shell, "_ENVIRONMENT_SCRIPT", activation)
    selected_path = "/selected/bin"
    environment = {
        "HOME": str(tmp_path),
        "MC_ID": "selected",
        "MC_VALUE": "private",
        "PATH": selected_path,
    }

    # The OS executes the declared shebang; the runner does not reinterpret it.
    script = tmp_path / "inspect script.sh"
    result = tmp_path / "result.txt"
    script.write_text(
        '#!/bin/sh -e\nprintf "%s\\n" "$MC_ID|$MC_VALUE|$PATH" > "$RESULT"\nfalse\nexit 0\n'
    )
    script.chmod(0o755)
    with pytest.raises(subprocess.CalledProcessError) as failure:
        machine_scripts.run_scripts(
            [script], env={**environment, "RESULT": str(result)}, dry_run=False
        )
    assert failure.value.returncode == 1
    assert result.read_text().strip() == f"selected|private|{selected_path}"
