# Olist Customer Intelligence

This site is the living engineering reference for the Olist Customer Intelligence data platform.

Its purpose is to make architecture, delivery standards, platform contracts, governance decisions and public Python APIs discoverable from one place while keeping GitHub as the source of truth.

## What this documentation demonstrates

The project treats documentation as part of platform engineering rather than as a closeout artifact. Architectural decisions are recorded in ADRs, feature work follows explicit delivery gates, public APIs carry executable documentation through docstrings, and CI validates that the documentation site can still be built.

## Documentation model

```text
Code + docstrings
      │
      ├── mkdocstrings -> API Reference
      │
Markdown docs
      ├── architecture decisions
      ├── engineering standards
      ├── feature specifications
      └── operational guidance
      │
      ▼
Material for MkDocs
      │
      ▼
GitHub Pages
```

## Current platform direction

The active DAB + Platform Contracts feature is establishing:

- isolated `dev`, `stg` and `prd` environments;
- executable dataset contracts;
- Delta table lifecycle management separated from write semantics;
- controlled schema evolution;
- governed table/column tags;
- Unity Catalog ABAC foundations for row filters and column masks;
- automated CI/CD and documentation validation.

Use the navigation to inspect the accepted requirements, design documents, ADRs and generated API reference.
