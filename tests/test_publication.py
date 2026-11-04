import csv
import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from publication import (ROOT, DATASETS, REQUIRED_BLOCKERS, check_expected,
                         contained_file, deposit_root, make_checksums, publication_blockers,
                         read_json, read_schema, safe_relative, sanitize_registration,
                         sha256, summarise_manifest, validate_row, verify_checksums,
                         verify_payload, write_csv, write_json, write_rights_review_queue)
from prepare_metadata import export_paired
from package_deposit import main as package_main
from validate_release import validate_scaffold


def public_row(**changes):
    row = {"record_id": "POU000001", "split": "test", "image_path": "images/test/a.jpg",
           "label_path": "labels/test/a.txt", "source_dataset": "FASDD_CV", "source_record_id": "a.jpg",
           "width": "640", "height": "480", "file_size_bytes": "10", "image_sha256": "a" * 64,
           "classes": "fire", "box_count": "1", "is_negative": "false", "split_group_id": "g1",
           "dedup_stage": "retained", "license_id": "CC-BY-SA-4.0", "label_sha256": "b" * 64}
    return {**row, **changes}


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp_root = ROOT / ".local/test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="publication-test-", dir=temp_root)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, rows):
        path = self.root / "metadata/manifest.csv"
        write_csv(path, list(read_schema(DATASETS[0])["properties"]), rows)
        return path

    def test_scaffold_complete(self):
        self.assertEqual(validate_scaffold()["scaffold"], "PASS")

    def test_release_display_names_preserve_record_identifiers(self):
        records = (
            ("public_optical_release_v1", "unified single-modal optical dataset",
             "zenodo-public-optical.json.template", "public_optical.md"),
            ("paired_rgbt_v1", "multi-modal optical\u2013thermal paired dataset",
             "zenodo-paired-rgbt.json.template", "paired_rgbt.md"),
        )
        self.assertEqual(DATASETS, tuple(record[0] for record in records))
        plan = read_json(ROOT / "metadata/release_plan.json")
        for identifier, title, template, card in records:
            with self.subTest(dataset=identifier):
                self.assertEqual(plan["datasets"][identifier]["title"], title)
                self.assertEqual(read_json(ROOT / "templates" / template)["title"], title)
                card_text = (ROOT / "dataset_cards" / card).read_text(encoding="utf-8")
                self.assertEqual(card_text.splitlines()[0], "# " + title)
                self.assertIn(f"`{identifier}`", card_text)
                self.assertIn(title, (ROOT / "GITHUB_README_DRAFT.md").read_text(encoding="utf-8"))

    def test_safe_path(self):
        self.assertEqual(safe_relative("images/test/a.jpg"), "images/test/a.jpg")

    def test_release_root_names_are_distinct_from_record_ids(self):
        plan = read_json(ROOT / "metadata/release_plan.json")
        for dataset, directory in zip(DATASETS, ("public optical", "paired_RGBT")):
            with self.subTest(dataset=dataset):
                self.assertEqual(deposit_root(self.root, dataset, plan), self.root / directory)
                card = "public_optical.md" if dataset == DATASETS[0] else "paired_rgbt.md"
                self.assertIn(f"`{directory}/`", (ROOT / "dataset_cards" / card).read_text(encoding="utf-8"))

    def test_release_root_rejects_nested_or_unsafe_names(self):
        for directory in ("nested/folder", "../outside", "/absolute", "C:/outside", "a\\b", "a\nb", ""):
            plan = {"datasets": {DATASETS[0]: {"directory": directory}}}
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                deposit_root(self.root, DATASETS[0], plan)

    def test_metadata_preview_keeps_requested_top_level_folders(self):
        plan = read_json(ROOT / "metadata/release_plan.json")
        write_json(self.root / "metadata/release_plan.json", plan)
        for dataset in DATASETS:
            base = deposit_root(self.root / "data_deposit", dataset, plan)
            write_json(base / "metadata/classes.json", {"0": "fire", "1": "smoke"})
            (base / "README.md").write_text("Incomplete test fixture\n", encoding="utf-8")
            make_checksums(base)
            with patch("package_deposit.ROOT", self.root), patch.object(
                    sys, "argv", ["package_deposit.py", dataset, "--metadata-only"]), contextlib.redirect_stdout(io.StringIO()):
                package_main()
            output = self.root / "archives" / (dataset + "-INCOMPLETE-METADATA-PREVIEW.zip")
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {
                    "INCOMPLETE_NOT_FOR_DATA_PUBLICATION.txt", base.name + "/README.md",
                    base.name + "/metadata/classes.json", base.name + "/SHA256SUMS_METADATA.txt"})

    def test_reject_unsafe_paths(self):
        for value in ("../secret", "/absolute", "//server/file", "C:/secret", "a\\b", "a/../b", "./a", "a//b", "a\nb", "a:b", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_relative(value)

    def test_symlink_escape_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        base = self.root / "base"
        base.mkdir()
        try:
            (base / "linked").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        with self.assertRaises(ValueError):
            contained_file(base, "linked/a.txt")

    def test_registration_redacts_only_private_path(self):
        source = {"calibration_source": {"path": "PRIVATE", "schema_version": 1}, "matrix": [[1, 0], [0, 1]]}
        output = sanitize_registration(source)
        self.assertNotIn("path", output["calibration_source"])
        self.assertEqual(output["matrix"], source["matrix"])
        self.assertEqual(source["calibration_source"]["path"], "PRIVATE")

    def test_unrecognised_registration_path_fails_closed(self):
        with self.assertRaises(ValueError):
            sanitize_registration({"unexpected": "/home/private/file"})

    def test_valid_manifest_summary(self):
        result = summarise_manifest(self.manifest([public_row()]), DATASETS[0])
        self.assertEqual(result["samples"], 1)
        self.assertEqual(result["boxes_from_manifest"], 1)
        self.assertFalse(result["payload_files_verified_now"])

    def test_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate sample"):
            summarise_manifest(self.manifest([public_row(), public_row()]), DATASETS[0])

    def test_group_split_overlap_rejected(self):
        second = public_row(record_id="POU2", split="train", image_path="images/train/b.jpg", image_sha256="c" * 64)
        with self.assertRaisesRegex(ValueError, "crosses splits"):
            summarise_manifest(self.manifest([public_row(), second]), DATASETS[0])

    def test_exact_hash_split_overlap_rejected(self):
        second = public_row(record_id="POU2", split="train", split_group_id="g2", image_path="images/train/b.jpg")
        with self.assertRaisesRegex(ValueError, "hash crosses splits"):
            summarise_manifest(self.manifest([public_row(), second]), DATASETS[0])

    def test_duplicate_media_path_rejected(self):
        second = public_row(record_id="POU2", split_group_id="g2", image_sha256="c" * 64)
        with self.assertRaisesRegex(ValueError, "media path"):
            summarise_manifest(self.manifest([public_row(), second]), DATASETS[0])

    def test_negative_inconsistency_rejected(self):
        with self.assertRaisesRegex(ValueError, "inconsistency"):
            summarise_manifest(self.manifest([public_row(is_negative="true")]), DATASETS[0])

    def test_bad_hash_rejected(self):
        with self.assertRaises(ValueError):
            validate_row(public_row(image_sha256="not-a-hash"), read_schema(DATASETS[0]))

    def test_extra_private_field_rejected(self):
        with self.assertRaises(ValueError):
            validate_row(public_row(private_input="hidden"), read_schema(DATASETS[0]))

    def test_absolute_source_identifier_rejected(self):
        with self.assertRaises(ValueError):
            validate_row(public_row(source_record_id="/home/private/a.jpg"), read_schema(DATASETS[0]))

    def test_expected_count_mismatch_rejected(self):
        result = summarise_manifest(self.manifest([public_row()]), DATASETS[0])
        expected = {"expected_samples": 2, "expected_splits": {"test": 1}, "expected_groups": 1,
                    "expected_sources": {"FASDD_CV": 1}, "expected_negative_images": 0, "expected_boxes": {"fire": 1}}
        with self.assertRaisesRegex(ValueError, "sample count"):
            check_expected(result, expected)

    def test_metadata_checksum_tampering(self):
        self.manifest([public_row()])
        make_checksums(self.root)
        verify_checksums(self.root)
        write_json(self.root / "metadata/new.json", {"added": True})
        with self.assertRaisesRegex(ValueError, "incomplete"):
            verify_checksums(self.root)

    def test_metadata_checksum_modified_bytes(self):
        path = self.manifest([public_row()])
        make_checksums(self.root)
        path.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_checksums(self.root)

    def test_payload_missing_then_verified_then_tampered(self):
        image, label = self.root / "images/test/a.jpg", self.root / "labels/test/a.txt"
        image.parent.mkdir(parents=True)
        label.parent.mkdir(parents=True)
        image.write_bytes(b"synthetic fixture bytes, not a real image")
        label.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        row = public_row(image_sha256=sha256(image), label_sha256=sha256(label))
        self.manifest([row])
        self.assertEqual(verify_payload(self.root, DATASETS[0]), 2)
        label.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed payload"):
            verify_payload(self.root, DATASETS[0])

    def test_missing_payload_rejected(self):
        self.manifest([public_row()])
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            verify_payload(self.root, DATASETS[0])

    def paired_fixture(self):
        source, output = self.root / "source", self.root / "output"
        source.mkdir()
        row = {"id": "synthetic:sample", "domain": "synthetic", "experiment": "exp", "stem": "sample",
               "split": "test", "image_sizes": {"optic": [1280, 720], "thermal_registered": [1280, 720]},
               "release_optic_path": "dataset/synthetic/exp/pair_optic/sample.png",
               "release_thermal_path": "dataset/synthetic/exp/pair_thermal/sample.png",
               "release_label_path": "dataset/synthetic/exp/pair_label/sample.txt",
               "optic_sha256": "a" * 64, "thermal_sha256": "b" * 64, "label_sha256": "c" * 64,
               "fire_boxes": 1, "smoke_boxes": 2, "label_basis": "optic",
               "private_path": "PRIVATE_SOURCE_PATH_NOT_EXPORTED"}
        (source / "pairs.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        for name in ("registration_config.json", "split_summary.json", "validation.json"):
            write_json(source / name, {})
        return source, output

    def test_paired_source_and_derived_gt_not_conflated(self):
        source, output = self.paired_fixture()
        export_paired(source, output, sha256(source / "pairs.jsonl"))
        with (output / "metadata/manifest.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["source_label_sha256"], "c" * 64)
        self.assertEqual(row["training_label_sha256"], "")
        self.assertNotEqual(row["source_label_path"], row["training_optic_label_path"])
        self.assertNotIn("PRIVATE_SOURCE", json.dumps(row))
        with self.assertRaisesRegex(ValueError, "Missing or changed payload"):
            verify_payload(output, DATASETS[1])

    def test_frozen_paired_manifest_pin_enforced(self):
        source, output = self.paired_fixture()
        with self.assertRaisesRegex(ValueError, "Frozen paired"):
            export_paired(source, output, "0" * 64)
        self.assertFalse(output.exists())

    def test_publication_is_blocked_in_draft(self):
        plan = read_json(ROOT / "metadata/release_plan.json")
        status = read_json(ROOT / "metadata/publication_status.json")
        issues = publication_blockers(plan, status, [])
        self.assertIn("source_rights", issues)
        self.assertTrue(any("sign-off" in issue for issue in issues))

    def test_cannot_remove_required_review_categories(self):
        plan = read_json(ROOT / "metadata/release_plan.json")
        status = {"publication_ready": True, "reviewed_by": "fixture", "reviewed_at": "fixture", "blockers": []}
        self.assertTrue(any("categories" in issue for issue in publication_blockers(plan, status, [])))

    def test_templates_do_not_invent_creators(self):
        for path in (ROOT / "templates").glob("zenodo-*.json.template"):
            data = read_json(path)
            self.assertEqual(data["creators"], [])
            self.assertIsNone(data["license"])

    def test_text_false_does_not_count_as_review_approval(self):
        plan = read_json(ROOT / "metadata/release_plan.json")
        status = {"publication_ready": "false", "reviewed_by": "fixture", "reviewed_at": "fixture",
                  "blockers": [{"id": key, "resolved": "false", "evidence": "fixture"} for key in REQUIRED_BLOCKERS]}
        issues = publication_blockers(plan, status, [])
        self.assertIn("source_rights", issues)
        self.assertTrue(any("sign-off" in issue for issue in issues))

    def test_rights_queue_does_not_clear_unflagged_images(self):
        rows = [public_row(source_dataset="D-Fire", source_record_id="PublicDataset_example.jpg"),
                public_row(record_id="POU2", image_path="images/test/b.jpg")]
        self.manifest(rows)
        write_rights_review_queue(self.root)
        with (self.root / "metadata/rights_review_queue.csv").open(encoding="utf-8", newline="") as stream:
            queue = list(csv.DictReader(stream))
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["clearance"], "PENDING")

    def test_required_derived_hash_not_copied_from_source(self):
        source, output = self.paired_fixture()
        export_paired(source, output, sha256(source / "pairs.jsonl"))
        from publication import payload_entries
        with (output / "metadata/manifest.csv").open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        entries = payload_entries(row, DATASETS[1])
        self.assertEqual(entries[-1][1], "")
        self.assertEqual(entries[-2][1], "")


if __name__ == "__main__":
    unittest.main()
