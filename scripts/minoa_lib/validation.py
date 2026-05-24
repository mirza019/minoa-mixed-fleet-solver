from __future__ import annotations

import subprocess
from pathlib import Path


def validate(
    validator: Path,
    input_path: Path,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["java", "-jar", str(validator), str(input_path), str(output_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

