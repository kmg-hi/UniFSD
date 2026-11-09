"""Read-only source metadata conversion; no media processing or network access."""

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("public_optical_release_v1", "paired_rgbt_v1")
SPLITS = ("train", "val", "test")
HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE_PATTERN = re.compile(r"\b[A-Za-z]:[\\/]|/(?:home|root|code/DC)/|127\.0\.0\.1")
REQUIRED_BLOCKERS = {
    "source_rights", "real_capture_ethics_privacy", "unity_asset_rights",
    "canonical_payload", "derived_label_provenance", "annotation_quality",
    "acquisition_metadata", "portable_processing_code", "authors_and_licenses",
    "repository_and_identifiers", "manuscript_and_deposit_alignment",
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Unsafe relative file path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in (".", "..", "") for p in value.split("/")):
        raise ValueError(f"Unsafe relative file path: {value!r}")
    if any(ord(c) < 32 for c in value):
        raise ValueError("Control character in path")
    return value


def contained_file(base, relative):
    relative = safe_relative(relative)
    base = Path(base).resolve()
    path = base.joinpath(*PurePosixPath(relative).parts)
    current = base
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink not allowed in deposit: {relative}")
    if not path.resolve().is_relative_to(base):
        raise ValueError("Path escapes deposit")
    return path


def deposit_root(base, dataset, plan):
    name = safe_relative(plan["datasets"][dataset]["directory"])
    if "/" in name:
        raise ValueError("Dataset directory must be a single top-level folder name")
    return contained_file(base, name)


def deposit_base(root=ROOT):
    root = Path(root)
    preview = root / "data_deposit"
    return preview if preview.is_dir() else root


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def read_schema(dataset):
    return read_json(ROOT / "schemas" / f"{dataset}.schema.json")


def validate_row(row, schema):
    fields = schema["properties"]
    if set(row) != set(fields):
        raise ValueError("Manifest fields differ from schema allowlist")
    for name, spec in fields.items():
        value = row[name]
        if not isinstance(value, str):
            raise ValueError(f"{name}: CSV value is not a string")
        if "enum" in spec and value not in spec["enum"]:
            raise ValueError(f"{name}: invalid category {value!r}")
        if "pattern" in spec and re.fullmatch(spec["pattern"], value) is None:
            raise ValueError(f"{name}: invalid lexical value")
        if name.endswith("_path"):
            safe_relative(value)
        if PRIVATE_PATTERN.search(value):
            raise ValueError(f"Private operational path in {name}")


def sanitize_registration(config):
    result = json.loads(json.dumps(config))
    source = result.get("calibration_source", {})
    source.pop("path", None)
    result["publication_note"] = "Private calibration file location removed; original matrices retained."
    if PRIVATE_PATTERN.search(json.dumps(result)):
        raise ValueError("Unrecognised private field in registration metadata")
    return result


def selected_json(source, destination, keys):
    data = read_json(source)
    result = {key: data[key] for key in keys if key in data}
    if PRIVATE_PATTERN.search(json.dumps(result)):
        raise ValueError("Selected metadata contains a private path")
    write_json(destination, result)


def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_rights_review_queue(target):
    fields = ["record_id", "image_path", "source_dataset", "source_record_id", "review_reason", "clearance"]

    def flagged():
        for row in csv_rows(Path(target) / "metadata/manifest.csv"):
            if row["source_dataset"] == "D-Fire" and "publicdataset" in row["source_record_id"].lower():
                yield {**{key: row[key] for key in fields[:4]},
                       "review_reason": "DFire_PublicDataset_component_original_provider_terms",
                       "clearance": "PENDING"}

    write_csv(Path(target) / "metadata/rights_review_queue.csv", fields, flagged())


def summarise_manifest(path, dataset, schema=None):
    schema = schema or read_schema(dataset)
    ids, files, groups, hashes = set(), set(), {}, {}
    splits, domains, sources = Counter(), Counter(), Counter()
    box_domains = defaultdict(Counter)
    total_boxes = negatives = dfire_marker = count = 0
    for row in csv_rows(path):
        validate_row(row, schema)
        count += 1
        identity = row["record_id"] if dataset == DATASETS[0] else row["sample_id"]
        if not identity or "\n" in identity or identity in ids:
            raise ValueError("Missing or duplicate sample ID")
        ids.add(identity)
        split, group = row["split"], row["split_group_id"]
        splits[split] += 1
        if not group or (group in groups and groups[group] != split):
            raise ValueError("Split group missing or crosses splits")
        groups[group] = split
        media = [(row["image_path"], row["image_sha256"])] if dataset == DATASETS[0] else [
            (row["optic_path"], row["optic_sha256"]),
            (row["thermal_path"], row["thermal_sha256"]),
        ]
        for file_path, digest in media:
            if file_path in files:
                raise ValueError("Duplicate media path")
            files.add(file_path)
            if digest in hashes and hashes[digest] != split:
                raise ValueError("Exact image content hash crosses splits")
            hashes[digest] = split
        if dataset == DATASETS[0]:
            sources[row["source_dataset"]] += 1
            boxes = int(row["box_count"])
            negative = row["is_negative"] == "true"
            if negative != (boxes == 0) or bool(row["classes"]) != (boxes > 0):
                raise ValueError("Class/negative/box-count inconsistency")
            total_boxes += boxes
            negatives += negative
            dfire_marker += row["source_dataset"] == "D-Fire" and "publicdataset" in row["source_record_id"].lower()
        else:
            domain = row["domain"]
            if group != f"{domain}:{row['experiment']}":
                raise ValueError("Pair group differs from domain:experiment")
            domains[domain] += 1
            for name in ("fire", "smoke"):
                box_domains[f"{split}/{domain}"][name] += int(row[f"source_{name}_boxes"])
    result = {"samples": count, "split_counts": dict(splits), "groups": len(groups),
              "group_cross_split_overlap": 0, "recorded_image_hash_cross_split_overlap": 0,
              "payload_files_verified_now": False}
    if dataset == DATASETS[0]:
        result.update(source_counts=dict(sources), boxes_from_manifest=total_boxes,
                      negative_images=negatives, dfire_publicdataset_name_matches=dfire_marker)
    else:
        result.update(domain_counts=dict(domains), source_box_counts_by_split_domain=dict(box_domains),
                      source_box_counts={name: sum(c[name] for c in box_domains.values()) for name in ("fire", "smoke")})
    return result


def check_expected(summary, expected):
    checks = [(summary["samples"], expected["expected_samples"], "sample count"),
              (summary["split_counts"], expected["expected_splits"], "split counts"),
              (summary["groups"], expected["expected_groups"], "group count")]
    if "expected_sources" in expected:
        checks.extend([(summary["source_counts"], expected["expected_sources"], "source counts"),
                       (summary["negative_images"], expected["expected_negative_images"], "negative count"),
                       (summary["boxes_from_manifest"], sum(expected["expected_boxes"].values()), "box count")])
    else:
        checks.extend([(summary["domain_counts"], expected["expected_domains"], "domain counts"),
                       (summary["source_box_counts"], expected["expected_source_boxes"], "source box counts")])
    for actual, wanted, name in checks:
        if actual != wanted:
            raise ValueError(f"Unexpected {name}: {actual!r} != {wanted!r}")


def metadata_files(base):
    base = Path(base)
    candidates = [base / "README.md"]
    for directory in ("metadata", "splits"):
        candidates.extend(p for p in (base / directory).rglob("*") if p.is_file())
    for path in sorted(candidates):
        if path.exists():
            relative = path.relative_to(base).as_posix()
            yield contained_file(base, relative)


def make_checksums(base):
    base = Path(base)
    lines = [f"{sha256(p)}  {p.relative_to(base).as_posix()}\n" for p in metadata_files(base)]
    (base / "SHA256SUMS_METADATA.txt").write_text("".join(lines), encoding="utf-8")


def distribution_metadata_files(base):
    for path in metadata_files(base):
        if "SHA256SUMS" not in path.name and path.name != "registration.public.json":
            yield path


def verify_checksums(base, required=True):
    base = Path(base)
    inventory = base / "SHA256SUMS_METADATA.txt"
    if not inventory.exists() and not required:
        return
    listed = set()
    for line in inventory.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if not HASH_PATTERN.fullmatch(digest) or relative in listed:
            raise ValueError("Invalid/duplicate metadata checksum entry")
        listed.add(relative)
        path = contained_file(base, relative)
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Metadata checksum mismatch: {relative}")
    actual = {p.relative_to(base).as_posix() for p in metadata_files(base)}
    if listed != actual:
        raise ValueError("Metadata inventory is incomplete")


def payload_entries(row, dataset):
    if dataset == DATASETS[0]:
        return [(row["image_path"], row["image_sha256"]), (row["label_path"], row["label_sha256"])]
    return [(row["optic_path"], row["optic_sha256"]), (row["thermal_path"], row["thermal_sha256"]),
            (row["source_label_path"], row["source_label_sha256"]),
            (row["training_optic_label_path"], row["training_label_sha256"]),
            (row["training_thermal_label_path"], row["training_label_sha256"])]


def verify_payload(base, dataset):
    checked = set()
    for row in csv_rows(Path(base) / "metadata/manifest.csv"):
        for relative, expected in payload_entries(row, dataset):
            if not HASH_PATTERN.fullmatch(expected):
                raise ValueError(f"Missing canonical payload hash: {relative}")
            if relative in checked:
                raise ValueError("Duplicate payload path")
            path = contained_file(base, relative)
            if not path.is_file() or sha256(path) != expected:
                raise ValueError(f"Missing or changed payload: {relative}")
            checked.add(relative)
    return len(checked)


def publication_blockers(plan, status, rights):
    issues = []
    rows = status.get("blockers", [])
    if {r.get("id") for r in rows} != REQUIRED_BLOCKERS or len(rows) != len(REQUIRED_BLOCKERS):
        issues.append("Required publication review categories are missing/duplicated")
    issues.extend(r.get("id", "unknown") for r in rows if r.get("resolved") is not True or not r.get("evidence"))
    if status.get("publication_ready") is not True or not status.get("reviewed_by") or not status.get("reviewed_at"):
        issues.append("Human publication sign-off absent")
    if not plan.get("authors") or any(not a.get("name") or not a.get("affiliation") for a in plan.get("authors", [])):
        issues.append("Author/affiliation metadata incomplete")
    for key in ("github_url", "software_version", "software_doi", "code_license"):
        if not plan.get(key):
            issues.append(f"Missing {key}")
    if plan.get("github_url") and not re.fullmatch(r"https://github\.com/[^/\s]+/[^/\s]+/?", plan["github_url"]):
        issues.append("GitHub repository URL is not a concrete repository")
    if plan.get("software_doi") and not re.fullmatch(r"10\.\d{4,9}/\S+", plan["software_doi"]):
        issues.append("Software DOI is not a DOI identifier")
    required_rights = {"FASDD_CV", "D-Fire", "CQU", "Roboflow_FireSmoke", "real_capture", "unity_synthetic", "derived_annotations"}
    if {r.get("source_id") for r in rights} != required_rights or len(rights) != len(required_rights):
        issues.append("Rights review source coverage incomplete")
    if any(r.get("publication_clearance") != "CLEARED" or not r.get("evidence_url") for r in rights):
        issues.append("Source/component rights review not cleared with evidence")
    for name in DATASETS:
        dataset = plan["datasets"][name]
        if not dataset.get("doi") or not dataset.get("license"):
            issues.append(f"Dataset identifier/licence incomplete: {name}")
        elif not re.fullmatch(r"10\.\d{4,9}/\S+", dataset["doi"]):
            issues.append(f"Invalid dataset DOI identifier: {name}")
    return issues
