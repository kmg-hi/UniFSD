# multi-modal optical–thermal paired dataset

Dataset card draft. Stable record identifier: `paired_rgbt_v1`.
Release root directory: `paired_RGBT/` (case-sensitive spelling).
Previous short name: Paired RGB-T v1. The name change does not alter membership or splits.

| Split | Real pairs | Synthetic pairs | Total pairs |
|---|---:|---:|---:|
| Train | 12,190 | 16,621 | 28,811 |
| Val | 1,524 | 2,000 | 3,524 |
| Test | 1,524 | 2,000 | 3,524 |
| Total | 15,238 | 20,621 | 35,859 |

71,718 views, 66 real and 21 synthetic experiments. Source GT totals: Fire49,361,
Smoke32,363. Whole real dataset has Smoke labels (train3,035/val863), but real
test has none. Synthetic test: Fire3,738/Smoke2,298; real test: Fire2,264/Smoke0.

Optic-only, thermal-only and paired RGB-T are modality views of the same membership
and derived targets, not independently sampled datasets. Do not merge their
metrics with the separate 86,563-image Public Optical test.

Grouping is experiment-disjoint, **not scene-disjoint**. Unity thermal is processed
reference-plane-registered imagery; not radiometric temperatures or independent
raw-thermal GT. Residual parallax and model-assisted synthetic annotation limit
generalisability. A full annotation review protocol is still needed.

Source labels and common clipped training labels must both be identifiable and
kept separate. The PRIVATE transfer manifest contains actual canonical label
hashes restored from the frozen training artifact and checked against each
original hash; older metadata-only previews left these hashes blank.
Sensor/acquisition metadata, real capture rights/ethics and Unity asset
permissions remain pending. The authorised PRIVATE ZIP transfer is in progress,
not a public release.

ICAFusion's exclusion from a requested model comparison does not remove any
dataset samples, source annotations or completed experiment artefacts.
