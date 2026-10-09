# DiffEHR Contract Schema

The implementation lives in `src/diffehr/core/schema.py`.

## Required Fields

Each JSON contract must include:

- `id`
- `title`
- `domain`
- `task`
- `contract_type`
- `allowed_decisions`
- `base_patient`
- `variant_patient`
- `expected`

The compact v0.2 format supports one base chart and one paired variant chart. Multiple variants can be represented as multiple contracts sharing a base scenario.

## Contract Categories

`contract_type` must be one of:

- `clinical_sensitivity`
- `nonclinical_invariance`
- `temporal_validity`

The expected behavioral relation is encoded in `expected.relation`:

- `flip`: the task-relevant decision should change.
- `same`: the task-relevant decision should remain invariable.

Aliases such as `must_flip` and `must_remain_invariable` are accepted and normalized.

## Patient Records

Each patient record has:

- `id`
- `as_of`, the decision index date,
- `attributes`, synthetic demographics/administrative fields,
- `record`, a list of dated synthetic chart items.

Record item IDs must be unique within each chart. Required citation IDs must refer to existing record items.

## Optional Research Metadata

The schema also supports:

- `mutation`: changed fields and clinical intent,
- `provenance`: source, review status, and references,
- `safety_critical_assertions`,
- `known_ambiguities`,
- `known_limitations`,
- `temporal_constraints`.

Existing contracts default to synthetic unreviewed provenance unless explicitly upgraded. This preserves backward compatibility while allowing stricter future packs.

## Validation Behavior

The loader rejects:

- unknown top-level fields,
- missing required fields,
- invalid enum values,
- duplicate allowed decisions,
- invalid ISO dates,
- required citations absent from the relevant chart,
- contradictory `same` or `flip` expectations,
- bad FHIR JSON objects when optional FHIR resources are present,
- FHIR Bundles with unsupported `resourceType`, duplicate `(resourceType, id)` pairs, `subject.reference` values of the form `Patient/x` that do not resolve to a Patient in the bundle, or a Patient id that differs from the chart id.

All 120 shipped contracts embed a FHIR R4 Bundle on both charts. Loader errors name the file, and JSON syntax errors include line and column.

Dataset-level validation additionally checks `examples/manifest.json` when present.

## Counterfactual Integrity

`diffehr.dataset.summarize_counterfactual_differences` compares base and variant records and labels the observed difference as:

- `none`,
- `single_factor`,
- `multifactor_or_dependent_representation`.

This is a structural check. It does not determine clinical validity by itself.
