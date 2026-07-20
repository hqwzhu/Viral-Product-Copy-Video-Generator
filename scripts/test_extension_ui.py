import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "browser-extension"


class ExtensionUiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (EXTENSION / "popup.html").read_text(encoding="utf-8")
        cls.js = (EXTENSION / "popup.js").read_text(encoding="utf-8")
        cls.css = (EXTENSION / "popup.css").read_text(encoding="utf-8")
        cls.manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))

    def test_guide_markup_has_accessible_views_and_tabs(self):
        for element_id in (
            "openGuide",
            "openWorkspace",
            "guideView",
            "guideBack",
            "guideTabs",
            "guideFeatures",
            "guideUsage",
            "guideSubscription",
        ):
            self.assertRegex(self.html, rf'id=["\']{element_id}["\']')
        self.assertRegex(self.html, r'id=["\']guideTabs["\'][^>]*role=["\']tablist["\']')
        self.assertRegex(self.html, r'role=["\']tab["\']')
        self.assertRegex(self.html, r'aria-selected=["\'](?:true|false)["\']')
        self.assertRegex(self.html, r'aria-controls=["\']guide(?:Features|Usage|Subscription)["\']')

    def test_new_translation_keys_exist_in_both_dictionaries(self):
        en = self._dictionary_body("EN_TRANSLATIONS")
        zh = self._dictionary_body("ZH_TRANSLATIONS")
        keys = set(re.findall(r'^\s{2}([A-Za-z][A-Za-z0-9]*)\s*:', en, re.MULTILINE))
        new_keys = {
            key
            for key in keys
            if key.startswith("guide")
            or key in {"openGuide", "openWorkspace", "guideBack", "workspacePlaceholder"}
        }
        self.assertTrue(new_keys, "expected guide/workspace translation keys")
        for key in new_keys:
            self.assertRegex(zh, rf'\n  {re.escape(key)}\s*:', msg=key)

    def test_manifest_permissions_are_minimal(self):
        self.assertEqual(self.manifest["permissions"], ["activeTab", "storage", "clipboardWrite"])

    def test_plan_values_match_product_contract(self):
        for key, credits, price in (("starter", 60, 19), ("growth", 220, 59), ("scale", 800, 199)):
            self.assertRegex(self.js, rf'{key}:\s*\{{[^}}]*credits:\s*{credits}[^}}]*priceCny:\s*{price}')

    def _dictionary_body(self, name):
        match = re.search(rf'const {name} = Object\.freeze\(\{{(?P<body>.*?)\}}\);', self.js, re.DOTALL)
        self.assertIsNotNone(match, name)
        return match.group("body")


if __name__ == "__main__":
    unittest.main()
