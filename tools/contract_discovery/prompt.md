# OSBench Contract Discovery Prompt

You are proposing one behavioral OSBench Contract from bounded evidence. Treat the pinned Debian oracle as authoritative for distro-specific behavior. Describe externally observable semantics, never internal implementation requirements.

Input includes a workload trace, relevant primary documentation, nearby accepted Contracts, and one or more oracle observations. Return exactly one JSON object conforming to `proposal.schema.json`.

The proposal must:

- identify one stable abstraction and operation;
- list only prerequisites demonstrated by dependency evidence;
- state success invariants, error conditions, state transitions, cleanup and resource invariants;
- declare legal nondeterminism explicitly;
- identify orthogonal dimensions that should be composed in hidden cases;
- propose a deterministic generator and minimal probe;
- preserve provenance for every claim;
- put unresolved behavior in `uncertainty.open_questions`;
- remain in `proposed` state until a real probe has executed on the pinned reference.

Never invent expected output, errno, timing bounds, package versions, hashes, or paths. Mark unsupported conclusions as open questions.
