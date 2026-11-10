# Dataset Overview Figures

Descriptive statistics of the frozen records. All train/validation/test samples
are included. These figures are not model-performance or annotation-accuracy
measurements. Existing images, labels, metadata and split assignments are unchanged.

## Figures

| Figure | Preview | Vector PDF |
|---|---|---|
| Final dataset composition | [PNG](01_final_dataset_scale.png) | [PDF](01_final_dataset_scale.pdf) |
| Retained image resolution | [PNG](02_image_resolution.png) | [PDF](02_image_resolution.pdf) |
| Fire/Smoke source-box dimensions | [PNG](03_bounding_box_size.png) | [PDF](03_bounding_box_size.pdf) |
| Source versus canonical relative area (supplement) | [PNG](S1_box_area_source_vs_training.png) | [PDF](S1_box_area_source_vs_training.pdf) |

## Definitions and Counts

| Annotation basis | Fire boxes | Smoke boxes | Median Fire area (%) | Median Smoke area (%) |
|---|---:|---:|---:|---:|
| Single-modal optical | 67,269 | 45,010 | 1.409 | 17.288 |
| Paired source | 49,361 | 32,363 | 0.581 | 3.364 |
| Paired canonical training | 49,361 | 32,363 | 0.581 | 3.355 |

Median area is a percentage of image area, not pixel area, segmentation coverage
or a performance metric. The main box-size figure uses original source annotations.
The supplementary figure separates canonical clipped training targets.

The optical record has 86,563 images. The paired record has 35,859 pairs and
71,718 image views. Do not add an image count and a pair count as if they were
the same unit. Both modality label copies contain common canonical targets;
count these once per pair for object statistics.

All 158,281 retained image dimensions were checked against file headers with
EXIF orientation. Eight optical JPEGs require width-height interchange under
EXIF orientation. All metadata dimensions then match; no file was rewritten.
Every consumed label file (194,140 files including paired source and both
canonical modality copies) passed its recorded SHA-256. All 25 ZIP parts passed
their catalog SHA-256. This does not replace semantic label-quality review.

Under an explicit 1e-6 normalised-coordinate tolerance, 8,916 original paired
source boxes extend outside the frame. Canonical paired training targets have
zero such boxes. This newly specified counter is not interchangeable with older
processing counters that used different definitions/tolerances. No annotation
was clipped or filtered for these descriptive source-box figures.

## Underlying Tables

- [Sample composition](statistics/sample_counts.csv)
- [Exact retained resolutions](statistics/image_resolutions.csv)
- [Resolution summaries](statistics/resolution_summary.json)
- [Box counts and area quantiles](statistics/bounding_box_summary.csv)
- [Source width-height bins](statistics/box_width_height_bins.csv)
- [Relative-area bins](statistics/box_area_bins.csv)
- [EXIF orientation audit](statistics/image_orientation_audit.csv)
- [Full definitions and audit totals](statistics/overview_statistics.json)

## Captions

### 01_final_dataset_scale

Final dataset composition. (a) The unified single-modal optical dataset contains 86,563 images from four retained source collections. (b) The multi-modal optical-thermal paired dataset contains 35,859 pairs from real and Unity-synthetic acquisitions. Colours distinguish the frozen training, validation and test partitions. Counts in (a) are images; counts in (b) are pairs, with two retained image views per pair.

### 02_image_resolution

Resolution distributions of retained image files: (a) single-modal optical images, (b) paired optical views and (c) paired thermal views. Each bubble represents an exact width-height combination, and bubble size indicates its frequency within that panel. Both axes use a logarithmic scale. The three most frequent combinations are labelled with percentages of images. JPEG EXIF orientation is respected. These are retained, processed image dimensions, not raw sensor resolutions; Unity optical and registered thermal files are both 1280 x 720 pixels.

### 03_bounding_box_size

Class-wise bounding-box size distributions for the single-modal optical dataset (a,b) and original paired source annotations (c,d). Box widths and heights are normalised by the corresponding image dimensions and expressed as percentages. All panels use the same 50 x 50 bin grid, and colour denotes the absolute number of boxes per bin on a logarithmic scale. Empty bins are white. Counts include all frozen training, validation and test samples. Original source rectangles are retained without clipping, and paired annotations are counted once rather than once per modality.

### S1_box_area_source_vs_training

Relative bounding-box area distributions for the single-modal optical annotations (a), paired source rectangles (b) and paired canonical training targets (c). Relative area is 100 times the product of YOLO-normalised width and height. Curves show the percentage of each class in 42 common logarithmically spaced area bins, and dashed lines mark class medians. Original and clipped training targets have the same class counts but may differ in geometry. Paired modality-specific copies are not counted twice.

## Reproduction

Use [the collector](../../scripts/plot_data_overview.py) and
[the renderer](../../scripts/data_overview_figures.py), following the
[usage guide](../../docs/usage_and_validation.md).
The reference environment used NumPy 2.5.2, Matplotlib 3.11.2 and Pillow 12.3.0.
Main figures and the supplement are supplied here as 600-dpi PNG and PDF.
The separate local manuscript-delivery folder also contains SVG and LZW-TIFF.
