"""Upload checksum-verified dataset ZIP parts to an unpublished private draft."""

import argparse
import json
import subprocess
import time
from pathlib import Path

from publication import ROOT, DATASETS, read_json, sha256, write_json
from package_private_upload import PART_LIMIT, PREFIXES, write_once

REPO = "kmg-hi/unified-fire-smoke-datasets"
BASE_COMMIT = "64f3f2cd5ef9fcb176d4da4d4f31b1946667e236"


def gh(executable, *args):
    result = subprocess.run([str(executable), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError("GitHub operation failed; inspect the remote state before retrying. "
                           + result.stderr[-1500:])
    return result.stdout


def verify_asset(asset, expected):
    if (asset.get("name") != expected["name"] or asset.get("size") != expected["bytes"]
            or asset.get("state") != "uploaded"
            or asset.get("digest") != "sha256:" + expected["sha256"]):
        raise ValueError("Remote asset size/state/SHA-256 differs; never overwrite it automatically")


def private_repository(executable):
    account = json.loads(gh(executable, "api", "user"))
    repo = json.loads(gh(executable, "api", "repos/" + REPO))
    if account["login"] != "kmg-hi" or repo["full_name"] != REPO or repo["private"] is not True:
        raise ValueError("Expected account/private repository not verified")


def upload(executable, dataset, output, allow_partial=False):
    private_repository(executable)
    prefix = PREFIXES[dataset]
    catalog_path = output / (prefix + "-archives.json")
    final = catalog_path.is_file()
    if final:
        catalog = read_json(catalog_path)
        planned_parts = len(catalog["parts"])
    elif allow_partial:
        progress = read_json(output / (prefix + "-packaging-progress.json"))
        plan = read_json(ROOT / "metadata/release_plan.json")
        if not progress["completed_parts"] or not all(p["extraction_verified"] for p in progress["completed_parts"]):
            raise ValueError("No verified finished ZIP parts are available")
        planned_parts = progress["planned_parts"]
        catalog = {"dataset": progress["dataset"], "parts": progress["completed_parts"],
                   "directory": plan["datasets"][dataset]["directory"],
                   "all_archive_members_extraction_verified": True}
    else:
        raise ValueError("Complete packaging catalog is absent")
    if catalog["dataset"] != dataset or not catalog["all_archive_members_extraction_verified"]:
        raise ValueError("Verified packaging catalog is required")
    tag = prefix + "-private-20261104"
    notes = output / (prefix + "-DOWNLOAD.md")
    text = (f"# Private transfer: {catalog['directory']}\n\n"
            "Unpublished preparation draft in a PRIVATE repository; not a public dataset release.\n\n"
            f"The complete transfer requires {planned_parts} independently readable ZIP parts. Download all numbered parts, "
            f"verify `{prefix}-SHA256SUMS.txt`, and extract every part into the same parent directory.\n"
            f"The result has the root folder `{catalog['directory']}/`. Do not concatenate the ZIP parts.\n\n"
            "PAYLOAD_FILES.csv inside the dataset root lists the retained payload members and SHA-256 values. "
            "Each uploaded part has passed source and archived-member hash checks. "
            "The transfer remains incomplete until all numbered parts, the archive catalog and checksum file are attached.\n\n"
            "Source annotations and canonical training annotations are distinct. Frozen IDs and train/val/test membership are preserved.\n"
            "Historical metadata preview status is separate from the new private-transfer verification record.\n\n"
            "Source/component redistribution rights, privacy/ethics, final licences, author approvals and DOI deposition remain pending. "
            "Keep this repository private and this release unpublished. No blanket reuse licence is granted.\n")
    write_once(notes, text.encode("utf-8"))
    releases = json.loads(gh(executable, "api", "repos/" + REPO + "/releases?per_page=100"))
    matches = [r for r in releases if r["tag_name"] == tag]
    if len(matches) > 1:
        raise ValueError("Duplicate release tags require audit")
    if not matches:
        gh(executable, "release", "create", tag, "--repo", REPO, "--draft", "--prerelease",
           "--latest=false", "--target", BASE_COMMIT, "--title", "Private dataset transfer: " + catalog["directory"],
           "--notes-file", str(notes))
        for attempt in range(5):
            releases = json.loads(gh(executable, "api", "repos/" + REPO + "/releases?per_page=100"))
            matches = [r for r in releases if r["tag_name"] == tag]
            if matches:
                break
            time.sleep(1)
    if len(matches) != 1 or matches[0]["draft"] is not True or matches[0]["target_commitish"] != BASE_COMMIT:
        raise ValueError("Expected unpublished draft and target commit not verified")
    release = matches[0]

    def assets():
        result, page = [], 1
        while True:
            batch = json.loads(gh(executable, "api", f"repos/{REPO}/releases/{release['id']}/assets?per_page=100&page={page}"))
            result.extend(batch)
            if len(batch) < 100:
                return result
            page += 1

    expected = list(catalog["parts"])
    if final:
        for path in (catalog_path, output / (prefix + "-SHA256SUMS.txt"), notes):
            expected.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    completed = []
    for item in expected:
        path = output / item["name"]
        if path.parent != output or item["bytes"] >= PART_LIMIT or sha256(path) != item["sha256"]:
            raise ValueError("Local asset changed or exceeds the part size limit")
        private_repository(executable)
        existing = [asset for asset in assets() if asset["name"] == item["name"]]
        if len(existing) > 1:
            raise ValueError("Duplicate remote asset names require audit")
        if not existing:
            print(json.dumps({"stage": "uploading", "asset": item["name"], "bytes": item["bytes"]}), flush=True)
            gh(executable, "release", "upload", tag, str(path), "--repo", REPO)
            existing = [asset for asset in assets() if asset["name"] == item["name"]]
        if len(existing) != 1:
            raise ValueError("Uploaded asset is not uniquely visible")
        verify_asset(existing[0], item)
        completed.append({**item, "asset_id": existing[0]["id"], "remote_digest": existing[0]["digest"]})
        write_json(output / (prefix + "-upload-progress.json"), {
            "repo": REPO, "tag": tag, "release_id": release["id"], "release_url": release["html_url"],
            "draft": True, "completed_assets": completed, "planned_assets": planned_parts + 3,
            "complete": final and len(completed) == len(expected)})
        print(json.dumps({"stage": "remote_digest_verified", "asset": item["name"],
                          "completed": len(completed), "total": planned_parts + 3}), flush=True)
    return {"dataset": dataset, "release_url": release["html_url"], "assets": len(completed),
            "draft": True, "private": True, "complete": final}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--gh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--allow-partial", action="store_true", help="Upload only finished, verified parts while packaging continues; never mark the transfer complete.")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".local").resolve()):
        raise SystemExit("Only audited .local transfer outputs may be uploaded")
    print(json.dumps(upload(args.gh.resolve(), args.dataset, output, args.allow_partial)), flush=True)


if __name__ == "__main__":
    main()
