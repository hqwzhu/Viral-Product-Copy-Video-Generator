import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "browser-extension"


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, _tag, attrs):
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids.append(element_id)


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

    def test_workspace_markup_groups_primary_and_secondary_content_with_unique_ids(self):
        self.assertRegex(self.html, r'<body[^>]*data-layout=["\']popup["\'][^>]*data-view=["\']main["\']')
        self.assertRegex(self.html, r'class=["\'][^"\']*workspace-grid[^"\']*["\']')
        self.assertRegex(self.html, r'class=["\'][^"\']*workspace-primary[^"\']*["\']')
        self.assertRegex(self.html, r'class=["\'][^"\']*workspace-secondary[^"\']*["\']')

        collector = _IdCollector()
        collector.feed(self.html)
        duplicates = sorted({element_id for element_id in collector.ids if collector.ids.count(element_id) > 1})
        self.assertEqual(duplicates, [])

    def test_workspace_styles_define_desktop_tablet_mobile_and_reduced_motion_contracts(self):
        self.assertRegex(
            self.css,
            re.compile(
                r'body\[data-layout=["\']workspace["\']\]\s*\{[^}]*width:\s*100%[^}]*min-width:\s*320px[^}]*max-width:\s*none',
                re.DOTALL,
            ),
        )
        self.assertRegex(
            self.css,
            re.compile(
                r'body\[data-layout=["\']workspace["\']\]\s+\.workspace-grid\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1\.15fr\)\s+minmax\(300px,\s*\.85fr\)[^}]*gap:\s*16px',
                re.DOTALL,
            ),
        )
        self.assertRegex(self.css, r'@media\s*\([^)]*max-width:\s*900px[^)]*\)')
        self.assertRegex(self.css, r'@media\s*\([^)]*max-width:\s*520px[^)]*\)')
        self.assertRegex(self.css, r'@media\s*\(prefers-reduced-motion:\s*reduce\)')

    def test_hidden_guide_panels_are_not_overridden_by_component_display_rules(self):
        self.assertRegex(
            self.css,
            re.compile(r'\[hidden\]\s*\{[^}]*display:\s*none\s*!important', re.DOTALL),
        )

    def test_workspace_query_initializes_main_layout_and_guide_round_trip_preserves_it(self):
        script = f"""
const els = {{
  mainView: {{ hidden: false }},
  guideView: {{ hidden: true }},
  guideFeatures: {{ hidden: false }},
  guideUsage: {{ hidden: true }},
  guideSubscription: {{ hidden: true }}
}};
global.document = {{
  body: {{ dataset: {{}} }},
  querySelector: () => null,
  querySelectorAll: () => []
}};
{self._function_source("setLayout")}
{self._function_source("initializeViewState")}
{self._function_source("setView")}
{self._function_source("setGuideTab")}

initializeViewState("?view=workspace");
const workspace = {{
  layout: document.body.dataset.layout,
  view: document.body.dataset.view,
  mainHidden: els.mainView.hidden,
  guideHidden: els.guideView.hidden
}};
setView("guide");
const guide = {{ layout: document.body.dataset.layout, view: document.body.dataset.view }};
setView("main");
const returned = {{ layout: document.body.dataset.layout, view: document.body.dataset.view }};
initializeViewState("");
const popup = {{ layout: document.body.dataset.layout, view: document.body.dataset.view }};
process.stdout.write(JSON.stringify({{ workspace, guide, returned, popup }}));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(
            observed["workspace"],
            {"layout": "workspace", "view": "main", "mainHidden": False, "guideHidden": True},
        )
        self.assertEqual(observed["guide"], {"layout": "workspace", "view": "guide"})
        self.assertEqual(observed["returned"], {"layout": "workspace", "view": "main"})
        self.assertEqual(observed["popup"], {"layout": "popup", "view": "main"})

    def test_actual_page_initializes_guide_without_working_chrome_storage(self):
        page_url = f"{(EXTENSION / 'popup.html').resolve().as_uri()}?view=workspace"
        script = f"""
const {{ chromium }} = require("playwright");
const pageUrl = {json.dumps(page_url)};

async function inspectPage(browser, storageMode) {{
  const context = await browser.newContext({{ locale: "en-US", viewport: {{ width: 720, height: 900 }} }});
  const page = await context.newPage();
  if (storageMode === "reject") {{
    await page.addInitScript(() => {{
      window.chrome = window.chrome || {{}};
      window.chrome.storage = {{
        local: {{
          get: async () => {{ throw new Error("storage get rejected"); }},
          set: async () => {{ throw new Error("storage set rejected"); }}
        }}
      }};
    }});
  }}
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(pageUrl, {{ waitUntil: "load" }});
  await page.waitForTimeout(50);

  const guide = await page.evaluate(() => ({{
    featureCards: document.querySelectorAll("#guideFeatureList .guide-card").length,
    advancedDisclosures: document.querySelectorAll("#guideFeatureList .guide-disclosure").length,
    usageItems: document.querySelectorAll("#guideUsageList .guide-usage-item").length,
    planRows: document.querySelectorAll("#guidePlans .plan-row").length,
    planNames: Array.from(document.querySelectorAll("#guidePlans .plan-row-summary strong"), (node) => node.textContent)
  }}));

  await page.click("#openGuide");
  const visiblePanels = {{}};
  for (const tabName of ["features", "usage", "subscription"]) {{
    await page.click(`[data-guide-tab="${{tabName}}"]`);
    visiblePanels[tabName] = await page.$$eval(
      "[role=tabpanel]",
      (panels) => panels.filter((panel) => !panel.hidden).map((panel) => panel.id)
    );
  }}
  await page.click("#guideBack");

  await page.click("#languageZh");
  await page.click("#saveLicense");
  await page.evaluate(() => {{ document.getElementById("commandOutput").value = "test command"; }});
  await page.click("#copyCommand");
  await page.click("#useTab");
  await page.waitForTimeout(50);

  const state = await page.evaluate(() => ({{
    layout: document.body.dataset.layout,
    view: document.body.dataset.view,
    mainHidden: document.getElementById("mainView").hidden,
    guideHidden: document.getElementById("guideView").hidden
  }}));
  await context.close();
  return {{ storageMode, pageErrors, guide, visiblePanels, state }};
}}

(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  try {{
    const results = [];
    for (const storageMode of ["missing", "reject"]) {{
      results.push(await inspectPage(browser, storageMode));
    }}
    process.stdout.write(JSON.stringify(results));
  }} finally {{
    await browser.close();
  }}
}})().catch((error) => {{
  console.error(error.stack);
  process.exit(1);
}});
"""
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for observed in json.loads(result.stdout):
            with self.subTest(storage_mode=observed["storageMode"]):
                self.assertEqual(observed["pageErrors"], [])
                self.assertEqual(
                    observed["guide"],
                    {
                        "featureCards": 8,
                        "advancedDisclosures": 1,
                        "usageItems": 8,
                        "planRows": 4,
                        "planNames": ["Free", "Starter", "Growth", "Scale"],
                    },
                )
                self.assertEqual(observed["visiblePanels"]["features"], ["guideFeatures"])
                self.assertEqual(observed["visiblePanels"]["usage"], ["guideUsage"])
                self.assertEqual(observed["visiblePanels"]["subscription"], ["guideSubscription"])
                self.assertEqual(
                    observed["state"],
                    {"layout": "workspace", "view": "main", "mainHidden": False, "guideHidden": True},
                )

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
