# ICTAI ingestion incident investigation research code

Research code accompanying the manuscript A Hierarchical AI-Assisted Investigation Framework for Enterprise Data-Ingestion Incidents.

## Experiment snapshots

- `experiments/ictai-live12`: implementation for the completed 12-case comparison.
- `experiments/ictai-toolaware`: subsequent tool-aware routing snapshot.
- `experiments/ictai-knowledge-lifecycle`: later knowledge lifecycle, observability and stopping investigations.

These snapshots are separate experimental conditions. Do not replace the original comparison implementation with the latest development snapshot when reproducing reported results. SOURCE_MANIFEST.json records source file hashes.

## Offline checks

Use Python 3.10 or later. From each experiment directory run:

```text
python -m unittest discover -s tests -v
```

Read that snapshot's README_LIVE_12.md and other experiment notes for evaluation commands. Fixtures and provisional labels are synthetic. Offline tests require no model credentials. Live model calls are optional, require the user's own credentials, incur provider charges, and may produce different proposals and latency.

## Evidence and limits

Summary and manifest files retain recorded experiment outcomes. Raw model responses and detailed execution logs are omitted from this initial release candidate pending separate review. The live comparison matched 10/12 provisional labels in all arms and averaged four tool attempts per case. These are controlled development outcomes, not production accuracy or measured human time savings.

## Release status

Repository: https://github.com/kishor-tatavarty/AI-assisted-framework-EDI- . A distribution license has not yet been selected. This package contains no manuscript or practitioner review documents. Local credential files and environment folders are excluded.
