import json
import re
import subprocess
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

    def test_workspace_tab_rejection_uses_safe_fallback(self):
        body = self._function_body("openWorkspace")
        self.assertRegex(body, r'await\s+chrome\.tabs\.create\(')
        self.assertRegex(body, re.compile(r'catch\s*\([^)]*\)\s*\{.*openWorkspaceFallback\(', re.DOTALL))
        self.assertRegex(self.js, r'openWorkspace\(\)\.catch\(')

        script = f"""
const calls = [];
let createCalls = 0;
global.window = {{
  location: {{ href: "chrome-extension://test/popup.html?view=guide&source=test" }},
  open: (...args) => calls.push(args)
}};
global.chrome = {{
  tabs: {{
    create: async () => {{
      createCalls += 1;
      throw new Error("tabs unavailable");
    }}
  }}
}};
{self._function_source("openWorkspace")}
{self._function_source("openWorkspaceFallback")}
(async () => {{
  await openWorkspace();
  process.stdout.write(JSON.stringify({{ createCalls, calls }}));
}})().catch((error) => {{
  console.error(error.stack);
  process.exit(1);
}});
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed["createCalls"], 1)
        self.assertEqual(
            observed["calls"],
            [["chrome-extension://test/popup.html?view=workspace", "_blank", "noopener,noreferrer"]],
        )

    def test_each_subscription_plan_has_audience_and_included_usage(self):
        en = self._dictionary_body("EN_TRANSLATIONS")
        zh = self._dictionary_body("ZH_TRANSLATIONS")
        for plan in ("Free", "Starter", "Growth", "Scale"):
            audience = f"guidePlan{plan}Audience"
            included = f"guidePlan{plan}Included"
            for dictionary, hosted_term in ((en, "hosted"), (zh, "托管")):
                self.assertRegex(dictionary, rf'\n  {audience}:\s*"[^"\n]+"')
                included_match = re.search(rf'\n  {included}:\s*"(?P<text>[^"\n]*\{{credits\}}[^"\n]*)"', dictionary)
                self.assertIsNotNone(included_match, included)
                self.assertIn(hosted_term, included_match.group("text").lower())
            self.assertRegex(
                self.js,
                rf'{plan.lower()}:\s*\{{[^}}]*audience:\s*"{audience}"[^}}]*included:\s*"{included}"',
            )
        self.assertIn("Object.entries(PLANS)", self.js)
        self.assertIn('t(details.included, { credits: plan.credits })', self.js)

    def _dictionary_body(self, name):
        match = re.search(rf'const {name} = Object\.freeze\(\{{(?P<body>.*?)\}}\);', self.js, re.DOTALL)
        self.assertIsNotNone(match, name)
        return match.group("body")

    def _function_body(self, name):
        match = re.search(rf'(?:async\s+)?function {name}\([^)]*\) \{{(?P<body>.*?)\n\}}\n\nfunction', self.js, re.DOTALL)
        self.assertIsNotNone(match, name)
        return match.group("body")

    def _function_source(self, name):
        match = re.search(
            rf'(?P<source>(?:async\s+)?function {name}\([^)]*\) \{{.*?\n\}})(?=\n\nfunction)',
            self.js,
            re.DOTALL,
        )
        self.assertIsNotNone(match, name)
        return match.group("source")


if __name__ == "__main__":
    unittest.main()
