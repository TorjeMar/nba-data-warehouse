"""Project source package."""

from __future__ import annotations

import os
from pathlib import Path


def _load_project_env_file() -> None:
	"""Load key=value pairs from the repo .env file into process env."""
	env_path = Path(__file__).resolve().parents[1] / ".env"
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue

		key, value = line.split("=", 1)
		key = key.removeprefix("export ").strip()
		value = value.strip()

		if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
			value = value[1:-1]

		if key and key not in os.environ:
			os.environ[key] = value


_load_project_env_file()
