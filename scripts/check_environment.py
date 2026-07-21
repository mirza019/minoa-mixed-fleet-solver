#!/usr/bin/env python3
"""Check that the MINOA runtime environment is ready."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import shutil
import subprocess
import sys


MIN_PYTHON = (3, 9)
PACKAGE_IMPORTS = {
    "networkx": "networkx",
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "pandas": "pandas",
    "pillow": "PIL",
    "python-docx": "docx",
    "scipy": "scipy",
    "pytest": "pytest",
}
VALIDATOR = Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar")
SENIOR_INPUT_DIR = Path("data/raw/minoa/senior")
REQUIRED_INPUTS = [
    "Small_Input_S.json",
    "Medium_Input_S.json",
    "Large_Input_S.json",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Python packages and MINOA runtime files.")
    parser.add_argument("--require-java", action="store_true", help="Fail if Java is not available.")
    parser.add_argument("--require-validator", action="store_true", help="Fail if the validator JAR is missing.")
    parser.add_argument("--require-data", action="store_true", help="Fail if required raw Senior inputs are missing.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    errors: list[str] = []

    if sys.version_info < MIN_PYTHON:
        errors.append(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required; "
            f"current version is {sys.version.split()[0]}."
        )

    missing_packages = []
    for package_name, import_name in PACKAGE_IMPORTS.items():
        try:
            importlib.import_module(import_name)
        except Exception as exc:  # pragma: no cover - message path only
            missing_packages.append(f"{package_name} ({exc.__class__.__name__}: {exc})")
    if missing_packages:
        errors.append(
            "Missing or broken Python packages:\n  - " + "\n  - ".join(missing_packages)
        )

    java_path = shutil.which("java")
    if args.require_java and not java_path:
        errors.append("Java was not found on PATH. Java is required for the MINOA validator.")
    elif java_path:
        try:
            subprocess.run([java_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception as exc:  # pragma: no cover - message path only
            errors.append(f"Java was found but could not be executed: {exc}")

    if args.require_validator and not VALIDATOR.exists():
        errors.append(f"MINOA desktop validator JAR is missing: {VALIDATOR}")

    if args.require_data:
        missing_inputs = [name for name in REQUIRED_INPUTS if not (SENIOR_INPUT_DIR / name).exists()]
        if missing_inputs:
            errors.append(
                f"Required raw Senior inputs are missing under {SENIOR_INPUT_DIR}:\n  - "
                + "\n  - ".join(missing_inputs)
            )

    if errors:
        raise SystemExit("Environment check failed:\n\n" + "\n\n".join(errors))

    print("Environment check passed.")
    print(f"Python: {sys.version.split()[0]}")
    print("Python packages: ok")
    if args.require_java:
        print("Java: ok")
    if args.require_validator:
        print(f"Validator: {VALIDATOR}")
    if args.require_data:
        print(f"Raw Senior inputs: {SENIOR_INPUT_DIR}")


if __name__ == "__main__":
    main()
