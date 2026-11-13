# Completed Held-Out Test Benchmarks

These are the nine model rows selected for Table 5 of the supplied v2 manuscript.
Values are fractions on a 0-1 scale, rounded to four decimal places. They agree
with the preserved original completed-test report. No training, inference or
test reevaluation was performed for this repository update.

## Unified Single-Modal Optical Dataset

The test split contains 9,374 optical images, including annotation-negative
images. Public optical and the paired record's optical-only benchmark are not
the same test dataset.

| Model | Input | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---:|---:|---:|---:|
| Faster R-CNN | Optical | 0.7293 | 0.6202 | 0.6915 | 0.3958 |
| RetinaNet | Optical | 0.7452 | 0.6024 | 0.6889 | 0.4001 |
| RT-DETR-L | Optical | 0.7371 | 0.6285 | 0.7078 | 0.4452 |
| YOLOv9-C | Optical | 0.7417 | 0.6487 | 0.7324 | 0.4784 |

## Paired Multi-Modal Optical-Thermal Dataset

All five rows use the same 3,524 test pairs: 1,524 real and 2,000 synthetic.
Single-modality rows use one view of each pair, while fusion rows use both views.

| Model | Input | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---:|---:|---:|---:|
| YOLOv9-T | Optical only | 0.8758 | 0.9116 | 0.9567 | 0.7807 |
| YOLOv9-T | Thermal only | 0.8486 | 0.9099 | 0.9345 | 0.6217 |
| YOLO11n-RGBT | Optical + thermal | 0.9147 | 0.9108 | 0.9664 | 0.8129 |
| DEYOLO-n | Optical + thermal | 0.9008 | 0.9197 | 0.9653 | 0.8101 |
| DAMSDet R50-vd | Optical + thermal | 0.8058 | 0.9676 | 0.9614 | 0.7831 |

[Machine-readable Table 5 values](../figures/manuscript_v2/table5_test_metrics.csv)
use the same fractions and rounding. Manuscript shorthand "YOLOv9" is made
explicit here: YOLOv9-C for Public optical, YOLOv9-T for the paired baselines.
ICAFusion is outside this manuscript table/figure selection; its completed
artifacts are not deleted or invalidated.

## Metric Conventions and Limitations

- These are original held-out test results, not validation scores or scores
  computed from the selected images in Figure 10.
- All-class results are Fire/Smoke class-macro metrics. They are not
  class-agnostic matching, and pooled-test AP is not an average of domain AP.
- Precision and recall follow native evaluator operating points, not a common
  confidence threshold. Faster R-CNN and RetinaNet use best-F1 confidence
  selected on test; this is descriptive, not a deployment threshold fixed on an
  independent validation set.
- DAMSDet P/R use confidence 0.25, IoU 0.50, class-aware COCO matching,
  area=all and maxDets=100, macro-averaged over classes with nonignored GT.
  Reported recall is not COCO average recall.
- Figure 10 instead displays predictions at confidence >=0.50. Display
  thresholds must not be substituted for the original full-test P/R criteria.
- Real paired test contains 2,264 Fire and zero Smoke source GT boxes. Synthetic
  test contains 3,738 Fire and 2,298 Smoke boxes. Real images can contribute
  Smoke false positives even though all scored Smoke GT is synthetic.
- Model capacity, losses, native optimizers, augmentation, precision, AP
  implementations and best-checkpoint selection differ. This is not a
  capacity-matched causal estimate of the benefit of fusion.

## Training and Hardware Summary

The manuscript reports 100 training epochs, total batch 16 for Public optical
models and total batch 32 for paired-record models. Public models used one GPU,
paired single-modality models two GPUs, and fusion models four GPUs per run.
These totals do not imply identical native optimizers or augmentation policies.

The training server has two Intel Xeon Gold 5220R CPUs at a nominal 2.20 GHz,
48 physical cores and 96 logical threads in total. The supplied system output
reports approximately 502 GiB of usable RAM, not an exact 502-GB installed-RAM
specification. Training used NVIDIA Tesla V100-SXM2 GPUs with 32 GB memory per
GPU. Acquisition hardware in Figure 2 is a separate system.

## Selected Detection Examples

[Manuscript Figure 10](../figures/manuscript_v2/Figure10.png) uses the following
previously checked examples:

| Record/domain | Sample ID | Illustrated target |
|---|---|---|
| Public optical | `POU002347` | Fire and Smoke |
| Paired real | `real:230714_5m_suppression/230714_5m_suppression_pair_00070` | Fire |
| Paired synthetic | `synthetic:warehouse_fire2_fire3_05428` | Smoke |

The paired examples were selected after a separate prediction-only comparison
on the frozen test set. At display confidence >=0.50 and class-correct IoU >=0.50,
both single-modality models miss the selected target, while the three illustrated
fusion models match it. Other displayed predictions were retained. This
purposive selection illustrates possible complementary information; it does not
summarize the frequency or direction of errors across all test objects.
