# Unified Single-Modal and Multi-Modal Fire and Smoke Datasets

**Publication draft: no public dataset download is available yet.**

This project brings together two distinct fire and smoke detection resources:

- **unified single-modal optical dataset:** a curated collection of optical images from four public sources.
- **multi-modal optical–thermal paired dataset:** corresponding optical and processed thermal images from real-world experiments and Unity simulations.

This private preparation repository is being assembled for documentation,
metadata, validation utilities, and the original retained image and annotation
files of both datasets. The author-approved private data transfer is complete.
The project title, authors, licences, public download locations, and citation identifiers
have not yet been finalised. The folder names below describe the planned release
layout, not a claim that the image and annotation payloads are already available.

## Dataset overview

| Dataset | Sample unit | Train | Validation | Test | Total |
|---|---|---:|---:|---:|---:|
| unified single-modal optical dataset | One optical image | 68,475 | 8,714 | 9,374 | 86,563 |
| multi-modal optical–thermal paired dataset | One optical-thermal pair | 28,811 | 3,524 | 3,524 | 35,859 |

The publication-facing names were updated on 2026-11-04. The stable record
identifiers remain `public_optical_release_v1` and `paired_rgbt_v1`, respectively.
Their release root directories are `public optical/` and `paired_RGBT/`,
respectively; these folder names are distinct from the stable record identifiers.
Public Optical and Paired RGB-T are previous short names used in historical
documentation; the renaming does not change file contents, annotations, or split membership.

### unified single-modal optical dataset

| Retained source | Images |
|---|---:|
| FASDD_CV | 66,480 |
| D-Fire | 6,288 |
| CQU | 6,244 |
| Roboflow_FireSmoke | 7,551 |
| **Total** | **86,563** |

This version contains 112,279 annotated boxes: 67,269 Fire and 45,010 Smoke.
There are 41,364 images with zero annotated target boxes. These are designated
negative samples; that designation is not an independent guarantee that every
possible fire or smoke phenomenon is absent. DFS is excluded from this version.

### multi-modal optical–thermal paired dataset

| Domain | Train pairs | Validation pairs | Test pairs | Total pairs |
|---|---:|---:|---:|---:|
| Real | 12,190 | 1,524 | 1,524 | 15,238 |
| Unity synthetic | 16,621 | 2,000 | 2,000 | 20,621 |
| **Total** | **28,811** | **3,524** | **3,524** | **35,859** |

The paired collection contains 71,718 image views from 66 real and 21 synthetic
experiments. Every retained pair has at least one source-annotated target.
The 20,621 synthetic pairs were selected from 21,000 candidates by excluding
206 reviewed-empty and 173 unlabelled samples; these exclusions are not a count
of perceptual duplicates removed.

Optic-only, thermal-only, and optical-thermal experiments on the paired dataset
use the same pair membership, frozen splits, and common derived targets.
**Paired optic-only experiments are not the separate unified single-modal optical dataset.**

## Data access and release status

| Resource | Current status | Download / identifier |
|---|---|---|
| unified single-modal optical dataset archives | Private upload complete: 8 verified ZIP parts; not publicly released | [Private draft assets](https://github.com/kmg-hi/unified-fire-smoke-datasets/releases/tag/untagged-83bf651c3c7c7f34d35b) |
| multi-modal optical–thermal paired dataset archives | Private upload complete: 17 verified ZIP parts; not publicly released | [Private draft assets](https://github.com/kmg-hi/unified-fire-smoke-datasets/releases/tag/untagged-d38a0decc3241fd55fa6) |
| Dataset version DOIs | Not assigned | Not assigned |
| Paper | Manuscript preparation | Not assigned |

The repository's `public optical/` and `paired_RGBT/` directories contain the
dataset metadata, frozen split lists, and payload inventories. The actual retained
images, source annotations, and canonical training annotations are available as
independently readable ZIP parts attached to unpublished drafts in this same
private repository, not as ordinary Git blobs or metered Git LFS objects.
Download all numbered parts for a dataset, verify their archive checksums, and
extract every part into the same parent directory. Do not concatenate the ZIPs.
Both private transfers are complete: all 25 ZIP parts and six archive-catalog,
checksum and download-note assets were uploaded and their server SHA-256 values
verified. They cover 352,421 frozen image/annotation files, plus metadata. No paid
capacity is enabled. Verification is recorded in `metadata/private_transfer_status.json`.
Private draft locations:
[public optical](https://github.com/kmg-hi/unified-fire-smoke-datasets/releases/tag/untagged-83bf651c3c7c7f34d35b),
[paired_RGBT](https://github.com/kmg-hi/unified-fire-smoke-datasets/releases/tag/untagged-d38a0decc3241fd55fa6).
A future public release still requires component rights/privacy review, final
licences, a suitable persistent dataset record, and version-specific identifiers.

## Intended repository layout

Companion documentation and metadata are provided in the directories
below. Image and annotation payloads are in the separate private ZIP attachments.

```text
README.md                         Dataset introduction and access information
dataset_cards/                    Dataset-specific descriptions and limitations
docs/                             Layout, field definitions, methods, and release notes
metadata/                         Preparation status, overview, and rights review tables
schemas/                          Manifest field definitions
scripts/                          Metadata preparation and validation utilities
tests/                            Tests for the preparation utilities
templates/                        Unfinished citation and deposit metadata templates
LICENSES/                         Licensing guidance; final terms still pending
public optical/                   Single-modal metadata, splits, and payload inventory
paired_RGBT/                      Paired metadata, splits, registration, and payload inventory
```

This README remains a preparation draft, not a dataset release announcement.
Private local configuration, credentials, research logs, and model weights are
excluded. Manuscript working files require a separate review. Original retained
images and labels are within the approved private upload scope, but require a
separate, storage-aware transfer step rather than an unreviewed regular-Git push.

## Planned dataset archive layouts

The two dataset archives are separate from the companion repository:

```text
public optical/
  README.md
  images/{train,val,test}/
  labels/{train,val,test}/
  metadata/
    manifest.csv
    classes.json
    summary.json
    ...
  splits/{train,val,test}.txt
  SHA256SUMS_METADATA.txt

paired_RGBT/
  README.md
  dataset/{real,synthetic}/{experiment}/
    pair_optic/
    pair_thermal/
    pair_label/
  labels/{optic,thermal}/{real,synthetic}/{experiment}/
  metadata/
    manifest.csv
    classes.json
    registration.public.json
    summary.json
    ...
  splits/{train,val,test}.txt
  SHA256SUMS_METADATA.txt
```

Image and annotation directories appear after all private ZIP parts are extracted;
they are not included as ordinary Git files in the repository tree.
Paths inside each manifest are relative to its dataset root. Quote paths containing
the space in `public optical` when using command-line tools. Preparation scripts
still accept stable record identifiers and resolve folder names from `metadata/release_plan.json`.
`SHA256SUMS_METADATA.txt` covers metadata only. `PAYLOAD_FILES.csv` records the
payload paths, sizes, and expected hashes; the separate archive catalogs and
`*-SHA256SUMS.txt` files record verified ZIP parts. Metadata alone does not prove
that the entire transfer has completed.

## Sample identifiers and correspondence

The single-modal record uses stable retained identifiers such as `POU000001`; the manifest
also retains source collection and source-relative identifiers. An example
image-label path pair recorded in the manifest is:

```text
images/train/FASDD_CV__all__bothFireAndSmoke_CV000000.jpg
labels/train/FASDD_CV__all__bothFireAndSmoke_CV000000.txt
```

The paired record uses a domain-qualified `sample_id`, for example:

```text
real:230714_3m_nan/230714_3m_nan_pair_00001
```

Its optical image, thermal image, and source annotation share the stem
`230714_3m_nan_pair_00001` within the same domain and experiment. Use `sample_id`
as a manifest key, not as a literal filesystem path. Paths in the manifests are
relative to their dataset archive root and use `/` separators.

## Annotation format

Model-training annotations use one object per line in YOLO text format:

```text
class_id x_center y_center width height
```

| Class identifier | Class |
|---|---|
| 0 | Fire |
| 1 | Smoke |

Coordinates are normalised by image width and height. An empty training label
file represents zero annotated boxes. Do not infer that both dataset versions
retain background-only samples: the paired version contains only source-positive
pairs.

In the paired record, `pair_label/` preserves source annotations, while
`labels/{optic,thermal}/` is reserved for the actual canonical derived training
annotations. Real source boxes extending beyond the visible frame were clipped
for the common training targets. Source and training annotation files must not be
silently substituted for one another.

`source_label_sha256` records source-label integrity. The separate
`training_label_sha256` field in the private-transfer manifest is populated from
the existing frozen training artifact, with every restored label's bytes checked
against its original SHA-256. Older metadata-only previews left this field blank.
Source hashes were not substituted and ground truth was not regenerated.
Synthetic annotations were model assisted; the full annotation and review
protocol remains to be documented.

## Frozen dataset partitions

- The single-modal record: 5,845 filename-derived sequence groups, seed `20260924`.
- The paired record: 87 domain-and-experiment groups, seed `20261025`.
- No group occurs in more than one split in the exported manifests.
- Group separation does **not** establish complete scene independence.

Each `splits/*.txt` file lists frozen sample identifiers, one per line, rather
than image paths. Keep these assignments when reproducing the reported
benchmarks. Do not create new random splits as part of downloading or unpacking
the data. Independent new experiments should identify any changed partition
scheme explicitly.

## Quick start

### Metadata preparation checks available now

The included preparation utilities use Python 3.10 or later and the standard
library. From the companion repository root:

```bash
python -B -m unittest discover -s tests -v
python -B scripts/validate_release.py --mode scaffold
python -B scripts/validate_release.py --mode metadata
```

Metadata validation uses the two dataset root folders when present in the
repository; the earlier local `data_deposit/` layout is also supported.
Cloning the repository does not supply the actual image/annotation payloads:
download and extract every private ZIP part before requesting payload verification.
See the [reproduction and release notes](docs/reproduction_and_release.md) for
the preparation workflow. Source paths and local configuration must never be
published with the repository.

These commands do not download data, train a model, or verify every payload file.
The publication validator currently blocks release because review and payload
requirements are unfinished. Original processing, training, and inference
workflows still require separately reviewed, portable instructions; no working
end-to-end training command is claimed here.

### Dataset use after publication

1. Download the approved archive version from its dataset record.
2. Verify the supplied archive checksums and extract the documented directory tree.
3. Resolve manifest paths from the appropriate dataset root.
4. Select samples using the published split identifiers and preserve optical-thermal correspondence.
5. Use canonical derived training labels for benchmark reproduction, retaining source annotations for provenance.

## Metadata and technical notes

The [data dictionary](docs/data_dictionary.md) explains manifest fields, class
mapping, label provenance, and the distinction between recorded and newly
verified hashes. See also:

- [unified single-modal optical dataset card](dataset_cards/public_optical.md)
- [multi-modal optical–thermal paired dataset card](dataset_cards/paired_rgbt.md)
- [Dataset and deposit layout](docs/repository_and_deposit_layout.md)
- [Methods and validation notes](docs/methods_and_validation.md)
- [Source and rights review](docs/rights_ethics_and_assets.md)

### Important limitations

- The real held-out test subset has Fire annotations but **no Smoke ground-truth boxes**. It cannot establish real-world test Smoke performance.
- Registered Unity thermal views are processed colour images, not calibrated temperature measurements. Reference-plane registration leaves residual parallax at other depths.
- Synthetic labels are model assisted, not fully independent manually drawn ground truth.
- Filename- or experiment-level separation is not a guarantee of scene-disjoint evaluation or exhaustive semantic deduplication.
- The two dataset versions have not been jointly audited for cross-release content overlap.
- Existing source validation records are historical evidence, not a fresh integrity or annotation-quality audit of a publication payload.

## Licensing and source attribution

**Final data and code licences have not been assigned.** Public availability of
source images is not, by itself, redistribution permission. Component-level
terms and attribution must be checked for FASDD_CV, D-Fire, CQU, and
Roboflow_FireSmoke. Excluding DFS does not clear the remaining sources.

Real capture permissions, privacy/ethics requirements, and Unity rendered-output
rights also require review. The licences for images, annotations, newly prepared
metadata, and code must be stated separately where their terms differ. No blanket
permission or common dataset-wide licence is granted by this draft.

The [prepublication checklist](PREPUBLICATION_CHECKLIST.md) and
[licensing notes](LICENSES/README.md) track the work needed before release.

## Citation

The dataset version DOIs, final paper citation, author list, and root
`CITATION.cff` are pending. Do not cite placeholder identifiers or describe this
draft as a published dataset. The final repository should cite the exact data
versions, their original component sources, and the accompanying paper when
available.

## Contact and contributions

Maintainer details and an approved contact address will be added after author
review. Once the repository is established, report problems with the dataset
version, sample identifier, and a reproducible description. Proposed corrections
must preserve prior release history and document any changes to annotations or
split membership.
