# DiffEHR Metrics

This document defines the metrics implemented in `src/diffehr/metrics/computation.py`.

## Unit Of Analysis

The primary unit is one contract. Each contract contains a base case and a variant case. Some metrics also aggregate over contract sides or cited evidence IDs.

Invalid contracts are rejected before scoring. A model invocation error currently fails the evaluation command rather than being counted as a successful clinical output. Evaluation JSON includes the DiffEHR version, Python version, adapter class, contract IDs, dataset version, dataset SHA-256 fingerprint, run timestamp, bootstrap seed, and whether the adapter is external.

## Contract Compliance

Contract compliance is the fraction of contracts that pass all deterministic assertions:

```text
contract_pass_rate = passed_contracts / evaluated_contracts
```

A contract passes only if:

- base decision equals expected base decision,
- variant decision equals expected variant decision,
- the expected relation holds,
- required citations are present on both sides,
- no cited evidence is dated after the decision index.

## Decisive Sensitivity Score

DSS measures expected flips on decisive pairs:

```text
DSS = decisive_successes / decisive_contracts
```

`decisive_successes` counts contracts with relation `flip` where:

- base and variant decisions are both correct, and
- the observed decisions differ.

If there are no decisive contracts, DSS is reported as `0.0` because there is no supported denominator.

## Invariance Violation Rate

IVR measures unexpected flips on invariant pairs:

```text
IVR = invariance_violations / invariant_contracts
```

An invariance violation occurs when a contract with relation `same` produces different observed decisions between base and variant.

If there are no invariant contracts, IVR is reported as `0.0` because no invariant-pair violation was observable.

## Evidence Citation Precision And Recall

Required evidence is defined by contract-side citation IDs.

```text
precision = |observed citations ∩ required citations| / |observed citations|
recall    = |observed citations ∩ required citations| / |required citations|
```

If both sets are empty, precision and recall are `1.0`. If required citations exist but the model provides none, precision and recall are `0.0`.

Important limitation: deterministic citation matching checks whether the model cited required record IDs. It does not prove that a natural-language rationale semantically supports every clinical claim.

## Temporal Leakage

A temporal leakage violation is a cited evidence ID whose chart date is greater than the case decision index:

```text
TLVR = future_dated_citations / observed_citations
```

A zero temporal leakage count means no leakage was detected by citation timestamps. It does not prove the model did not internally use future evidence without citing it.

## Bootstrap Confidence Intervals

DiffEHR computes deterministic percentile bootstrap intervals for IVR and DSS:

- sampling unit: contract,
- resampling: with replacement,
- default samples: 1000,
- default seed: 2025,
- interval: 2.5th to 97.5th percentile.

These intervals are conditional on this checked-in synthetic benchmark. They are not claims about a representative clinical population.

## Worked Examples

Citation example:

```text
required = {a, b}
observed = {a, x}
precision = 1 / 2 = 0.5
recall = 1 / 2 = 0.5
```

Invariant-pair example:

```text
expected relation = same
base observed = eligible
variant observed = ineligible
IVR numerator += 1
```

Temporal example:

```text
decision_t = 2025-02-15
cited evidence date = 2025-03-01
temporal leakage violation += 1
```

## Safety-Critical Failures

Safety-related expected decisions such as `contraindicated`, `unsafe`, `avoid_beta_lactam`, or `defer` are highlighted as high severity in failure reports. This is a benchmark severity rule, not a real-world clinical severity determination.
