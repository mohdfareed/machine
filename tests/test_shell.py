"""Commands preserve arguments, terminal output, previews, and failures."""

import json
import os
import shutil
import subprocess
import sys

import pytest
from app.runtime import shell


@pytest.fixture(autouse=True)
def isolated_activation(tmp_path, monkeypatch):
    monkeypatch.setattr(shell, "ROOT", tmp_path)
    activation = tmp_path / "environment.sh"
    activation.write_text("")
    monkeypatch.setattr(shell, "_ENVIRONMENT_SCRIPT", activation)


def test_argument_lists_preserve_paths_values_and_environment(tmp_path, monkeypatch):
    script = tmp_path / "script with spaces.py"
    script.write_text(
        """import json, os, sys
print(json.dumps([sys.argv[1:], os.environ['MC_TEST_VALUE'], os.environ.get('MC_PARENT_ONLY')]))
"""
    )
    arguments = ["two words", 'a"quote', "it's quoted", "$value; literal", ""]
    environment = {"MC_TEST_VALUE": "custom value"}
    monkeypatch.setenv("MC_PARENT_ONLY", "inherited value")
    result = shell.run(
        [sys.executable, str(script), *arguments],
        env=environment,
        dry_run=False,
        capture_output=True,
        check=True,
    )
    assert result is not None
    assert json.loads(result.stdout) == [arguments, "custom value", "inherited value"]


def test_default_execution_inherits_output(capfd):
    result = shell.run(
        [
            sys.executable,
            "-c",
            "import sys; print('direct output'); print('direct error', file=sys.stderr)",
        ],
        env=dict(os.environ),
        dry_run=False,
    )
    output = capfd.readouterr()
    assert result is not None
    assert result.stdout is None
    assert "direct output" in output.out.splitlines()
    assert "direct error" in output.err.splitlines()


def test_preview_does_not_execute_command(tmp_path, monkeypatch):
    monkeypatch.setattr(
        shell, "process_env", lambda *a: pytest.fail("preview prepared environment")
    )
    target = tmp_path / "must not exist"
    result = shell.run(
        [
            sys.executable,
            "-c",
            "import pathlib, sys; pathlib.Path(sys.argv[1]).touch()",
            str(target),
        ],
        env=dict(os.environ),
        dry_run=True,
        capture_output=True,
        check=True,
    )
    assert result is None
    assert not target.exists()


def test_checked_execution_raises_after_command_failure():
    command = [sys.executable, "-c", "import sys; sys.exit(7)"]
    result = shell.run(command, env=dict(os.environ), dry_run=False)
    assert result is not None
    assert result.returncode == 7
    with pytest.raises(subprocess.CalledProcessError) as failure:
        shell.run(command, env=dict(os.environ), dry_run=False, check=True)
    assert failure.value.returncode == 7
    assert failure.value.cmd == command

    command = [sys.executable, "-c", "import sys; sys.stderr.write('failure details'); sys.exit(7)"]
    with pytest.raises(RuntimeError, match="failure details"):
        shell.run(command, env=dict(os.environ), dry_run=False, capture_output=True, check=True)
    with pytest.raises(RuntimeError, match="failure details"):
        shell.query(command, env=dict(os.environ))
    result = shell.query(command, env=dict(os.environ), check=False)
    assert result.returncode == 7
    assert result.stderr == "failure details"


@pytest.mark.skipif(sys.platform == "win32", reason="Unix shell expansion")
def test_unix_string_commands_use_shell():
    result = shell.run(
        'printf "%s" "$MC_TEST_VALUE"',
        env={**os.environ, "MC_TEST_VALUE": "expanded value"},
        dry_run=False,
        capture_output=True,
    )
    assert result is not None
    assert result.stdout == b"expanded value"


def test_captured_output_is_not_replayed(capfd):
    result = shell.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('raw-output\\n')"],
        env=dict(os.environ),
        dry_run=False,
        capture_output=True,
    )
    assert result is not None
    assert result.stdout == f"raw-output{os.linesep}".encode()
    assert "raw-output" not in capfd.readouterr().out.splitlines()


def test_query_is_quiet_and_uses_the_supplied_path(capfd):
    environment = {
        "PATH": os.path.dirname(sys.executable),
        "QUERY_VALUE": "selected",
    }
    result = shell.query(
        [os.path.basename(sys.executable), "-c", "import os; print(os.environ['QUERY_VALUE'])"],
        env=environment,
    )
    assert result.stdout.strip() == "selected"
    assert capfd.readouterr() == ("", "")


@pytest.mark.parametrize("windows,resolved", [(False, None), (True, None), (True, sys.executable)])
def test_commands_resolve_only_on_windows_without_preflight(monkeypatch, windows, resolved):
    environment = {"PATH": "refreshed-path"}
    command = ["query-tool", "two words", ""]
    monkeypatch.setattr(shell, "is_windows", windows)
    monkeypatch.setattr(shell, "process_env", lambda overrides: environment)

    def which(name, *, path):
        assert windows, "POSIX execution must use subprocess PATH lookup"
        assert name == command[0]
        assert path == environment["PATH"]
        return resolved

    def run(args, **kwargs):
        assert args == [resolved or command[0], *command[1:]]
        assert kwargs["env"] is environment
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(shell.shutil, "which", which)
    monkeypatch.setattr(shell.subprocess, "run", run)
    shell.query(command, env={})
    shell.run(command, env={}, dry_run=False)
    assert command == ["query-tool", "two words", ""]


def test_missing_commands_raise_native_file_not_found(tmp_path):
    command = [str(tmp_path / "missing-command")]
    with pytest.raises(FileNotFoundError) as failure:
        shell.query(command, env={})
    assert failure.value.errno is not None
    with pytest.raises(FileNotFoundError) as failure:
        shell.run(command, env={}, dry_run=False)
    assert failure.value.errno is not None


def test_git_context_cannot_redirect_queries_or_change_another_index(tmp_path, monkeypatch):
    if not shutil.which("git"):
        pytest.skip("Git is unavailable")

    # Create two disposable repositories before introducing a foreign Git context.
    for name in tuple(os.environ):
        if name.upper().startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    outer, inner = tmp_path / "outer", tmp_path / "inner"
    for repo in (outer, inner):
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "config", "remote.origin.url", repo.name], check=True
        )
        (repo / "keep.txt").write_text(repo.name)
        subprocess.run(["git", "-C", str(repo), "add", "keep.txt"], check=True)
    index = outer / ".git" / "index"
    original_index = index.read_bytes()

    # Match a terminal launched by a diff tool, including an explicit index override.
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outer))
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", "must-not-run")
    monkeypatch.setenv("GIT_DIFFTOOL_NO_PROMPT", "true")
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    overrides = {"GIT_INDEX_FILE": str(index)}
    command = ["git", "-C", str(inner), "config", "--get", "remote.origin.url"]
    assert subprocess.check_output(command, text=True).strip() == "outer"
    assert shell.query(command, env=overrides).stdout.strip() == "inner"

    # Stage only the requested repository, preserving both caller state and authentication.
    (inner / "keep.txt").write_text("updated")
    shell.run(
        ["git", "-C", str(inner), "add", "keep.txt"], env=overrides, dry_run=False, check=True
    )
    assert index.read_bytes() == original_index
    assert (
        shell.query(["git", "-C", str(inner), "show", ":keep.txt"], env=overrides).stdout
        == "updated"
    )
    prepared = shell.process_env(overrides)
    assert prepared["GIT_SSH_COMMAND"] == "ssh -o BatchMode=yes"
    assert prepared["GIT_CONFIG_GLOBAL"] == os.devnull
    assert "GIT_EXTERNAL_DIFF" not in prepared and "GIT_DIFFTOOL_NO_PROMPT" not in prepared
    assert os.environ["GIT_DIR"] == str(outer / ".git")
    assert overrides == {"GIT_INDEX_FILE": str(index)}


@pytest.mark.skipif(sys.platform == "win32", reason="Unix command activation")
def test_activation_applies_to_new_commands_without_profiles(tmp_path, monkeypatch):
    configuration = shell._ENVIRONMENT_SCRIPT
    configuration.write_text(
        'export PATH="$HOME/tools:$PATH"\n'
        'export MC_ID="activation cannot select a machine"\n'
        '[ ! -f "$HOME/installed.env" ] || . "$HOME/installed.env"\n'
    )
    profile_marker = tmp_path / "profile-ran"
    for name in (".profile", ".bashrc", ".bash_profile", ".zshrc", ".zshenv"):
        (tmp_path / name).write_text(f'touch "{profile_marker}"\n')
    overrides = {
        "HOME": str(tmp_path),
        "MC_ID": "selected",
        "LITERAL": "\n".join(("first", "second=value")),
    }
    monkeypatch.delenv("INSTALLED_VALUE", raising=False)
    assert shell.find_executable("new-command", env=overrides) is None

    # Stand in for an installer that creates a command and persists activation values.
    installer = tmp_path / "install.py"
    installer.write_text(
        r"""import os
from pathlib import Path
home = Path(os.environ['HOME'])
(home / 'tools').mkdir()
command = home / 'tools' / 'new-command'
command.write_text('#!/bin/sh\n' 'printf "%s" "$INSTALLED_VALUE|$MC_ID|$LITERAL"\n')
command.chmod(0o755)
(home / 'installed.env').write_text('export INSTALLED_VALUE=installed\n')
"""
    )
    shell.run([sys.executable, str(installer)], env=overrides, dry_run=False, check=True)

    # Each lookup, query and execution sees installation changes and selected overrides.
    assert shell.find_executable("new-command", env=overrides) == str(
        tmp_path / "tools/new-command"
    )
    result = shell.query(["new-command"], env=overrides)
    assert result.stdout == f"installed|selected|{overrides['LITERAL']}"
    executed = shell.run(["new-command"], env=overrides, dry_run=False, capture_output=True)
    assert executed is not None and executed.stdout.decode() == result.stdout
    assert not profile_marker.exists()
    assert "INSTALLED_VALUE" not in os.environ
    assert "PATH" not in overrides


@pytest.mark.skipif(sys.platform == "win32", reason="Unix command activation")
def test_activation_failure_stops_before_execution(tmp_path, monkeypatch):
    configuration = shell._ENVIRONMENT_SCRIPT
    configuration.write_text(
        """printf 'activation failed' >&2
return 7
"""
    )
    with pytest.raises(RuntimeError, match="activation failed"):
        shell.query([sys.executable, "-c", "raise AssertionError('must not run')"], env={})

    def blocked(*args, **kwargs):
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(shell.subprocess, "run", blocked)
    with pytest.raises(subprocess.TimeoutExpired):
        shell.process_env({})


def test_windows_overrides_use_registered_values_without_activation(monkeypatch):
    monkeypatch.setattr(shell, "is_windows", True)
    overrides = {"Path": "selected", "MC_ID": "selected"}

    def system_env(values):
        assert values is overrides
        return {
            "PATH": "selected",
            "SDK_ROOT": "new",
            "MC_ID": "selected",
            "Git_Dir": "foreign-repository",
            "git_difftool_no_prompt": "true",
        }

    monkeypatch.setattr(shell, "system_env", system_env)
    monkeypatch.setattr(
        shell.subprocess, "run", lambda *a, **kw: pytest.fail("Windows ran a profile")
    )

    assert shell.process_env(overrides) == {
        "PATH": "selected",
        "SDK_ROOT": "new",
        "MC_ID": "selected",
    }


@pytest.mark.parametrize("windows", [False, True])
@pytest.mark.parametrize("module_path", [None, "existing-modules"])
def test_powershell_files_prepare_once_and_preserve_module_path(monkeypatch, windows, module_path):
    monkeypatch.setattr(shell, "is_windows", windows)
    environment = {"PATH": "installed-path"}
    if module_path is not None:
        environment["PSModulePath"] = module_path
    prepared = []
    commands = []
    interpreter = "powershell.exe" if windows else "pwsh-preview"

    def process_env(overrides):
        prepared.append(overrides)
        return environment

    def which(name, *, path):
        assert path == "installed-path"
        return f"/tools/{interpreter}" if name == interpreter else None

    def run(command, **kwargs):
        assert kwargs["env"] is environment
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(shell, "process_env", process_env)
    monkeypatch.setattr(shell.shutil, "which", which)
    monkeypatch.setattr(shell.subprocess, "run", run)
    shell.run(["script with spaces.ps1", "two words"], env={}, dry_run=False, powershell=True)

    assert prepared == [{}]
    assert commands == [
        [
            f"/tools/{interpreter}",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "script with spaces.ps1",
            "two words",
        ]
    ]
    assert environment.get("PSModulePath") == module_path


@pytest.fixture
def powershell(monkeypatch):
    executable = (
        shutil.which("pwsh.exe")
        or shutil.which("powershell.exe")
        or shutil.which("pwsh")
        or shutil.which("pwsh-preview")
    )
    if executable is None:
        pytest.skip("PowerShell is unavailable")
    monkeypatch.setattr(shell, "is_windows", True)
    monkeypatch.setattr(shell.shutil, "which", lambda *args, **kwargs: executable)


@pytest.mark.parametrize(
    "command,expected,code",
    [
        (
            '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\SteamInputBridge"; '
            "Write-Output $env:STEAM_INPUT_BRIDGE_REPO",
            r"C:\Dev Projects\SteamInputBridge",
            0,
        ),
        ('Write-Output "quoted value" | ForEach-Object { "[$_]" }', "[quoted value]", 0),
        (
            "Write-Host 'host output'; Write-Warning 'warning output'; "
            "Write-Progress -Activity 'probe' -Status 'probe'",
            "warning output",
            0,
        ),
        ('Write-Host "before error"; throw "example failure"', "example failure", 1),
        (
            "\"throw 'repository already exists'\" | Invoke-Expression",
            "repository already exists",
            1,
        ),
    ],
)
def test_windows_commands_preserve_source_and_failure(command, expected, code, powershell):
    result = shell.run(
        command,
        env={**os.environ, "DEV": r"C:\Dev Projects"},
        dry_run=False,
        capture_output=True,
    )
    assert result is not None
    output = result.stdout
    assert b"CLIXML" not in output
    assert b"CategoryInfo" not in output
    assert b"FullyQualifiedErrorId" not in output
    assert b"At line:" not in output
    assert result.returncode == code
    assert expected in output.decode(errors="replace")


def test_windows_native_command_failures_propagate(powershell):
    executable = sys.executable.replace("'", "''")
    result = shell.run(
        f"& '{executable}' -c 'import sys; print(123); sys.exit(7)'",
        env=dict(os.environ),
        dry_run=False,
        capture_output=True,
    )
    assert result is not None
    assert result.returncode == 7
    assert result.stdout.strip() == b"123"
