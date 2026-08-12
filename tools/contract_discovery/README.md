# AI-assisted Contract discovery

This directory contains the deterministic interface around an optional model-assisted
proposal step. The model receives bounded evidence: one workload trace, selected
primary-source excerpts, nearby accepted Contracts, and the relevant capability-graph
neighborhood. It returns a proposal matching `proposal.schema.json`.

A proposal is never an expected answer. It must pass schema review, produce a probe,
run on the pinned Debian oracle, stabilize across repeated seeds, be minimized, and
receive human approval before becoming an accepted Contract.
