"""Create local-only demo credentials and run the complete Docker lab."""

from __future__ import annotations

import os
import secrets
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = {"MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "POSTGRES_PASSWORD"}


def ensure_local_env(path: Path) -> bool:
    if path.exists():
        settings = dict(
            line.split("=", 1)
            for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        )
        if any("replace-with" in value for value in settings.values()):
            raise ValueError(".env still contains example passwords; replace or remove it")
        if not REQUIRED_KEYS.issubset(settings) or any(not settings[key] for key in REQUIRED_KEYS):
            raise ValueError(".env must define three nonempty database passwords")
        return False
    values = {
        "MYSQL_PASSWORD": secrets.token_urlsafe(24),
        "MYSQL_ROOT_PASSWORD": secrets.token_urlsafe(24),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")
    return True


def main() -> None:
    created = ensure_local_env(PROJECT_ROOT / ".env")
    if created:
        print("Created ignored .env with random local demo passwords", flush=True)
    try:
        subprocess.run(
            ["docker", "compose", "run", "--build", "--rm", "runner", "sh", "scripts/run_demo.sh"],
            cwd=PROJECT_ROOT,
            check=True,
        )
    except FileNotFoundError:
        raise SystemExit("Docker Compose was not found; install and start Docker") from None
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None


if __name__ == "__main__":
    main()
