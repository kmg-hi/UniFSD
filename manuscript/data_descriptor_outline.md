# Data Descriptor working outline - not submission-ready

## Working title

Public optical and paired optical-thermal fire and smoke image datasets

Scope decision pending: one descriptor for both related records versus separate
descriptors. Explain added curation/provenance value and overlap with prior work.

## Authors and affiliations

[AUTHOR INPUT REQUIRED: names, affiliations, ORCIDs, corresponding contact,
approval of inclusion/order. Do not infer these from file ownership.]

## Abstract - factual draft for author revision

This resource comprises a curated optical image collection and a paired optical
and registered thermal collection for fire and smoke detection. The optical
collection contains 86,563 images retained from four public sources with unified
class identifiers and grouped dataset splits. The paired collection contains
35,859 samples from real recordings and Unity simulations, with optical and
thermal views associated with common detection targets. Documentation separates
source annotations from derived training targets and records modality, domain,
experiment and split membership. Relevant limitations include model-assisted
synthetic annotations, reference-plane thermal registration and the absence of
smoke annotations in the real held-out test subset.

This draft does not assert that data are already public or legally cleared.

## Background & Summary

- Motivate consistent fire/smoke definitions and modality/domain-aware reuse.
- Distinguish the unified single-modal optical dataset and the multi-modal optical–thermal paired dataset; these retain the stable record identifiers `public_optical_release_v1` and `paired_rgbt_v1`.
- Their release root folders are `public optical/` and `paired_RGBT/`, respectively; record identifiers are not folder names.
- Cite original datasets, their versions, related publications and prior overlap.
- Explain compilation/curation value without unsupported priority claims.

## Methods

1. Input data: exact source versions, acquisition dates and inclusion criteria.
2. Real capture: hardware, scene protocols, sampling, permissions and ethics.
3. Synthetic generation: Unity/project/assets/parameters and rendered modalities.
4. Annotation: classes, tools/models, annotator roles, review and uncertainty.
5. Registration: transform, reference plane, retained sizes and residual parallax.
6. Curation: source priority, duplicate thresholds, remapping and exclusions.
7. Frozen splits: grouping, seeds, source/derived GT and leakage checks.

Use `docs/methods_and_validation.md`; missing acquisition/review details require
author evidence, not prose invention. Describe the true performed pipeline.

## Data Records

[DATA DOI/VERSION REQUIRED] Describe file structure, formats, dictionaries,
checksums, relationships and licences. Keep dataset statistics in the optional
overview, not as a substitute for file documentation.

## Data Overview - optional

At most a compact dataset/modality/domain/split table and a small representative
example figure after rights/privacy review. Clearly distinguish images from pairs.

## Technical Validation

Document actual integrity, annotation and registration checks. Existing held-out
baselines may illustrate data usability with the correct versions and limitations;
do not claim model superiority proves data quality or causally isolates fusion.
Link saved metrics and evaluator/operating-point definitions, not validation as test.

## Usage Notes

Explain source-vs-derived GT, modality views, non-radiometric thermal data,
experiment-not-scene separation, synthetic annotation provenance and absent
real-test Smoke GT. Note unresolved cross-release overlap checks.

## Data Availability / Code Availability

Complete the separate templates only after records and code versions exist.

## References

[AUTHOR INPUT] Original dataset records and papers, acquisition/annotation tools,
third-party algorithms and specific final data/software releases.

## Author Contributions / Funding / Competing Interests / Ethics

[AUTHOR INPUT] Include actual roles, support, interests and relevant institutional
determinations. Disclose AI-assisted annotation/code/writing as applicable; an LLM
is not an author. Never manufacture consent, ethics approval or independence.
