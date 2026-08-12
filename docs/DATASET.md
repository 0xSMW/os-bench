# Dataset

## Public v0.1

`dataset/public/v0.1/cases.jsonl` contains 2,660 cases generated from 266 Contracts with seed 1 and ten cases per Contract. `dataset/manifests/v0.1-public.json` records counts, domain and level distributions, Contract-corpus hash, and case-file hash.

Every row carries benchmark and schema versions, reference ID, stable case and Contract IDs, domain, level, difficulty, family, seed, generator and probe, prerequisites, transport, setup parameters, stimulus, comparison requirements, resource limits, cleanup invariants, linked workloads, provenance, and tags.

## Determinism

A case seed is the first 64 bits of SHA-256 over:

```text
benchmark_version : global_seed : contract_id : case_index
```

Each case has an independent PRNG. Adding an unrelated Contract therefore does not alter existing Contract cases. Case order is stable Contract-ID order.

Run:

```bash
osbench dataset build --profile public --seed 1 --check-determinism
```

The check generates two isolated datasets and compares SHA-256 digests.

## Expected observations

Cases do not contain hardcoded distro outcomes. They specify the reference oracle, observables, normalization, comparator, invariants, and errors. Raw expected observations can be cached after reference execution under ignored artifacts, tied to the reference lock and case digest.

## Versioning

Changing Contract semantics, generator behavior, normalization, comparator, virtual hardware, or reference artifact changes a benchmark version or manifest identity. Adding hidden seeds alone does not change the public version.
