# Methods and validation notes

This guide incorporates the author-supplied manuscript v2 reviewed on
13 November 2026. The [figure gallery](../figures/manuscript_v2/README.md)
preserves its illustrations, while manifests, canonical labels and prior audit
records define the frozen data. Manuscript descriptions are not a new audit of
every acquisition, manual review decision or calibration measurement.

## unified single-modal optical dataset: input and curation

Current retained release: 86,563 RGB images from FASDD_CV (66,480), D-Fire (6,288),
CQU (6,244), Roboflow_FireSmoke (7,551). DFS is excluded. Do not reuse the obsolete
five-source 94,317-image description.

Historical curation combined internal duplicate stages and cross-source screening,
prioritising FASDD_CV, D-Fire, CQU, then Roboflow. The original configuration is
exported as evidence; a complete portable implementation is not yet included.
Splits use 5,845 filename-sequence groups, numeric buckets of 100, seed 20260924.
Group non-overlap does not prove complete semantic duplicate removal or scene
independence. Provider splits were not kept.

Output IDs are `0=fire`, `1=smoke`. D-Fire's source IDs were swapped; Roboflow's
`other` class was removed and smoke remapped from 2 to 1. Report the effects and
limitations of these changes. No exhaustive semantic content cleaning is claimed.

### Four-stage matching and source priority

The retained configuration and manuscript describe:

1. SHA-256 equality of complete image-file bytes.
2. SHA-256 equality of EXIF-oriented RGB pixel arrays with image dimensions.
3. Equality of either a 64x64 grayscale digest or a 32x32 RGB digest after
   normalization. This is an OR criterion, not simultaneous equality of both.
4. Joint perceptual matching with maximum Hamming distances 4 for pHash,
   8 for centre pHash, 10 for dHash and 10 for aHash, plus maximum absolute
   logarithmic aspect-ratio difference 0.25. The centre crop retains 88% of
   width and height. All five conditions must hold for an optical Stage 4 match.

Cross-source integration prioritizes FASDD_CV, then D-Fire, CQU and NEWFire2 v1
(the metadata source identifier is `Roboflow_FireSmoke`). A match removes an
incoming sample rather than the earlier retained source. The checked optical
counts are:

| Source | Raw | S1 | S2 | S3 | S4 | Cross-source removed | Final |
|---|---:|---:|---:|---:|---:|---:|---:|
| FASDD_CV | 95,314 | 150 | 20 | 46 | 28,618 | 0 | 66,480 |
| D-Fire | 21,527 | 0 | 0 | 0 | 9,081 | 6,158 | 6,288 |
| CQU | 11,021 | 1,169 | 0 | 10 | 3,367 | 231 | 6,244 |
| NEWFire2 v1 | 8,443 | 0 | 0 | 0 | 886 | 6 | 7,551 |
| Total | 136,305 | 1,319 | 20 | 56 | 41,952 | 6,395 | 86,563 |

The six NEWFire2 cross-source removals are required for the row and total to
reconcile; a dash in that cell of manuscript Table 3 is not a zero in the
underlying records. No additional, separately quantified public optical
relevance-review removal count is asserted by this table.

## multi-modal optical–thermal paired dataset: real/synthetic construction

The frozen release combines 66 real experiments and 21 Unity experiments.
Domain+experiment grouping, seed 20261025, retains prior real membership and
prevents experiment overlap, not scene overlap. Exact paired manifest SHA-256:
`8f10fb98b629b6ce04be3945efaac55b288cba57500664591af2b56e20ae97a7`.

The manuscript describes FireGuard optical, thermal and LiDAR acquisition,
camera intrinsic calibration, camera-LiDAR extrinsic calibration and thermal
registration. LiDAR is an intermediate geometric reference and is not included
in the released record. The 21 synthetic experiment groups span three virtual
environments: an underground parking lot, a logistics warehouse and a
reuse-battery storage facility; experiment count and environment count are
different quantities.

Paired duplicate removal requires matches in both corresponding modalities;
an optical-only or thermal-only match is insufficient. The manuscript describes
real pair-level perceptual matching and strict zero-distance synthetic hash
checking. Do not substitute the public optical Stage 4 tolerances for an
unverified real-pair configuration.

The synthetic input count is 21,000 pairs. The 379 relevance/annotation-eligibility
exclusions comprise 206 reviewed-empty and 173 unlabeled pairs, leaving 20,621.
Missing labels are not proof of absent Fire/Smoke, and these exclusions must not
be relabeled as cross-source duplicate removals or all-manual review. Final real
membership is 15,238 pairs; historical intermediate real curation counts alone
do not establish the scope of expert review.

Unity optical frames are 1280x720; raw thermal frames 640x480. Released thermal
views were projected into optical coordinates at a 5.317814839 m reference depth.
The static transform/homography is valid at that plane; other depths retain
parallax. These processed thermal colour views are not calibrated temperature
measurements. Real frame sizes vary from Unity; use manifest dimensions.

Original GT is preserved. The learned benchmark uses common visible-intersection
derived labels for optical/thermal views. Original reports flag 8,905 overflowing
source boxes; later geometry processing recorded 9,064 changed boxes in 7,421
frames, including small numerical boundary cases. These are different counters,
not evidence that all boxes required manual relabelling. Exact frozen source
and canonical label bytes are both included, with their separate manifest hashes.
Do not reconstruct or substitute the canonical targets when using this record.

### Annotation and temporal evidence scope

The manuscript describes initial manual labels, teacher/student model assistance
and iterative expert corrections. Preserve this model-assisted provenance.
The diagrams and file hashes do not independently establish exhaustive human
review, missing-object recall or inter-annotator agreement.

The supplied timing report analyzes a separate Fusion_v2 proxy cohort, not the
frozen 15,238 released real pairs. Its 45 experiments contain 250,673 analyzed
pairs with mean absolute header-timestamp difference 8.508750 ms and population
standard deviation 5.490104 ms. The inspected proxy extractor uses offline
nearest header timestamps, a <=20-ms acceptance rule, earlier-frame tie-breaking
and permitted thermal-frame reuse. Its linkage to each released pair is not
established. Neither 8.51 +/- 5.49 ms nor the proxy acceptance rule should be
presented as independently verified release-wide synchronization accuracy.
Message timestamps do not establish simultaneous physical exposure, and
spatial registration does not by itself correct time offsets.

The supplied calibration illustrations are manuscript observations; this
documentation update does not recompute camera or registration RMSE. Metric
units, sample coverage and any pixel-to-millimetre conversion require the
underlying calibration/landmark records before interpreting such results as
release-wide geometric accuracy.

## Evidence versus checks performed by this preparation

Preparation checks parse full metadata, preserve IDs/order/splits, enforce safe
relative paths, validate expected counts and SHA formats, check group/content hash
overlap, and hash the exported metadata. The normal metadata validator does not
open every image, assess annotation correctness, measure registration accuracy,
or validate privacy. Historical source validation records retain that distinction.

The separately supplied descriptive figures used a fresh read-only scan of all
25 catalog-pinned ZIP parts, 194,140 label files and 158,281 retained image
headers. Label hashes and archive hashes matched. Eight JPEGs require EXIF-aware
width-height interchange; all retained dimensions then agree with the manifests.
Figure definitions and aggregate tables are in
[the overview figure notes](../figures/data_overview/README.md).

Still needed for a complete reproducibility/quality audit: actual acquisition
and Unity versions, execution linkage to released pair IDs, annotation model
settings and review coverage, raw calibration/registration validation records,
and stratified manual label-quality review. The manuscript adds workflow
descriptions; completed byte-integrity checks do not establish semantic accuracy.
No new annotation quality statistics have been invented.

## Benchmark use

The manuscript's completed-test rows, model variants and metric conventions are
provided in [the benchmark guide](benchmarks.md), alongside selected-case IDs.

Existing held-out baselines may support technical validation if linked to exact
data/GT/model versions and evaluator settings. Do not retrain to prepare this repo.
Optic-only/thermal-only baselines belong to the paired release, not the separate
Public Optical test. Model capacity, losses, optimisation, augmentation and
precision differ. P/R operating points also differ; native COCO AR is not the
reported conventional recall. `All` in prior comparisons is a class macro average,
not class-agnostic matching or an average across domains. No causal fusion gain
or common fixed-threshold comparison is established.

Real test has 2,264 Fire and **zero Smoke** GT boxes; test Smoke GT (2,298) comes
only from synthetic data. Do not claim real-Smoke held-out generalisation.
The two releases have not been jointly checked for cross-release content overlap.
