# Data dictionary

All exports: UTF-8; CSV header present; empty values mean unknown/not staged, not
zero. Paths use `/`, are relative to the dataset-deposit root and cannot contain
parent traversal. Splits are frozen `train`, `val`, `test`. Hashes are lowercase
SHA-256 of file bytes; source/recorded hashes are not a fresh payload verification.

## unified single-modal optical dataset manifest

Stable record identifier: `public_optical_release_v1`; previous short name: Public Optical.
Release root directory: `public optical/`; manifest paths are relative to this root.

| Field | Meaning |
|---|---|
| record_id | Stable retained image identifier, not a new numbering after export |
| split | Frozen membership; source providers' original splits were not preserved |
| image_path / label_path | RGB file and YOLO label relative paths |
| source_dataset / source_record_id | Input collection and original source-relative identifier |
| width / height | Retained image dimensions in pixels |
| file_size_bytes | Recorded image size |
| image_sha256 / label_sha256 | Expected image hash and label hash from recorded checksum inventory |
| classes | Comma-separated `fire`, `smoke`, or empty for no boxes |
| box_count / is_negative | Number of boxes; negative means zero boxes, not verified universal absence |
| split_group_id | Filename-sequence bucket used for splitting; not a certified independent scene |
| dedup_stage | Historical retention-stage label |
| license_id | Recorded source-specific identifier; not publication clearance |

YOLO text: `class_id x_center y_center width height`, normalised to image width/
height, zero-based classes `0=fire`, `1=smoke`; empty file represents no boxes.
No coordinate reinterpretation or label rewriting is performed by the exporter.

## multi-modal optical–thermal paired dataset manifest

Stable record identifier: `paired_rgbt_v1`; previous short name: Paired RGB-T.
Release root directory: `paired_RGBT/`; manifest paths are relative to this root.

| Field | Meaning |
|---|---|
| sample_id | Frozen paired identity, including domain; may contain `:` as an ID value |
| split / domain | Frozen split; `real` or `synthetic` |
| experiment / scene | Acquisition/simulation group; scene may be unknown |
| split_group_id | `domain:experiment`; experiment-disjoint, not scene-disjoint |
| optic_path / thermal_path | Retained optical and processed/registered thermal views |
| source_label_path | Original source GT, preserved bytes; not necessarily clipped training targets |
| training_optic_label_path / training_thermal_label_path | Paths of the actual frozen common derived targets after extracting the private ZIP parts |
| optic_sha256 / thermal_sha256 / source_label_sha256 | Recorded hashes from original paired manifest |
| training_label_sha256 | Private-transfer manifest: actual frozen canonical label byte hash, checked against the original training artifact; blank in older metadata-only previews |
| optic_width / optic_height / thermal_width / thermal_height | Retained view dimensions, not raw sensor dimensions |
| source_fire_boxes / source_smoke_boxes | Source GT counts, not a new audit of derived labels |
| source_label_basis | Original manifest field; `optic` does not by itself establish manual annotation |
| annotation_provenance | Conservative domain-level note; row-level review evidence still needs publication export |

The same source/derived distinction applies to all views. For real source boxes
extending beyond the visible frame, benchmark targets were clipped to the visible
intersection. Source boxes remain unchanged. Synthetic annotations were model
assisted; do not describe all labels as independently human-drawn ground truth.

## Other records

- `summary.json`: counts recomputed from exported manifest; source counts labelled. Its `payload_files_verified_now: false` is preserved from the earlier metadata-only export, not the status of the completed private ZIP transfer; see the separate private-transfer verification record.
- `source_*`: selected historical metadata; historical validation is not a new audit.
- `build_provenance.json`: input metadata hashes, redaction notes and export scope.
- `metadata_preview_build_provenance.json`: preserved earlier paired metadata-export receipt before canonical training hashes were added.
- `private_transfer.json`: private-transfer scope, original/transfer manifest hashes and canonical-label provenance; not public-release clearance.
- `splits/*.txt`: one frozen sample ID per line; not paths or newly sampled splits.
- `source_rights_review.csv`: `PENDING` is unresolved; recorded licence != clearance.
- `PAYLOAD_FILES.csv`: relative path, size, SHA-256 and role of every frozen payload file in the ZIP parts.

The 2026-11-09 distribution revision omits standalone checksum-list files and
the camera-registration JSON from both the Git tree and downloadable ZIP parts.
File hashes remain in the unchanged manifests and payload inventories. Archive
catalogs retain ZIP sizes and SHA-256 values. Internal calibration and earlier
verification records are preserved separately and are not uploaded again.

Retained thermal files remain processed/registered views. Removing a distributed
calibration file does not undo that processing or establish calibration for every
real capture. Reference-plane registration has residual parallax at other depths.
Use the manifest's per-view dimensions and do not register retained images again.

See [Dataset structure and metadata](DATASET_STRUCTURE_AND_METADATA.md) for the
revised Figure 6 layout, file roles and manuscript-ready Data Records wording.

`classes.json` gives the shared ID mapping. Machine-readable field allowlists are
in `schemas/`; the validator implements these fields and additional invariants
without claiming full general-purpose JSON Schema validation.
