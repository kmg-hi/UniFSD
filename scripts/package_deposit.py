"""Create a clearly marked metadata preview, never an upload-ready media archive."""

import argparse
import zipfile
from pathlib import Path
from publication import ROOT, DATASETS, deposit_base, deposit_root, metadata_files, read_json, verify_checksums


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--metadata-only", action="store_true", required=True)
    args = parser.parse_args()
    plan = read_json(ROOT / "metadata/release_plan.json")
    base = deposit_root(deposit_base(ROOT), args.dataset, plan)
    verify_checksums(base)
    output = ROOT / "archives" / (args.dataset + "-INCOMPLETE-METADATA-PREVIEW.zip")
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("INCOMPLETE_NOT_FOR_DATA_PUBLICATION.txt", "No image/label payload; no publication clearance.\n")
        for path in metadata_files(base):
            archive.write(path, base.name + "/" + path.relative_to(base).as_posix())
        archive.write(base / "SHA256SUMS_METADATA.txt", base.name + "/SHA256SUMS_METADATA.txt")
    print("Local incomplete preview created:", output.name)


if __name__ == "__main__":
    main()
