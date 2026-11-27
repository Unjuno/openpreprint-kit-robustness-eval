"""Regression tests for the fixed robustness-evaluation evidence."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
ANALYZERS = (
    ROOT / "analysis/analyze_robustness.py",
    ROOT / "manuscripts/openpreprint-kit-robustness-eval/analysis/analyze_robustness.py",
    ROOT / "manuscripts/openpreprint-kit-robustness-eval/v1/analysis/analyze_robustness.py",
)
DATA = ROOT / "manuscripts/openpreprint-kit-robustness-eval/v1/data"


class RobustnessEvidenceTests(unittest.TestCase):
    def test_v2_release_manifest_declares_every_staged_public_research_file(self):
        v2 = ROOT / "manuscripts/openpreprint-kit-robustness-eval/v2"
        config = yaml.safe_load((v2 / "research-assets.yaml").read_text(encoding="utf-8"))
        declared = {asset["path"] for asset in config["public_assets"]}
        expected = set()
        for area in ("data", "analysis"):
            for source in (ROOT / area, v2 / area):
                if source.exists():
                    expected.update(f"{area}/{path.name}" for path in source.iterdir() if path.is_file())
        expected.update(
            f"supplements/{path.name}"
            for path in (v2 / "supplements").iterdir()
            if path.is_file()
        )
        self.assertEqual(expected, declared)

    def test_results_must_match_the_pre_fixed_spec_commit(self):
        for source_analyzer in ANALYZERS:
            with self.subTest(analyzer=source_analyzer.relative_to(ROOT).as_posix()):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    analysis_dir = root / "analysis"
                    data_dir = root / "data"
                    analysis_dir.mkdir()
                    data_dir.mkdir()
                    analyzer = analysis_dir / "analyze_robustness.py"
                    shutil.copy2(source_analyzer, analyzer)
                    for name in ("negative-suite-spec.json", "negative-suite-results.json", "negative-suite-summary.json"):
                        shutil.copy2(DATA / name, data_dir / name)

                    valid = subprocess.run(
                        [sys.executable, str(analyzer)], capture_output=True, text=True, check=False
                    )
                    self.assertEqual(valid.returncode, 0, valid.stderr)

                    results_path = data_dir / "negative-suite-results.json"
                    results = json.loads(results_path.read_text(encoding="utf-8"))
                    results["toolkit_main"] = "0" * 40
                    results_path.write_text(json.dumps(results), encoding="utf-8")

                    mismatched = subprocess.run(
                        [sys.executable, str(analyzer)], capture_output=True, text=True, check=False
                    )
                    self.assertEqual(mismatched.returncode, 1)
                    self.assertIn("toolkit_main does not match", mismatched.stderr)

    def test_all_reported_outcomes_and_counts_must_match_judgment_rows(self):
        mutations = (
            ("negative-suite-results.json", lambda data: data["results"][0].update(expected="ACCEPTED")),
            ("negative-suite-results.json", lambda data: data["results"][0].update(verdict="FAIL")),
            ("negative-suite-results.json", lambda data: data.update(fails=99, total=1)),
            ("negative-suite-summary.json", lambda data: data.update(total_judgments=1, passes=1)),
            (
                "negative-suite-summary.json",
                lambda data: data["by_case"]["1"][0].update(verdict="FAIL", rejected=False),
            ),
        )
        for source_analyzer in ANALYZERS:
            for filename, mutate in mutations:
                with self.subTest(analyzer=source_analyzer.relative_to(ROOT).as_posix(), file=filename):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        root = Path(temp_dir)
                        analysis_dir = root / "analysis"
                        data_dir = root / "data"
                        analysis_dir.mkdir()
                        data_dir.mkdir()
                        analyzer = analysis_dir / "analyze_robustness.py"
                        shutil.copy2(source_analyzer, analyzer)
                        for name in (
                            "negative-suite-spec.json",
                            "negative-suite-results.json",
                            "negative-suite-summary.json",
                        ):
                            shutil.copy2(DATA / name, data_dir / name)

                        target = data_dir / filename
                        changed = json.loads(target.read_text(encoding="utf-8"))
                        mutate(changed)
                        target.write_text(json.dumps(changed), encoding="utf-8")

                        rejected = subprocess.run(
                            [sys.executable, str(analyzer)], capture_output=True, text=True, check=False
                        )
                        self.assertEqual(rejected.returncode, 1)


if __name__ == "__main__":
    unittest.main()
