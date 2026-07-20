from __future__ import annotations

import argparse
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import print_final_results_table
import run_experiment


def test_final_results_table_reports_canonical_archive_totals() -> None:
    data = print_final_results_table._load_results(
        ROOT / "results/final_validated_results.json"
    )

    markdown, passed = print_final_results_table.build_tables(data)

    assert passed
    assert "| Full Senior benchmark | 12 instances total | 10000.48 | 126 |" in markdown
    assert "| Headline | Small | 162.44 | 2 |" in markdown
    assert "| Headline | Medium | 371.35 | 5 |" in markdown
    assert "| Headline | Large | 1163.35 | 15 |" in markdown


def test_run_experiment_creates_output_directory_and_reports_pairs(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[list[str]] = []
    report_pairs: list[str] = []

    def fake_run(command, cwd=None, text=None, stdout=None, stderr=None, env=None, check=False):
        calls.append([str(part) for part in command])
        output_index = command.index("--output") + 1
        output_path = ROOT / command[output_index]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('{"vehicleBlockList": []}\n', encoding="utf-8")
        if stdout is not None:
            stdout.write("fake solver completed\n")
        return SimpleNamespace(returncode=0)

    def fake_report(pairs: list[str], validator: Path) -> None:
        report_pairs.extend(pairs)

    monkeypatch.setattr(run_experiment.subprocess, "run", fake_run)
    monkeypatch.setattr(run_experiment, "run_report", fake_report)

    output_dir = tmp_path / "generated"
    args = argparse.Namespace(
        algorithm="greedy",
        scope="sml",
        only="Small",
        quick=True,
        output_dir=output_dir,
        processed_dir=None,
        input_dir=Path("data/raw/minoa/senior"),
        validator=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )

    run_experiment.run_sml(args)

    output_file = output_dir / "Small_Output_greedy.json"
    assert output_file.exists()
    assert (output_dir / "Small_greedy.log").exists()
    assert calls
    assert any("scripts/minoa_solver.py" in part for part in calls[0])
    assert report_pairs == [
        f"data/raw/minoa/senior/Small_Input_S.json:{output_file}"
    ]
