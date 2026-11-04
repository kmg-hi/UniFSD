# unified single-modal optical dataset

Dataset card draft. Stable record identifier: `public_optical_release_v1`.
Release root directory: `public optical/` (contains a literal space).
Previous short name: Public Optical v1. The name change does not alter membership or splits.

- Unit: one RGB image and YOLO text labels; 0 Fire, 1 Smoke.
- Size: 86,563 images; 112,279 boxes (Fire 67,269; Smoke 45,010).
- 41,364 retained images have zero labelled boxes; this is not a guarantee of
  absence of every unlabelled fire/smoke phenomenon.
- Train/val/test: 68,475 / 8,714 / 9,374; test GT Fire 5,485 / Smoke 4,307.
- Sources: FASDD_CV, D-Fire, CQU, Roboflow_FireSmoke; source-specific rights.
- Source provenance and historical licence claims are exported, not re-certified.
- Deduplication and filename-group splitting reduce leakage but do not establish
  independent scenes or exhaustive semantic de-duplication.
- Intended reuse: detection-data curation and clearly scoped RGB baselines.
- Not a paired thermal dataset and not the paired-release optic-only benchmark.
- Candidate-release origin, publication version/DOI/licence: not finalised.
- Access now: author-approved PRIVATE ZIP transfer in progress; not a public release.
- Annotation accuracy, sensitive-image review, upstream component rights and
  representativeness require documented checks before release.
