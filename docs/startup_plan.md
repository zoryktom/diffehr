# DiffEHR Startup Plan

## Product Vision

**Regression testing and safety QA for clinical AI.**

Health AI companies ship model updates. Hospitals evaluate vendors. Both sides
need evidence that the model behaves reliably in clinically meaningful edge
cases. DiffEHR turns those edge cases into executable tests.

## Open-Source Core

- contract schema
- local CLI runner
- baseline adapters
- sample oncology, cardiology, and infectious disease packs
- automated counterfactual discovery fuzzer
- reproducible reports
- contribution workflow for new packs

## Commercial Layer

- hosted evaluation dashboards
- private contract packs by specialty
- clinician-reviewed scenario libraries
- CI/CD integration for model release gates
- vendor procurement reports for hospitals
- audit trail for model behavior over time

## Initial Wedge

Start with oncology because oncology has:

- biomarker-driven decisions
- trial eligibility
- complex longitudinal records
- imaging and pathology evidence
- treatment-line timelines
- high commercial interest from pharma and health AI companies

## Buyer Personas

- health AI startup CTO
- clinical AI product lead
- hospital Chief AI Officer
- Chief Medical Information Officer
- clinical informatics evaluation team
- pharma clinical trial matching team

## First Paid Offer

**DiffEHR-Oncology Private QA Pack**

A paid service that creates 100-500 custom counterfactual contracts for a
company's oncology AI workflow, runs the customer's model against the pack, and
delivers a model-regression and failure-mode report.

## Acquisition Narrative

DiffEHR becomes valuable if it owns:

- the contract format for clinical AI counterfactual tests
- a growing library of clinician-reviewed test packs
- benchmark evidence across major models
- integration hooks for vendor model endpoints
- trust with biomedical informatics researchers

Potential acquirers include health AI evaluation companies, EHR vendors,
ambient documentation vendors, clinical trial matching companies, payer/provider
workflow platforms, and AI governance platforms.
