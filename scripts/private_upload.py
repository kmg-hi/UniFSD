"""Inventory the exact frozen payload for a private transfer; never rebuild data."""

import argparse
import json
import stat
from collections import Counter
from datetime import datetime
from pathlib import Path

from publication import (ROOT, DATASETS, HASH_PATTERN, contained_file, csv_rows,
                         deposit_root, read_json, safe_relative, sha256, write_json)
from validate_release import validate_metadata


def payload_sources(dataset, preview, config):
    source_root = Path(config["public_optical_root" if dataset == DATASETS[0]
                              else "paired_release_root"]).resolve()
    parents = {}
    training_hashes = read_json(config["paired_training_hashes"]) if config.get("paired_training_hashes") else {}
    training_root = Path(config["paired_training_root"]).resolve() if config.get("paired_training_root") else source_root
    for row in csv_rows(preview / "metadata/manifest.csv"):
        if dataset == DATASETS[0]:
            fields = (("image_path", "image_sha256", "image"),
                      ("label_path", "label_sha256", "source_label"))
        else:
            fields = (("optic_path", "optic_sha256", "optic"),
                      ("thermal_path", "thermal_sha256", "thermal"),
                      ("source_label_path", "source_label_sha256", "source_label"),
                      ("training_optic_label_path", "training_label_sha256", "training_optic_label"),
                      ("training_thermal_label_path", "training_label_sha256", "training_thermal_label"))
        for path_field, hash_field, role in fields:
            root = source_root
            if role.startswith("training_"):
                root = training_root
            relative = safe_relative(row[path_field])
            parent_key = (root, str(Path(relative).parent))
            if parent_key not in parents:
                parents[parent_key] = contained_file(root, relative).parent
            path = parents[parent_key] / Path(relative).name
            expected = row[hash_field]
            if role.startswith("training_"):
                expected = training_hashes.get(row["sample_id"], expected)
            yield {"dataset": dataset, "sample_id": row.get("record_id", row.get("sample_id")),
                   "role": role, "relative_path": relative,
                   "source_path": str(path), "expected_sha256": expected}


def restore_training_labels(artifact, output):
    plan = read_json(ROOT / "metadata/release_plan.json")
    source = read_json(artifact)
    expected = plan["datasets"][DATASETS[1]]
    if source["source_manifest_sha256"] != expected["source_manifest_sha256"]:
        raise ValueError("Canonical label artifact source pin differs")
    records = source["records"]
    indexed = {row["id"]: row for row in records}
    if len(indexed) != expected["expected_samples"] or len(indexed) != len(records):
        raise ValueError("Canonical label artifact membership differs")
    preview = deposit_root(ROOT / "data_deposit", DATASETS[1], plan)
    rows = list(csv_rows(preview / "metadata/manifest.csv"))
    if {row["sample_id"] for row in rows} != set(indexed):
        raise ValueError("Canonical label IDs differ from frozen release")
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for row in rows:
        record = indexed[row["sample_id"]]
        if (record["split"], record["domain"]) != (row["split"], row["domain"]):
            raise ValueError("Canonical label domain/split differs")
        raw = record["label"].encode("utf-8")
        import hashlib
        digest = hashlib.sha256(raw).hexdigest()
        if digest != record["label_sha256"] or not HASH_PATTERN.fullmatch(digest):
            raise ValueError("Archived canonical label bytes do not match their original hash")
        for field in ("training_optic_label_path", "training_thermal_label_path"):
            target = contained_file(output, row[field])
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
        hashes[row["sample_id"]] = digest
    write_json(output / "training_hashes.json", hashes)
    evidence = {"artifact_sha256": sha256(artifact), "source_manifest_sha256": source["source_manifest_sha256"],
                "pairs": len(hashes), "label_files": len(hashes) * 2,
                "method": "Copy existing UTF-8 label bytes from the frozen adapter artifact; verify every original label_sha256",
                "relabelled": False, "boxes_recomputed": False, "splits_changed": False}
    write_json(output / "restoration_evidence.json", evidence)
    print(json.dumps(evidence), flush=True)


def inventory(config, output):
    plan = read_json(ROOT / "metadata/release_plan.json")
    previews = ROOT / "data_deposit"
    validate_metadata(previews, plan)
    public = Path(config["public_optical_root"])
    paired = Path(config["paired_release_root"])
    for dataset, manifest in ((DATASETS[0], public / "metadata/manifest.csv"),
                              (DATASETS[1], paired / "pairs.jsonl")):
        if sha256(manifest) != plan["datasets"][dataset]["source_manifest_sha256"]:
            raise ValueError("Frozen original manifest differs; no payload preparation performed")
    output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    with (output / "files.private.jsonl").open("x", encoding="utf-8") as stream:
        for dataset in DATASETS:
            counts, sizes, missing, unpinned = Counter(), Counter(), Counter(), Counter()
            examples = []
            seen = set()
            preview = deposit_root(previews, dataset, plan)
            for entry in payload_sources(dataset, preview, config):
                relative = entry["relative_path"]
                if relative in seen:
                    raise ValueError("Duplicate member in frozen manifest")
                seen.add(relative)
                role = entry["role"]
                counts[role] += 1
                path = Path(entry["source_path"])
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    info = None
                if info is None:
                    missing[role] += 1
                    if len(examples) < 8:
                        examples.append({"role": role, "relative_path": relative})
                    entry["available"] = False
                    entry["bytes"] = None
                else:
                    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
                        raise ValueError("Non-regular payload member is not permitted")
                    entry["available"] = True
                    entry["bytes"] = info.st_size
                    entry["mtime_ns"] = info.st_mtime_ns
                    sizes[role] += entry["bytes"]
                if not HASH_PATTERN.fullmatch(entry["expected_sha256"]):
                    unpinned[role] += 1
                stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
                if sum(counts.values()) % 20000 == 0:
                    print(json.dumps({"stage": "inventory", "dataset": dataset,
                                      "files": sum(counts.values())}), flush=True)
            summaries[dataset] = {"directory": preview.name, "files_by_role": dict(counts),
                                  "available_bytes_by_role": dict(sizes),
                                  "missing_files_by_role": dict(missing),
                                  "missing_hashes_by_role": dict(unpinned),
                                  "missing_examples": examples,
                                  "available_bytes": sum(sizes.values()),
                                  "all_required_payload_present_and_pinned": not missing and not unpinned}
    provenance = read_json(Path(config["paired_training_root"]) / "restoration_evidence.json") if config.get("paired_training_hashes") else None
    report = {"checked_at": datetime.now().astimezone().isoformat(), "stage": "stat_inventory_only",
              "payload_sha256_verified_now": False, "uploaded": False,
              "canonical_training_provenance": provenance,
              "datasets": summaries}
    write_json(output / "inventory_summary.json", report)
    print(json.dumps(report, indent=2), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / ".local/inputs.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--restore-training-artifact", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".local").resolve()):
        raise SystemExit("The private inventory must remain inside .local; never upload source paths")
    if args.restore_training_artifact:
        restore_training_labels(args.restore_training_artifact, output)
    else:
        inventory(read_json(args.config), output)


if __name__ == "__main__":
    main()
