"""Regenerate metadata-preview checksums only, never media checksum claims."""

import argparse
from pathlib import Path
from publication import make_checksums


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deposit_record", type=Path)
    parser.add_argument("--confirm-metadata-only", action="store_true", required=True)
    args = parser.parse_args()
    if not (args.deposit_record / "metadata/manifest.csv").is_file():
        raise SystemExit("No prepared metadata manifest")
    make_checksums(args.deposit_record)
    print("Metadata checksums regenerated. This does not verify image/label payloads.")
