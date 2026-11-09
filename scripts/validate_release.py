"""Validate a local draft, exported metadata, or complete publication package."""

import argparse
import csv
import json
from pathlib import Path

from publication import (ROOT, DATASETS, SPLITS, PRIVATE_PATTERN, check_expected,
                         csv_rows, deposit_base, deposit_root, metadata_files, publication_blockers, read_json,
                         sha256, summarise_manifest, verify_checksums, verify_payload)


def validate_scaffold(root=ROOT):
    required = ["README.md", "PREPUBLICATION_CHECKLIST.md", ".gitignore", "LICENSES/README.md",
                "docs/scientific_data_policy_review.md", "docs/data_dictionary.md",
                "docs/reproduction_and_release.md", "docs/repository_and_deposit_layout.md",
                "docs/methods_and_validation.md", "docs/rights_ethics_and_assets.md",
                "manuscript/data_descriptor_outline.md", "manuscript/data_availability.template.md",
                "manuscript/code_availability.template.md", "metadata/source_rights_review.csv",
                "metadata/publication_status.json", "metadata/release_plan.json",
                "templates/CITATION.cff.template", "templates/zenodo-software.json.template",
                "templates/zenodo-public-optical.json.template", "templates/zenodo-paired-rgbt.json.template"]
    for dataset in DATASETS:
        required.append("schemas/" + dataset + ".schema.json")
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise ValueError(f"Missing scaffold files: {missing}")
    ignored = (root / ".gitignore").read_text(encoding="utf-8")
    if "/.local/" not in ignored or "/data_deposit/" not in ignored:
        raise ValueError("Private/bulk output exclusions missing")
    plan = read_json(root / "metadata/release_plan.json")
    record_folders = {deposit_root(root, dataset, plan).name for dataset in DATASETS}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if rel.parts[0] in {".local", "data_deposit", "archives", ".git", *record_folders} or "__pycache__" in rel.parts:
            continue
        if path.is_file() and path.suffix in (".md", ".json", ".csv", ".template"):
            if path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError(f"Unexpected large companion text file: {rel}")
            if PRIVATE_PATTERN.search(path.read_text(encoding="utf-8")):
                raise ValueError(f"Private operational path in companion file: {rel}")
    return {"scaffold": "PASS", "publication_ready": False, "note": "Scaffold success is not publication clearance."}


def validate_metadata(base, plan):
    output = {}
    for dataset in DATASETS:
        target = deposit_root(base, dataset, plan)
        verify_checksums(target, required=False)
        manifest = target / "metadata/manifest.csv"
        actual = summarise_manifest(manifest, dataset)
        check_expected(actual, plan["datasets"][dataset])
        if actual != read_json(target / "metadata/summary.json"):
            raise ValueError(f"Summary no longer agrees with manifest: {dataset}")
        receipt = read_json(target / "metadata/build_provenance.json")
        if receipt["export_manifest_sha256"] != sha256(manifest):
            raise ValueError("Export manifest provenance hash differs")
        source_name = "manifest.csv" if dataset == DATASETS[0] else "pairs.jsonl"
        expected_pin = plan["datasets"][dataset].get("source_manifest_sha256")
        if expected_pin and receipt["source_metadata_sha256"][source_name] != expected_pin:
            raise ValueError("Frozen source manifest hash differs")
        lists = {split: [] for split in SPLITS}
        for row in csv_rows(manifest):
            lists[row["split"]].append(row.get("record_id", row.get("sample_id")))
        for split, expected in lists.items():
            actual_ids = (target / "splits" / (split + ".txt")).read_text(encoding="utf-8").splitlines()
            if actual_ids != expected:
                raise ValueError("Frozen split IDs/order differ")
        for path in metadata_files(target):
            if PRIVATE_PATTERN.search(path.read_text(encoding="utf-8")):
                raise ValueError(f"Private operational path in metadata: {path.name}")
        output[dataset] = actual
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("scaffold", "metadata", "publish"), default="scaffold")
    parser.add_argument("--deposit", type=Path, default=deposit_base())
    parser.add_argument("--verify-files", action="store_true", help="Read and SHA-256-check every staged payload file.")
    args = parser.parse_args()
    report = {"mode": args.mode}
    try:
        report.update(validate_scaffold())
        plan = read_json(ROOT / "metadata/release_plan.json")
        if args.mode != "scaffold":
            report["datasets"] = validate_metadata(args.deposit, plan)
        if args.mode == "publish":
            report["unresolved_reviews"] = publication_blockers(
                plan, read_json(ROOT / "metadata/publication_status.json"),
                list(csv_rows(ROOT / "metadata/source_rights_review.csv")))
        if args.verify_files or args.mode == "publish":
            if args.mode == "scaffold":
                raise ValueError("Use metadata mode with --verify-files, not scaffold mode")
            if args.mode == "publish" and report["unresolved_reviews"]:
                raise ValueError("Unresolved reviews: " + "; ".join(report["unresolved_reviews"]))
            report["payload_files"] = {name: verify_payload(deposit_root(args.deposit, name, plan), name)
                                       for name in DATASETS}
        if args.mode == "publish":
            report["publication_ready"] = True
        print(json.dumps({"status": "PASS", **report}, indent=2))
    except (ValueError, KeyError, OSError, TypeError, csv.Error) as error:
        print(json.dumps({"status": "BLOCKED", "mode": args.mode, "reason": str(error)}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
