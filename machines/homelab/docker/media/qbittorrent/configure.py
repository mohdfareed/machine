import os
import stat
import sys
from pathlib import Path


def upsert_section(lines, section, settings):
    header = f"[{section}]"
    try:
        start = lines.index(header)
    except ValueError:
        if lines and lines[-1]:
            lines.append("")
        lines.append(header)
        lines.extend(f"{key}={value}" for key, value in settings.items())
        return

    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("[")),
        len(lines),
    )
    managed = set(settings)
    found = set()
    body = []

    for line in lines[start + 1 : end]:
        key = line.split("=", 1)[0]
        if key not in managed:
            body.append(line)
        elif key not in found:
            body.append(f"{key}={settings[key]}")
            found.add(key)

    body.extend(f"{key}={value}" for key, value in settings.items() if key not in found)
    lines[start + 1 : end] = body


path = Path(sys.argv[1])
server_domain = sys.argv[2]
original = path.read_text(encoding="utf-8") if path.exists() else ""
newline = "\r\n" if "\r\n" in original else "\n"
lines = original.splitlines()

if not lines:
    lines = [
        "[BitTorrent]",
        "Session\\Port=6881",
        "",
        "[Meta]",
        "MigrationVersion=9999",
        "",
    ]

upsert_section(
    lines,
    "BitTorrent",
    {
        r"Session\DefaultSavePath": "/data/downloads",
        r"Session\TempPath": "/data/downloads/temp",
        r"Session\TempPathEnabled": "true",
    },
)
upsert_section(
    lines,
    "Preferences",
    {
        r"WebUI\Address": "127.0.0.1",
        r"WebUI\AlternativeUIEnabled": "true",
        r"WebUI\ClickjackingProtection": "true",
        r"WebUI\CSRFProtection": "true",
        r"WebUI\HostHeaderValidation": "true",
        r"WebUI\LocalHostAuth": "false",
        r"WebUI\RootFolder": "/vuetorrent",
        r"WebUI\ServerDomains": server_domain,
    },
)

rendered = newline.join(lines) + newline
if rendered != original:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    if path.exists():
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
    temporary.replace(path)
