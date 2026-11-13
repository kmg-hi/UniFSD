"""Keep manuscript previews, links and published metric units consistent."""

import csv
import hashlib
import json
import re
import struct
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures/manuscript_v2"


class DocumentationTests(unittest.TestCase):
    def test_current_figures_are_complete_and_hash_pinned(self):
        manifest = json.loads((FIGURES / "figure_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([f["number"] for f in manifest["figures"]], list(range(1, 11)))
        self.assertRegex(manifest["source_manuscript_sha256"], r"^[0-9a-f]{64}$")
        for figure in manifest["figures"]:
            with self.subTest(figure=figure["number"]):
                data = (FIGURES / figure["path"]).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), (figure["width"], figure["height"]))
                self.assertEqual(hashlib.sha256(data).hexdigest(), figure["png_sha256"])
                self.assertTrue(figure["rgb_pixels_unchanged"])

    def test_documentation_relative_links_resolve(self):
        documents = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
        documents += list((ROOT / "docs").glob("*.md"))
        documents += list((ROOT / "figures").rglob("README.md"))
        for document in documents:
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                path = unquote(target.split("#", 1)[0].split("?", 1)[0].strip("<>"))
                with self.subTest(document=str(document.relative_to(ROOT)), target=path):
                    self.assertTrue((document.parent / path).resolve().exists())

    def test_table5_is_nine_rows_with_fraction_units(self):
        with (FIGURES / "table5_test_metrics.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 9)
        self.assertEqual(sum(r["record"] == "public_optical_release_v1" for r in rows), 4)
        self.assertEqual(sum(r["record"] == "paired_rgbt_v1" for r in rows), 5)
        for row in rows:
            self.assertEqual(int(row["test_samples"]), 9374 if row["record"] == "public_optical_release_v1" else 3524)
            for field in ("precision", "recall", "map50", "map50_95"):
                self.assertGreaterEqual(float(row[field]), 0)
                self.assertLessEqual(float(row[field]), 1)
            self.assertLessEqual(float(row["map50_95"]), float(row["map50"]))
        dams = next(r for r in rows if r["model"] == "DAMSDet R50-vd")
        self.assertEqual((dams["precision"], dams["recall"]), ("0.8058", "0.9676"))

    def test_schematic_path_discrepancy_is_explicit(self):
        readme = (FIGURES / "README.md").read_text(encoding="utf-8")
        self.assertIn("`public_optical/`", readme)
        self.assertIn("`public optical/`", readme)
        self.assertIn("`paired_RGBT/`", readme)


if __name__ == "__main__":
    unittest.main()
