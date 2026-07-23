import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DirectScriptImportTest(unittest.TestCase):
    def test_public_runners_reach_argparse_when_started_by_file_path(self) -> None:
        runners = (
            "run_promotion_workflow.py",
            "promotion_cycle_runner.py",
            "product_batch_runner.py",
            "final_capability_runner.py",
            "skill_entry.py",
        )
        for runner in runners:
            with self.subTest(runner=runner):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "scripts" / runner),
                        "--definitely-invalid",
                    ],
                    capture_output=True,
                    cwd=REPO_ROOT,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("usage:", result.stderr)
                self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
