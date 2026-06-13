from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed\n{result.stdout}\n{result.stderr}")


def main() -> None:
    package_root = Path(__file__).resolve().parents[1]
    work_dir = Path(tempfile.mkdtemp(prefix="cloptima-llm-py-install-"))
    env = {**os.environ, "PIP_CACHE_DIR": str(work_dir / "pip-cache")}
    ingest_url = "https://sdk-ingest.example.cloptima.ai/sdk/events"
    try:
        package_copy = work_dir / "package"
        shutil.copytree(package_root / "cloptima_llm_observability", package_copy / "cloptima_llm_observability")
        shutil.copytree(package_root / "examples", package_copy / "examples")
        shutil.copy2(package_root / "pyproject.toml", package_copy / "pyproject.toml")
        shutil.copy2(package_root / "README.md", package_copy / "README.md")
        shutil.copy2(package_root / "LICENSE", package_copy / "LICENSE")

        venv_dir = work_dir / "venv"
        run([sys.executable, "-m", "venv", str(venv_dir)], work_dir, env)
        python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", str(package_copy)], work_dir, env)
        run([
            str(python),
            "-c",
            "from importlib.metadata import metadata, version; "
            "from cloptima_llm_observability import init_from_env; "
            "assert version('cloptima-llm-observability') == '0.1.0'; "
            "assert metadata('cloptima-llm-observability')['Name'] == 'cloptima-llm-observability'; "
            "client = init_from_env(env={"
            f"'CLOPTIMA_LLM_OBSERVABILITY_INGEST_URL':'{ingest_url}', "
            "'CLOPTIMA_LLM_OBSERVABILITY_API_KEY':'pat-test', "
            "'CLOPTIMA_LLM_OBSERVABILITY_APP_ID':'agent-api', "
            "'CLOPTIMA_LLM_OBSERVABILITY_ENVIRONMENT':'dev'}); "
            "assert client.stats().queued_events == 0",
        ], work_dir, env)
        for example in sorted((package_copy / "examples").glob("*.py")):
            run([str(python), str(example)], work_dir, env)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
