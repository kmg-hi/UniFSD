# Repository and deposit layout

## Companion code/documentation repository

Publish the contents of this preparation folder only after review, excluding
`.local/`, `data_deposit/`, archives, images, credentials and weights. The root
`.gitignore` is a convenience, not a security or copyright audit. Do not initialise
Git in the entire parent research workspace or push the full research ledger.

Before a release, finish the templates, add agreed licence files, and copy the
final citation metadata to root `CITATION.cff` and, if used, `.zenodo.json`.
Authors, ORCIDs and identifiers must be supplied, not guessed.

For the author's separately approved PRIVATE transfer, the repository also holds
`public optical/` and `paired_RGBT/` metadata/split directories. The actual frozen
images and source/canonical training labels are in numbered ZIP parts attached
to unpublished private drafts, not ordinary Git or metered LFS. Extract all parts
into the same parent directory to reconstruct the dataset roots below. This
private transfer is not public redistribution clearance or a persistent DOI deposit.

## Proposed dataset deposit A: unified single-modal optical dataset

```text
public optical/
  README.md
  metadata/
    manifest.csv
    source_registry.csv
    license_provenance_recorded.csv
    source_rights_review.csv
    source_split_summary.json
    summary.json
    build_provenance.json
  splits/train.txt, val.txt, test.txt
  images/{train,val,test}/...          [NOT STAGED]
  labels/{train,val,test}/...          [NOT STAGED]
  SHA256SUMS_METADATA.txt
```

Keep original licence/attribution evidence beside the final deposit. The current
metadata export preserves relative manifest paths and expected image/label hashes.
It does not constitute approval to distribute these images.

## Proposed dataset deposit B: multi-modal optical–thermal paired dataset

```text
paired_RGBT/
  README.md
  metadata/
    manifest.csv
    registration.public.json
    source_summary.json
    source_validation_recorded.json
    summary.json
    build_provenance.json
  splits/train.txt, val.txt, test.txt
  dataset/{real,synthetic}/{experiment}/
    pair_optic/...                    [NOT STAGED]
    pair_thermal/...                  [NOT STAGED: registered thermal]
    pair_label/...                    [NOT STAGED: source GT]
  labels/{optic,thermal}/{domain}/{experiment}/...
                                     [NOT STAGED: canonical derived GT]
  SHA256SUMS_METADATA.txt
```

These root directory names are exact, including the space in `public optical` and
capitalisation of `paired_RGBT`. The stable record identifiers remain
`public_optical_release_v1` and `paired_rgbt_v1`; schema filenames and manifest IDs
are unchanged. Manifest file paths are relative to the corresponding root.
The `directory` fields in `metadata/release_plan.json` configure the preparation tools.

`pair_label` source labels and `labels/...` training labels have different roles.
Do not regenerate the latter as part of packaging. Populate their presently blank
hashes only from the actual frozen training artefacts. If raw thermal or original
sensor exports are shared, use separate documented paths, dimensions, bit depths,
rights and checksums. Do not call registered RGB thermal views raw radiometry.

## Archive inventory and identifiers

Measure payload sizes first. Assign stable shard names, for example
`paired-rgbt-v1-media-0001.tar`, and list every member in a checksummed inventory.
Split by whole files, retain relative paths, reject traversal and symlinks, and
verify an extraction test. Avoid thousands of loose web uploads. The included
packager creates **only an incomplete metadata preview**, not a final data deposit.

Choose repositories/quotas with the institution. Related records should link the
code version, dataset versions and eventual article DOI with accurate relation
types. A concept DOI identifies a family; cite the specific version used for
reproduction. Do not publish placeholder DOIs or reviewer access tokens in Git.
