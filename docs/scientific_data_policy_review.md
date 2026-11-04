# Scientific Data policy review

Checked 2026-10-30. Recheck at submission. These notes are not legal advice or
confirmation that the dataset is acceptable to the journal.

| Topic | Official guidance and project response |
|---|---|
| Article format | A Data Descriptor documents data creation, records, validation and reuse. Structure the manuscript accordingly; do not turn baseline model rankings into a conventional Results/Discussion paper. [Submission guidelines](https://www.nature.com/sdata/submission-guidelines) |
| Review access | First-round reviewers need practical anonymous downloads; from the second round, use a compliant public repository. [Repository guidance](https://www.nature.com/sdata/policies/repositories) |
| Preservation/licensing | Use a persistent repository. CC0/CC BY or equivalents are normally expected; SA/NC exceptions concern secondary data retaining original third-party terms. Do not remove FASDD's original terms or assume the exception guarantees acceptance. [Repository guidance](https://www.nature.com/sdata/policies/repositories) |
| Data hosting/rights | The journal does not host the dataset. Image redistribution requires rights review; a policy concerning compilation of facts is not a licence to copy images. Retain lab/institutional copies for at least five years after publication. [Data policies](https://www.nature.com/sdata/policies/data-policies) |
| Code | Previously unreported custom generation/processing code must be available. GitHub plus a DOI archive is recommended for a preserved usable version. [Editorial policies](https://www.nature.com/sdata/policies/editorial-and-publishing-policies) |

## Repository implementation decisions

These are project recommendations, not a prescribed journal folder standard:

- One companion GitHub repository for code, schemas, dictionaries and version history.
- Two separately described dataset deposits, because RGB compilation and paired
  real/synthetic acquisition have different membership, provenance and rights.
- A DOI-preserving software archive, linked to versioned data records.
- A stable submission snapshot rather than links to a changing training directory.
- Public Optical's compilation/curation contribution and related prior releases
  must be explained; editorial suitability and one-versus-two-paper scope remain open.

## Platform constraints checked

Ordinary Git warns above 50 MiB and blocks files above 100 MiB. Keep bulk media
and checkpoints outside Git. [GitHub large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

Zenodo's default record limit is 100 files / 50 GB; larger quotas can be requested.
Choose archive shards after measuring the real payload, not from sample counts.
[Zenodo file management](https://help.zenodo.org/docs/deposit/manage-files/)

GitHub releases can be archived with Zenodo; a GitHub URL alone is not the planned
data preservation record. [GitHub citation/archive documentation](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)

Keep `CITATION.cff` and `.zenodo.json` consistent: Zenodo gives `.zenodo.json`
precedence if both are present. Templates here are deliberately not active metadata.
[Zenodo metadata documentation](https://help.zenodo.org/docs/github/describe-software/)

## Source-specific warning

D-Fire's upstream README states that `PublicDataset*` images include third-party
components with original-provider terms. The old local CC0 collection entry does
not clear these components. [D-Fire upstream](https://github.com/gaia-solutions-on-demand/DFireDataset)
FASDD's locally recorded CC BY-SA terms require an exact-input/version check;
adapted contributions must retain applicable obligations, not be silently relicensed.
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
