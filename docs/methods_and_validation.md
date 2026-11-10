# Methods and validation notes

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

## multi-modal optical–thermal paired dataset: real/synthetic construction

The frozen release combines 66 real experiments and 21 Unity experiments.
Domain+experiment grouping, seed 20261025, retains prior real membership and
prevents experiment overlap, not scene overlap. Exact paired manifest SHA-256:
`8f10fb98b629b6ce04be3945efaac55b288cba57500664591af2b56e20ae97a7`.

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

Required additions: acquisition/sensor/Unity versions, inclusion/exclusion logic,
annotation tools/models and review coverage, calibration/registration validation,
and stratified manual label-quality review. The completed byte-integrity checks
do not establish semantic annotation accuracy.
No new annotation quality statistics have been invented.

## Benchmark use

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
