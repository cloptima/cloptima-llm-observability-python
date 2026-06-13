from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path


class PackagingSmokeTests(unittest.TestCase):
    def test_builds_wheel_and_imports_from_clean_venv(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="cloptima-llm-observability-py-") as temp_dir:
            build_root = Path(temp_dir) / "package"
            shutil.copytree(package_root, build_root)
            wheelhouse = Path(temp_dir) / "wheelhouse"
            wheelhouse.mkdir(parents=True, exist_ok=True)
            build_venv = Path(temp_dir) / "build-venv"
            venv.EnvBuilder(with_pip=True).create(build_venv)
            build_python = build_venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            if not build_python.exists():
                self.fail(f"python executable missing in build venv: {build_python}")

            subprocess.run(
                [str(build_python), "-m", "pip", "install", "--upgrade", "pip", "build"],
                check=True,
                capture_output=True,
                text=True,
            )

            subprocess.run(
                [str(build_python), "-m", "build", "--wheel", "--outdir", str(wheelhouse)],
                cwd=build_root,
                check=True,
                capture_output=True,
                text=True,
            )

            wheels = list(wheelhouse.glob("cloptima_llm_observability-*.whl"))
            self.assertEqual(len(wheels), 1, f"expected one wheel, found {wheels}")

            venv_dir = Path(temp_dir) / "venv"
            venv.EnvBuilder(with_pip=True).create(venv_dir)
            python_bin = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            if not python_bin.exists():
                self.fail(f"python executable missing in venv: {python_bin}")

            subprocess.run(
                [str(python_bin), "-m", "pip", "install", "--no-deps", str(wheels[0])],
                check=True,
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    str(python_bin),
                    "-c",
                    "from cloptima_llm_observability import CloptimaLLMObservability; print(CloptimaLLMObservability.__name__)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.strip(), "CloptimaLLMObservability")

            extras = subprocess.run(
                [
                    str(python_bin),
                    "-c",
                    "from importlib.metadata import metadata; print('|'.join(sorted(metadata('cloptima-llm-observability').get_all('Provides-Extra') or [])))",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(extras.stdout.strip(), "httpx")

    def test_examples_run_from_clean_install(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="cloptima-llm-observability-py-examples-") as temp_dir:
            build_root = Path(temp_dir) / "package"
            shutil.copytree(package_root, build_root)

            venv_dir = Path(temp_dir) / "venv"
            venv.EnvBuilder(with_pip=True).create(venv_dir)
            python_bin = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            if not python_bin.exists():
                self.fail(f"python executable missing in venv: {python_bin}")

            subprocess.run(
                [str(python_bin), "-m", "pip", "install", "."],
                cwd=build_root,
                check=True,
                capture_output=True,
                text=True,
            )

            for example in sorted((build_root / "examples").glob("*.py")):
                subprocess.run(
                    [str(python_bin), str(example)],
                    cwd=build_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )


if __name__ == "__main__":
    unittest.main()
