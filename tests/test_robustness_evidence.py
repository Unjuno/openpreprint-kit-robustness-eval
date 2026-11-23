"""Regression tests for the fixed robustness-evaluation evidence."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANALYZERS = (
    ROOT / "analysis/analyze_robustness.py",
    ROOT / "manuscripts/openpreprint-kit-robustness-eval/analysis/analyze_robustness.py",
    ROOT / "manuscripts/openpreprint-kit-robustness-eval/v1/analysis/analyze_robustness.py",
)
DATA = ROOT / "manuscripts/openpreprint-kit-robustness-eval/v1/data"


class RobustnessEvidenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
