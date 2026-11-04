"""Create verified, bounded ZIP parts for an authorised PRIVATE dataset transfer."""

import argparse
import csv
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path

from publication import (ROOT, DATASETS, check_expected, contained_file, csv_rows,
                         deposit_root, make_checksums, metadata_files, read_json,
                         safe_relative, sha256, summarise_manifest, write_json)

PART_LIMIT = 1500 * 1024 * 1024
RESERVE = 30 * 1024 ** 3
PREFIXES = dict(zip(DATASETS, ("public-optical-v1", "paired-rgbt-v1")))


def write_once(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Existing transfer metadata differs; preserve and audit it")
    else:
        with path.open("xb") as stream:
            stream.write(raw)


def transfer_members(inventory, dataset, output):
    inventory_summary = read_json(inventory / "inventory_summary.json")
    summary = inventory_summary["datasets"][dataset]
    if summary["all_required_payload_present_and_pinned"] is not True:
        raise ValueError("Dataset payload is incomplete or unpinned; no archive created")
    entries = []
    with (inventory / "files.private.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            entry = json.loads(line)
            if entry["dataset"] == dataset:
                entries.append(entry)
    plan = read_json(ROOT / "metadata/release_plan.json")
    preview = deposit_root(ROOT / "data_deposit", dataset, plan)
    target = output / "transfer_metadata" / preview.name
    hashes = {}
    for entry in entries:
        if entry["role"] == "training_optic_label":
            hashes[entry["sample_id"]] = entry["expected_sha256"]
    for source in metadata_files(preview):
        relative = source.relative_to(preview).as_posix()
        if relative == "README.md":
            continue
        if dataset == DATASETS[1] and relative == "metadata/build_provenance.json":
            write_once(target / "metadata/metadata_preview_build_provenance.json", source.read_bytes())
            continue
        if dataset == DATASETS[1] and relative == "metadata/manifest.csv":
            import io
            rows = list(csv_rows(source))
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            for row in rows:
                row["training_label_sha256"] = hashes[row["sample_id"]]
                writer.writerow(row)
            raw = buffer.getvalue().encode("utf-8")
        else:
            raw = source.read_bytes()
        write_once(target / relative, raw)
    if dataset == DATASETS[1]:
        receipt = read_json(preview / "metadata/build_provenance.json")
        receipt.update({"stage": "private_transfer_manifest_not_public_release",
                        "previous_export_manifest_sha256": receipt["export_manifest_sha256"],
                        "export_manifest_sha256": sha256(target / "metadata/manifest.csv"),
                        "derived_training_labels_staged": True,
                        "canonical_training_provenance": inventory_summary["canonical_training_provenance"],
                        "payload_verification_note": "See the separately verified archive catalog; metadata alone is not payload completion."})
        write_once(target / "metadata/build_provenance.json", (json.dumps(receipt, indent=2) + "\n").encode())
    check_expected(summarise_manifest(target / "metadata/manifest.csv", dataset), plan["datasets"][dataset])
    text = (f"# {plan['datasets'][dataset]['title']}\n\n"
            "PRIVATE TRANSFER PREPARATION - NOT A PUBLIC DATA RELEASE\n\n"
            f"Dataset identifier: `{dataset}`. Extracted root: `{preview.name}/`.\n\n"
            "Extract every numbered ZIP part into the same parent folder. Each part is independently readable.\n"
            "PAYLOAD_FILES.csv lists every included frozen image/source label/training label and its SHA-256.\n"
            "Metadata manifests preserve retained sample IDs and frozen train/val/test assignments.\n"
            "Canonical training label bytes, where applicable, are copied from the existing frozen training artifact, not relabelled.\n"
            "Historical build_provenance.json and summary.json describe the earlier metadata export.\n"
            "The separate private_transfer.json and per-part verification record describe this transfer.\n"
            "Rights, ethics/privacy, licences, author information and public DOI review remain pending.\n"
            "Repository privacy must be retained; this transfer grants no public redistribution licence.\n")
    write_once(target / "README.md", text.encode("utf-8"))
    evidence = {"purpose": "authorised_private_transfer_not_publication_clearance",
                "dataset": dataset, "directory": preview.name,
                "source_manifest_sha256": plan["datasets"][dataset]["source_manifest_sha256"],
                "preview_manifest_sha256": sha256(preview / "metadata/manifest.csv"),
                "transfer_manifest_sha256": sha256(target / "metadata/manifest.csv"),
                "payload_files": len(entries), "payload_bytes": sum(e["bytes"] for e in entries),
                "training_hashes_added_from_actual_frozen_bytes": dataset == DATASETS[1],
                "canonical_training_provenance": inventory_summary.get("canonical_training_provenance") if dataset == DATASETS[1] else None,
                "membership_changed": False, "annotations_recomputed": False,
                "summary_payload_verification_flag_is_historical": True}
    write_once(target / "metadata/private_transfer.json", (json.dumps(evidence, indent=2) + "\n").encode())
    import io
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("relative_path", "size_bytes", "sha256", "role"))
    for entry in entries:
        writer.writerow((entry["relative_path"], entry["bytes"], entry["expected_sha256"], entry["role"]))
    write_once(target / "PAYLOAD_FILES.csv", buffer.getvalue().encode("utf-8"))
    make_checksums(target)
    extra = list(metadata_files(target)) + [target / "SHA256SUMS_METADATA.txt", target / "PAYLOAD_FILES.csv"]
    metadata = [{"relative_path": p.relative_to(target).as_posix(), "source_path": str(p),
                 "bytes": p.stat().st_size, "expected_sha256": sha256(p), "role": "metadata"} for p in extra]
    result = metadata + entries
    for entry in result:
        entry["archive_path"] = safe_relative(preview.name + "/" + entry["relative_path"])
    names = [entry["archive_path"] for entry in result]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate archive member")
    return result


def partition(entries, limit=PART_LIMIT):
    parts, current, total = [], [], 0
    for entry in entries:
        size = entry["bytes"] + len(entry["archive_path"].encode("utf-8")) * 4 + 8192
        if size > limit:
            raise ValueError("A single member exceeds the part limit")
        if current and total + size > limit:
            parts.append(current)
            current, total = [], 0
        current.append(entry)
        total += size
    if current:
        parts.append(current)
    return parts


def verify_part(path, entries):
    expected = {entry["archive_path"]: entry for entry in entries}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) != len(expected) or {i.filename for i in infos} != set(expected):
            raise ValueError("Archive membership differs")
        for info in infos:
            entry = expected[info.filename]
            if info.file_size != entry["bytes"]:
                raise ValueError("Archive member size differs")
            digest = hashlib.sha256()
            with archive.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != entry["expected_sha256"]:
                raise ValueError("Archive extraction checksum differs: " + info.filename)
    if path.stat().st_size >= PART_LIMIT:
        raise ValueError("ZIP part exceeds the conservative transfer limit")


def create_part(path, entries):
    partial = path.with_suffix(path.suffix + ".partial")
    if partial.exists():
        raise ValueError("Unfinished part exists; preserve and audit it before recovery")
    with zipfile.ZipFile(partial, "x", allowZip64=True) as archive:
        for entry in entries:
            source = Path(entry["source_path"])
            info = source.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_size != entry["bytes"]:
                raise ValueError("Payload source changed or is not a regular file")
            member = zipfile.ZipInfo(entry["archive_path"], date_time=(2026, 11, 4, 0, 0, 0))
            member.external_attr = 0o100644 << 16
            member.compress_type = zipfile.ZIP_STORED
            digest = hashlib.sha256()
            with source.open("rb") as reader, archive.open(member, "w", force_zip64=True) as writer:
                for block in iter(lambda: reader.read(1024 * 1024), b""):
                    digest.update(block)
                    writer.write(block)
            if digest.hexdigest() != entry["expected_sha256"]:
                raise ValueError("Source checksum differs: " + entry["archive_path"])
    verify_part(partial, entries)
    partial.rename(path)


def package(inventory, dataset, output):
    output.mkdir(parents=True, exist_ok=True)
    entries = transfer_members(inventory, dataset, output)
    parts = partition(entries)
    if len(parts) > 990:
        raise ValueError("Too many assets for one release")
    needed = sum(e["bytes"] for e in entries)
    existing = sum(p.stat().st_size for p in output.glob(PREFIXES[dataset] + "-part*.zip"))
    if shutil.disk_usage(output).free < max(0, needed - existing) + RESERVE:
        raise ValueError("Insufficient local disk space while preserving the free-space reserve")
    completed = []
    for number, members in enumerate(parts, 1):
        path = output / f"{PREFIXES[dataset]}-part{number:04d}.zip"
        if path.exists():
            verify_part(path, members)
        else:
            create_part(path, members)
        completed.append({"name": path.name, "bytes": path.stat().st_size,
                          "sha256": sha256(path), "members": len(members), "extraction_verified": True})
        write_json(output / f"{PREFIXES[dataset]}-packaging-progress.json",
                   {"dataset": dataset, "planned_parts": len(parts), "completed_parts": completed,
                    "inventory_sha256": sha256(inventory / "files.private.jsonl")})
        print(json.dumps({"stage": "part_verified", "part": number, "total": len(parts),
                          **completed[-1]}), flush=True)
    result = {"dataset": dataset, "directory": entries[0]["archive_path"].split("/")[0],
              "parts": completed, "files": len(entries), "payload_hashes_verified_now": True,
              "all_archive_members_extraction_verified": True, "public_release": False}
    write_json(output / f"{PREFIXES[dataset]}-archives.json", result)
    sums = "".join(f"{item['sha256']}  {item['name']}\n" for item in completed)
    write_once(output / f"{PREFIXES[dataset]}-SHA256SUMS.txt", sums.encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".local").resolve()):
        raise SystemExit("Private transfer preparation must remain inside .local")
    result = package(args.inventory.resolve(), args.dataset, output)
    print(json.dumps({"stage": "packaged", "dataset": args.dataset, "parts": len(result["parts"])}), flush=True)


if __name__ == "__main__":
    main()
