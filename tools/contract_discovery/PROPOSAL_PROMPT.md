# OSBench Contract proposal prompt

You are proposing one behavioral OS Contract. Use only the supplied trace, primary
source excerpts, nearby accepted Contracts, and capability-graph neighborhood.
Describe an externally observable contract, its prerequisites, invariants, valid
state transitions, failure and cleanup behavior, legal nondeterminism, composition
surfaces, probe strategy, and provenance. Keep implementation details out of the
success condition. State every uncertainty. Output JSON conforming exactly to
`proposal.schema.json`. Set `status` to `proposed` and every oracle-dependent review
check to false. Do not invent expected observations; those are established only by
executing the generated probe on the pinned reference.
