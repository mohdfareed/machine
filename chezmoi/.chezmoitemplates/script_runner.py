#!/usr/bin/env python3
"""
Script runner template - symlinks a config file, allowing machine override.

Usage:
  template "script_runner.py" (dict "ctx" . "script"  "pkgs.py" "data" .pkgs)

Args:
  ctx: the template context (pass .)
  script: the script to run
  data: the data to pass to the script
"""

import os
import subprocess
import sys
from pathlib import Path

# scripts
script = Path("{{ .ctx.scriptsPath }}") / "{{ .script }}"
script_data = """
{{ .data | toJson }}
"""

# environment
env = os.environ.copy()
env["CHEZMOI_DATA"] = script_data

env["MACHINE"] = "{{ .ctx.machinePath }}"
env["MACHINE_ID"] = "{{ .ctx.machine }}"
env["MACHINE_PRIVATE"] = "{{ .ctx.privatePath }}"

env["MACHINE_SHARED"] = "{{ .ctx.configPath }}"
env["MACHINE_CONFIG"] = "{{ .ctx.machineConfigPath }}"

try:  # run script
    script = env["MACHINE"] / script
    result = subprocess.run(
        f"{sys.executable} {script}", shell=True, env=env, check=False
    )
    sys.exit(result.returncode)

except KeyboardInterrupt:
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"script error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)
