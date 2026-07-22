import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "scripts" / "setup_professional_media.py"


def load_setup_module():
    spec = importlib.util.spec_from_file_location("setup_professional_media", SETUP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SETUP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeSetupTest(unittest.TestCase):
    def test_runtime_plan_is_pinned_and_never_contains_secrets(self):
        setup = load_setup_module()

        plan = setup.build_install_plan(
            Path("C:/runtime"), with_comfyui=True, with_musetalk=False
        )
        serialized = json.dumps(plan, sort_keys=True)

        self.assertIn("hyperframes@0.7.68", serialized)
        self.assertIn(
            "f6d30bce9a862d56d9184dd65341621a8905ea3e", serialized
        )
        self.assertIn(
            "7d679837b018bfeb28eca55734b335efcd0e7100", serialized
        )
        self.assertNotIn("HF_TOKEN", serialized)
        self.assertNotIn("apiKey", serialized)


if __name__ == "__main__":
    unittest.main()
