"""Export publication metadata without copying or changing source images/labels."""

import argparse
import csv
from pathlib import Path

from publication import (ROOT, DATASETS, SPLITS, check_expected, csv_rows, deposit_root, make_checksums,
                         read_json, read_schema, safe_relative, sanitize_registration,
                         selected_json, sha256, summarise_manifest, write_csv, write_json,
                         write_rights_review_queue)


def export_public(source, target):
    metadata = source / "metadata"
    inventory = {r["relative_path"]: r for r in csv_rows(metadata / "file_checksums_sha256.csv")}
    schema = read_schema(DATASETS[0])

    def converted():
        for source_row in csv_rows(metadata / "manifest.csv"):
            row = {k: source_row[k] for k in schema["properties"] if k != "label_sha256"}
            image = inventory[safe_relative(row["image_path"])]
            label = inventory[safe_relative(row["label_path"])]
            if image["sha256"] != row["image_sha256"] or image["size_bytes"] != row["file_size_bytes"]:
                raise ValueError("Source manifest/checksum inventory disagreement")
            row["label_sha256"] = label["sha256"]
            yield row

    write_csv(target / "metadata/manifest.csv", list(schema["properties"]), converted())
    write_rights_review_queue(target)
    for original, output in (("source_registry.csv", "source_registry.csv"),
                             ("license_provenance.csv", "license_provenance_recorded.csv")):
        rows = list(csv_rows(metadata / original))
        write_csv(target / "metadata" / output, list(rows[0]), rows)
    for name, keys in {
        "split_summary.json": ["version", "images", "boxes", "totals", "split_seed", "split_ratios", "group_span", "groups", "groups_crossing_splits", "removed_duplicate_rows"],
        "deduplication_config.json": ["source_priority", "thresholds", "lsh", "keep_policy", "input_counts", "cqu_new_internal_stage4", "cross", "retained_counts", "final_images", "historical_internal_stages"],
    }.items():
        selected_json(metadata / name, target / "metadata" / ("source_" + name), keys)
    return {p.name: sha256(p) for p in [metadata / name for name in
            ("manifest.csv", "file_checksums_sha256.csv", "source_registry.csv", "license_provenance.csv", "split_summary.json", "deduplication_config.json")]}


def export_paired(source, target, expected_sha):
    original = source / "pairs.jsonl"
    actual = sha256(original)
    if actual != expected_sha:
        raise ValueError("Frozen paired source manifest hash differs; do not rebuild/resplit")
    schema = read_schema(DATASETS[1])

    def converted():
        import json
        with original.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                domain, experiment, stem = row["domain"], row["experiment"], row["stem"]
                sizes = row.get("image_sizes", {})
                optic = row.get("optic_size", sizes.get("optic"))
                thermal = row.get("thermal_size", sizes.get("thermal_registered"))
                if not optic or not thermal:
                    raise ValueError("Retained-view dimensions unavailable")
                yield {"sample_id": row["id"], "split": row["split"], "domain": domain,
                       "experiment": experiment, "scene": row.get("scene", ""),
                       "split_group_id": f"{domain}:{experiment}",
                       "optic_path": row["release_optic_path"], "thermal_path": row["release_thermal_path"],
                       "source_label_path": row["release_label_path"],
                       "training_optic_label_path": safe_relative(f"labels/optic/{domain}/{experiment}/{stem}.txt"),
                       "training_thermal_label_path": safe_relative(f"labels/thermal/{domain}/{experiment}/{stem}.txt"),
                       "optic_sha256": row["optic_sha256"], "thermal_sha256": row["thermal_sha256"],
                       "source_label_sha256": row["label_sha256"], "training_label_sha256": "",
                       "optic_width": str(optic[0]), "optic_height": str(optic[1]),
                       "thermal_width": str(thermal[0]), "thermal_height": str(thermal[1]),
                       "source_fire_boxes": str(row["fire_boxes"]), "source_smoke_boxes": str(row["smoke_boxes"]),
                       "source_label_basis": row.get("label_basis", ""),
                       "annotation_provenance": "existing_real_labels_protocol_pending" if domain == "real" else "model_assisted_review_protocol_pending"}

    write_csv(target / "metadata/manifest.csv", list(schema["properties"]), converted())
    write_json(target / "metadata/registration.public.json", sanitize_registration(read_json(source / "registration_config.json")))
    selected_json(source / "split_summary.json", target / "metadata/source_summary.json", [
        "total_pairs", "total_views", "seed", "ratio_target", "split_unit", "split_counts", "experiments", "leakage_groups",
        "excluded_reviewed_empty", "excluded_unreviewed", "exact_image_hash_cross_split_overlap", "experiment_cross_split_overlap",
        "scene_disjoint", "old_real_splits_preserved", "existing_real_border_overflow_boxes",
        "synthetic_test_is_model_assisted_not_fully_independent_gt", "thermal_warning", "manifest_sha256"])
    selected_json(source / "validation.json", target / "metadata/source_validation_recorded.json", [
        "state", "pairs", "views", "label_files", "final_media_sha256_checks", "label_sha256_checks", "provenance_sha256_checks",
        "exact_content_cross_split_overlap", "experiment_cross_split_overlap", "all9splitlists_match", "frozen_source_membership_matches", "manifest_sha256"])
    return {name: sha256(source / name) for name in ("pairs.jsonl", "split_summary.json", "registration_config.json", "validation.json")}


def finish(target, dataset, inputs, expected):
    manifest = target / "metadata/manifest.csv"
    summary = summarise_manifest(manifest, dataset)
    check_expected(summary, expected)
    write_json(target / "metadata/summary.json", summary)
    write_json(target / "metadata/classes.json", {"0": "fire", "1": "smoke"})
    write_json(target / "metadata/build_provenance.json", {
        "stage": "metadata_only_not_a_data_release", "source_metadata_sha256": inputs,
        "export_manifest_sha256": sha256(manifest), "media_copied": False, "labels_rewritten": False,
        "source_payload_rehashed_now": False, "splits_regenerated": False,
        "derived_training_labels_staged": False,
        "redactions": ["Private local/remote operational path fields are excluded by allowlist."] +
                      (["calibration_source.path removed from registration configuration."] if dataset == DATASETS[1] else []),
        "rights_status": "Recorded source terms are not current component-level clearance."})
    handles = {}
    try:
        (target / "splits").mkdir()
        for split in SPLITS:
            handles[split] = (target / "splits" / (split + ".txt")).open("w", encoding="utf-8", newline="\n")
        for row in csv_rows(manifest):
            handles[row["split"]].write(row.get("record_id", row.get("sample_id")) + "\n")
    finally:
        for stream in handles.values():
            stream.close()
    rights = list(csv_rows(ROOT / "metadata/source_rights_review.csv"))
    write_csv(target / "metadata/source_rights_review.csv", list(rights[0]), rights)
    (target / "README.md").write_text(
        f"# {expected['title']} - INCOMPLETE METADATA PREVIEW\n\n"
        f"Dataset identifier: `{dataset}`.\n\n"
        f"Release root directory: `{expected['directory']}/`.\n\n"
        "No images or label payloads have been copied. Not an upload-ready dataset.\n"
        "Manifest hashes are expected source values, not fresh full-image checks.\n"
        "Source GT and canonical derived training GT are distinct; derived hashes remain pending.\n"
        "SHA256SUMS_METADATA.txt covers only this metadata preview.\n"
        "Rights, privacy, authors, licence and identifiers require review.\n"
        "See the companion repository data dictionary and dataset card before reuse.\n", encoding="utf-8")
    make_checksums(target)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / ".local/inputs.json")
    args = parser.parse_args()
    config = read_json(args.config)
    plan = read_json(ROOT / "metadata/release_plan.json")
    destination = ROOT / "data_deposit"
    if destination.exists():
        raise SystemExit("data_deposit already exists; preserve it. Review/archive it explicitly before a new export.")
    source_public = Path(config["public_optical_root"]).resolve()
    source_paired = Path(config["paired_release_root"]).resolve()
    if source_public.is_relative_to(destination) or source_paired.is_relative_to(destination):
        raise SystemExit("Input cannot be inside output")
    expected_public_sha = plan["datasets"][DATASETS[0]]["source_manifest_sha256"]
    if sha256(source_public / "metadata/manifest.csv") != expected_public_sha:
        raise SystemExit("Frozen Public Optical manifest differs; no export performed")
    first, second = [deposit_root(destination, name, plan) for name in DATASETS]
    receipts = {}
    receipts[DATASETS[0]] = finish(first, DATASETS[0], export_public(source_public, first), plan["datasets"][DATASETS[0]])
    receipts[DATASETS[1]] = finish(second, DATASETS[1], export_paired(source_paired, second, plan["datasets"][DATASETS[1]]["source_manifest_sha256"]), plan["datasets"][DATASETS[1]])
    write_json(ROOT / ".local/preparation_summary.json", receipts)
    print("Prepared metadata only:", {k: v["samples"] for k, v in receipts.items()})


if __name__ == "__main__":
    main()
