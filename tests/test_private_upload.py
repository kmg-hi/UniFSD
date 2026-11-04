import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from publication import ROOT, DATASETS, deposit_base, write_csv, write_json
from private_upload import payload_sources, restore_training_labels
from package_private_upload import create_part, partition, verify_part
from upload_private_assets import verify_asset


class PrivateUploadTests(unittest.TestCase):
    def setUp(self):
        root = ROOT / ".local/test-tmp"
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def entry(self, name, content):
        path = self.root / name
        path.write_bytes(content)
        return {"archive_path": "public optical/" + name, "source_path": str(path),
                "bytes": len(content), "expected_sha256": hashlib.sha256(content).hexdigest()}

    def test_partition_retains_every_member_and_bounds_parts(self):
        entries = [self.entry(str(n) + ".txt", b"frozen") for n in range(5)]
        parts = partition(entries, limit=17000)
        self.assertEqual([e for part in parts for e in part], entries)
        self.assertTrue(all(len(part) <= 2 for part in parts))

    def test_metadata_base_supports_preparation_and_repository_layouts(self):
        self.assertEqual(deposit_base(self.root), self.root)
        (self.root / "data_deposit").mkdir()
        self.assertEqual(deposit_base(self.root), self.root / "data_deposit")

    def test_single_oversized_member_rejected(self):
        with self.assertRaisesRegex(ValueError, "single member"):
            partition([self.entry("a", b"frozen")], limit=10)

    def test_zip_content_extracts_byte_identically_under_requested_root(self):
        entries = [self.entry("a.jpg", b"fixture not an actual image"), self.entry("negative.txt", b"")]
        output = self.root / "part.zip"
        create_part(output, entries)
        verify_part(output, entries)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("public optical/negative.txt"), b"")
            self.assertEqual(len(archive.namelist()), 2)

    def test_wrong_source_hash_cannot_produce_final_part(self):
        entry = self.entry("a", b"frozen")
        entry["expected_sha256"] = "0" * 64
        output = self.root / "part.zip"
        with self.assertRaisesRegex(ValueError, "Source checksum"):
            create_part(output, [entry])
        self.assertFalse(output.exists())
        self.assertTrue(output.with_suffix(".zip.partial").exists())

    def test_existing_partial_is_preserved(self):
        output = self.root / "part.zip"
        partial = output.with_suffix(".zip.partial")
        partial.write_bytes(b"previous incomplete archive")
        with self.assertRaisesRegex(ValueError, "Unfinished"):
            create_part(output, [self.entry("a", b"frozen")])
        self.assertEqual(partial.read_bytes(), b"previous incomplete archive")

    def test_archive_extra_member_rejected(self):
        entry = self.entry("a", b"frozen")
        output = self.root / "part.zip"
        create_part(output, [entry])
        with zipfile.ZipFile(output, "a") as archive:
            archive.writestr("unexpected.txt", b"not allowed")
        with self.assertRaisesRegex(ValueError, "membership"):
            verify_part(output, [entry])

    def test_catalog_uses_only_manifest_members_not_entire_source_tree(self):
        source, preview = self.root / "source", self.root / "preview"
        (source / "images/test").mkdir(parents=True)
        (source / "labels/test").mkdir(parents=True)
        (source / "extra-private.txt").write_text("must not be included")
        row = {"record_id": "POU000001", "image_path": "images/test/a.jpg", "image_sha256": "a" * 64,
               "label_path": "labels/test/a.txt", "label_sha256": "b" * 64}
        write_csv(preview / "metadata/manifest.csv", list(row), [row])
        entries = list(payload_sources(DATASETS[0], preview, {"public_optical_root": str(source)}))
        self.assertEqual([e["relative_path"] for e in entries], [row["image_path"], row["label_path"]])

    def test_catalog_rejects_escape(self):
        row = {"record_id": "POU000001", "image_path": "../secret", "image_sha256": "a" * 64,
               "label_path": "labels/test/a.txt", "label_sha256": "b" * 64}
        write_csv(self.root / "metadata/manifest.csv", list(row), [row])
        with self.assertRaises(ValueError):
            list(payload_sources(DATASETS[0], self.root, {"public_optical_root": str(self.root)}))

    def test_remote_asset_requires_exact_digest_size_and_state(self):
        item = {"name": "part.zip", "bytes": 12, "sha256": "a" * 64}
        correct = {"name": "part.zip", "size": 12, "state": "uploaded", "digest": "sha256:" + "a" * 64}
        verify_asset(correct, item)
        for changes in ({"digest": None}, {"digest": "sha256:" + "b" * 64}, {"size": 11}, {"state": "starter"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                verify_asset({**correct, **changes}, item)

    def test_restoration_copies_existing_label_bytes_without_recomputing_boxes(self):
        raw = b"0 0.500000 0.500000 0.200000 0.200000\n"
        digest = hashlib.sha256(raw).hexdigest()
        pin = "a" * 64
        plan = {"datasets": {DATASETS[1]: {"directory": "paired_RGBT", "expected_samples": 1,
                                         "source_manifest_sha256": pin}}}
        write_json(self.root / "metadata/release_plan.json", plan)
        row = {"sample_id": "real:exp/a", "split": "train", "domain": "real",
               "training_optic_label_path": "labels/optic/real/exp/a.txt",
               "training_thermal_label_path": "labels/thermal/real/exp/a.txt"}
        write_csv(self.root / "data_deposit/paired_RGBT/metadata/manifest.csv", list(row), [row])
        artifact = self.root / "artifact.json"
        value = {"source_manifest_sha256": pin, "records": [{"id": row["sample_id"], "split": "train",
                 "domain": "real", "label": raw.decode(), "label_sha256": digest}]}
        write_json(artifact, value)
        with patch("private_upload.ROOT", self.root):
            restore_training_labels(artifact, self.root / "restored")
        for field in ("training_optic_label_path", "training_thermal_label_path"):
            self.assertEqual((self.root / "restored" / row[field]).read_bytes(), raw)
        value["records"][0]["label"] = "changed"
        write_json(artifact, value)
        with patch("private_upload.ROOT", self.root), self.assertRaisesRegex(ValueError, "original hash"):
            restore_training_labels(artifact, self.root / "rejected")


if __name__ == "__main__":
    unittest.main()
