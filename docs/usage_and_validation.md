# Download, Validation and Figure Reproduction

## Download and Extraction

Use the dataset attachments linked from the root README. Download the exact ZIP
filenames in the relevant archive catalog, including the revised first part.
Extract into an empty parent directory. The ZIP parts are independently readable
archives and must not be concatenated.

The Git repository contains metadata and split files, not the full image payload.
Metadata validation can run before downloading images. Full payload verification
requires the corresponding image and label directories.

## Metadata Validation

From the repository root, with Python 3.10 or later:

```bash
python -B -m unittest discover -s tests -v
python -B scripts/validate_release.py --mode scaffold
python -B scripts/validate_release.py --mode metadata
```

These checks use only the Python standard library. They validate the supported
release layout, manifest fields and hashes, counts, group membership, exact-content
hash split separation, original source manifest pins and split identifier order.
No dataset is generated, downloaded, relabelled or resplit.

If the extracted roots are inside a different parent directory:

```bash
python -B scripts/validate_release.py --mode metadata --deposit path/to/extracted
```

After extraction, check every image, source label and canonical training label:

```bash
python -B scripts/validate_release.py --mode metadata --deposit path/to/extracted --verify-files
```

Paths are relative to each dataset root. Quote arguments containing spaces.
Missing payloads or a changed byte hash cause a failure; no automatic repair occurs.
An optional internal metadata-checksum list is checked if present, but no such
standalone list is required or distributed.

## Descriptive Figures

The figure generator additionally needs NumPy, Matplotlib and Pillow.
It reads manifests and the original frozen YOLO label bytes. It can verify
EXIF-aware image dimensions from retained files.

```bash
python scripts/plot_data_overview.py --repo path/to/extracted --output overview --verify-image-dimensions
```

Keep the output directory outside the two dataset roots and their metadata.
The command produces statistics, publication figures and a private box-array
cache used for rendering. It does not modify the inputs.

If payloads remain in numbered ZIPs, the same tool accepts an archive catalog
directory and one or more directories containing the listed parts:

```bash
python scripts/plot_data_overview.py --repo . --output overview --catalog-directory catalogs --archive-directory original_parts --archive-directory revised_parts --verify-image-dimensions
```

Both datasets' current catalogs must be present. Archive sizes and SHA-256 are
checked by default. Every consumed label file is also checked against its
manifest hash. Image-size validation reads headers and EXIF orientation; it is not
a fresh pixel-quality, privacy or semantic-annotation audit.

The overview counts paired canonical targets once per pair. It does not double
the object count for two identical modality-specific label copies.
Original source-box counts are reported separately from derived training targets.
All existing train, validation and test samples contribute to these descriptive
figures; they are not held-out model-performance results.

## Scope and Publication Status

Tests and schemas are part of the validation tools. They do not depend on
manuscript drafts, authoring templates, private uploader scripts or duplicate
README drafts.

`--mode publish` performs additional read-only checks of the preserved
publication/rights records. It does not publish to GitHub or change permissions.
It currently remains blocked by unresolved author/institutional reviews.
Removing preparation documents does not resolve those reviews.
