#!/usr/bin/env python3
"""
Script runner template - symlinks a config file, allowing machine override.

Usage:
template "script_runner.py" (dict "ctx" . "script"  "packages" "data" .packages)

Args:
  ctx: the template context (pass .)
  cfg: the relative path from the config root
"""

import os
import subprocess
import sys
from pathlib import Path

# scripts
scripts_dir = Path("{{ .ctx.scriptsPath }}")
script = scripts_dir / "{{ .script }}"
script_data = """
{{ .data | toJson }}
"""

# environment
env = os.environ.copy()
env["CHEZMOI_DATA"] = script_data

try:  # run script
    r = subprocess.run([sys.executable, str(script)], env=env, check=False)
    sys.exit(r.returncode)

except KeyboardInterrupt:
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"script error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)
