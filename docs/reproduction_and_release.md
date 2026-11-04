# Reproduction and release procedure

## Metadata preparation only

Requirements: Python >=3.10, standard library only. No pip install is required.
Run commands from this companion folder, not from the whole research workspace.

Private `.local/inputs.json` has `public_optical_root` and `paired_release_root`.
It is already configured on the current machine and is ignored by Git. On a new
machine, set these to the accepted four-source candidate root and frozen paired
release root respectively. Never put private input paths in a tracked config.

```bash
python -B scripts/prepare_metadata.py --config .local/inputs.json
python -B -m unittest discover -s tests -v
python -B scripts/validate_release.py --mode scaffold
python -B scripts/validate_release.py --mode metadata
```

The exporter refuses an existing `data_deposit/`. Preserve/review an earlier
preview before preparing another; it never deletes an existing dataset folder.
A failed export may leave an incomplete preview which must not be published.
The validator detects missing/inconsistent files. Source files are read-only.

The two output roots are `data_deposit/public optical/` and `data_deposit/paired_RGBT/`,
as configured by each record's `directory` in `metadata/release_plan.json`.
These names do not change the stable record IDs or schema filenames. Quote the
entire path when passing a path containing `public optical` to a command.

Metadata checks verify full row membership, categories, counts, group and exact
recorded-content-hash split separation, relative paths, split-list order, and
metadata checksums. Metadata SHA values do not verify the actual media payload.

## Payload and publication checks

Do not download/rebuild/reclip frozen training data as an automatic preparation
step. After rights review, stage the existing authorised canonical payload at the
manifest-relative paths, export actual derived GT hashes and update provenance.
Reconcile changes with the immutable benchmark version explicitly.

```bash
python -B scripts/validate_release.py --mode metadata --verify-files
python -B scripts/validate_release.py --mode publish
```

The first reads every staged image/label for SHA-256 comparison. It is not a visual
image-quality, annotation or privacy audit. The second additionally requires
documented human review, rights decisions and real author/repository/licence
metadata. Currently both are expected to fail because payload/clearance is absent.
Never fill pending fields with fabricated hashes or blanket permissions.

For a local metadata preview only:

```bash
python -B scripts/package_deposit.py public_optical_release_v1 --metadata-only
```

This creates an archive explicitly marked INCOMPLETE. It is not a payload upload.
Archive names retain the record ID; extracted dataset files are
under `public optical/` or `paired_RGBT/`, with an incompleteness notice alongside.
Do not confuse this metadata preview with the separately verified private ZIP
payload parts described below.

## Authorised private transfer

The local-only workflow `private_upload.py` inventories only frozen manifest
members, and can copy canonical label bytes from an existing training artifact
after checking original hashes, IDs and splits. It never regenerates boxes.
Private paths/configuration and the raw training artifact remain in `.local/`.

`package_private_upload.py` checks every source SHA-256, creates independently
readable ZIP parts below 1500 MiB, then reads every archived member to verify its
extracted bytes. Failed `.partial` files are preserved and cannot be uploaded.
The transfer manifest's canonical training hashes have separate provenance;
the earlier metadata-only manifest and receipt remain preserved.

`upload_private_assets.py` requires explicit `--execute`, verifies the `kmg-hi`
account and PRIVATE target repository, and uploads to unpublished drafts only.
It verifies remote sizes, uploaded state and server SHA-256 digests. Matching
assets are reused, unknown/mismatched assets are never overwritten. Partial
transfers remain explicitly incomplete until all ZIP parts and companion files
are verified. No LFS, paid capacity, automatic workflow, public visibility or
release publication is enabled by these utilities.

Repository clones include metadata at `public optical/` and `paired_RGBT/`;
the validator uses these roots when `data_deposit/` is absent. Full file
verification additionally requires all corresponding ZIP parts to be extracted.

## Original scientific pipeline still to port

`metadata/code_provenance_inventory.csv` identifies local source filenames and
hashes, not a public, runnable reproduction package. Internal dashboards/remote
bridge scripts are deliberately not vendored. The original deduplication,
registration, annotation conversion and split code needs a separate licence and
private-path review, portable inputs, dependency lock, small lawful examples,
expected outputs and end-to-end tests. These publication utilities do not
reproduce those scientific processing steps by themselves.

## After author/institution approval

Finalise templates, choose licences component-by-component, create the GitHub
companion repository and appropriate data records, verify reviewer downloads,
record exact release/archive hashes, and align the article's records/citations.
Keep the article/data/code version mapping and retain institutional backups.
Public uploading remains a separate, explicit action, not a side effect here.
