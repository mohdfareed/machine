#!/usr/bin/env python3
"""
Script runner template - symlinks a config file, allowing machine override.

Usage:
  template "script_runner.py" (dict "ctx" . "script" "scripts.py" "argv" list "data" dict)

Args:
  ctx: the template context (pass .)
  script: the script to run
  argv: the arguments to pass to the script
  data: the data to pass to the script
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# scripts and args
script = Path("{{ .ctx.scriptsPath }}") / "{{ .script }}"
argv_data = """
{{- .argv | toJson -}}
"""
script_data = """
{{ .data | toJson }}
"""

try:  # parse argv
    argv = json.loads(argv_data) if argv_data.strip() else []
except json.JSONDecodeError as e:
    raise ValueError(f"invalid argv: {e}") from e

# environment
env = os.environ.copy()
env["CHEZMOI_DATA"] = script_data

env["MACHINE"] = "{{ .ctx.machinePath }}"
env["MACHINE_ID"] = "{{ .ctx.machine }}"
env["MACHINE_PRIVATE"] = "{{ .ctx.privatePath }}"

env["MACHINE_SHARED"] = "{{ .ctx.configPath }}"
env["MACHINE_CONFIG"] = "{{ .ctx.machineConfigPath }}"

try:  # run script
    script = Path(env["MACHINE"]) / script
    cmd = [sys.executable, str(script)] + list(argv)
    result = subprocess.run(cmd, shell=False, env=env, check=False)
    sys.exit(result.returncode)

except KeyboardInterrupt:
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"script error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)
