from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import copy
from pathlib import Path
from typing import Any, Iterable

import jsonschema

from .constants import LEVELS
from .paths import repo_root
from .util import read_json, read_yaml, sha256_tree


@dataclass(frozen=True)
class ContractIssue:
    path: str
    message: str


@dataclass
class ContractReport:
    contracts: list[dict[str, Any]]
    issues: list[ContractIssue]

    @property
    def valid(self) -> bool:
        return not self.issues

    def stats(self) -> dict[str, Any]:
        by_level = {level: 0 for level in LEVELS}
        by_domain: dict[str, int] = {}
        by_transport: dict[str, int] = {}
        for contract in self.contracts:
            level = str(contract["level"])
            domain = str(contract["domain"])
            transport = str(contract.get("transport", "none"))
            by_level[level] = by_level.get(level, 0) + 1
            by_domain[domain] = by_domain.get(domain, 0) + 1
            by_transport[transport] = by_transport.get(transport, 0) + 1
        return {
            "contracts": len(self.contracts),
            "by_level": by_level,
            "by_domain": dict(sorted(by_domain.items())),
            "by_transport": dict(sorted(by_transport.items())),
            "corpus_sha256": contract_corpus_sha256(),
        }


def contract_files(root: Path | None = None) -> list[Path]:
    base = (root or repo_root()) / "contracts"
    return sorted(
        path
        for path in base.rglob("*.yaml")
        if "schema" not in path.relative_to(base).parts
    )


def _load_contracts_uncached(root: Path | None = None) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for path in contract_files(root):
        value = read_yaml(path)
        if not isinstance(value, dict):
            raise TypeError(f"Contract {path} must be a mapping")
        contracts.append(value)
    return contracts


@lru_cache(maxsize=1)
def _default_contracts_cached() -> tuple[dict[str, Any], ...]:
    return tuple(_load_contracts_uncached(None))


def load_contracts(root: Path | None = None) -> list[dict[str, Any]]:
    if root is None:
        return copy.deepcopy(list(_default_contracts_cached()))
    return _load_contracts_uncached(root)


def contracts_by_id(
    contracts: Iterable[dict[str, Any]] | Path | None = None,
) -> dict[str, dict[str, Any]]:
    if isinstance(contracts, Path):
        items = load_contracts(contracts)
    elif contracts is None:
        items = load_contracts()
    else:
        items = list(contracts)
    return {str(contract["id"]): contract for contract in items}


def contract_corpus_sha256(root: Path | None = None) -> str:
    return sha256_tree((root or repo_root()) / "contracts", exclude=("schema",))


def _cycle_nodes(contracts: list[dict[str, Any]]) -> list[str]:
    dependencies = {
        str(contract["id"]): [str(item) for item in contract.get("prerequisites", [])]
        for contract in contracts
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visited:
            return None
        if node in visiting:
            index = stack.index(node)
            return stack[index:] + [node]
        visiting.add(node)
        stack.append(node)
        for dependency in dependencies.get(node, []):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(dependencies):
        cycle = visit(node)
        if cycle:
            return cycle
    return []


def _validate_contracts_uncached(root: Path | None = None) -> ContractReport:
    root = root or repo_root()
    schema = read_json(root / "contracts/schema/contract.schema.json")
    validator = jsonschema.Draft202012Validator(schema)
    issues: list[ContractIssue] = []
    contracts: list[dict[str, Any]] = []
    identifiers: dict[str, Path] = {}

    for path in contract_files(root):
        try:
            value = read_yaml(path)
        except Exception as exc:
            issues.append(ContractIssue(str(path), f"YAML parse failure: {exc}"))
            continue
        if not isinstance(value, dict):
            issues.append(ContractIssue(str(path), "Contract document is not a mapping"))
            continue
        schema_errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if schema_errors:
            for error in schema_errors:
                location = ".".join(str(item) for item in error.path) or "<root>"
                issues.append(ContractIssue(str(path), f"schema {location}: {error.message}"))
            continue
        identifier = str(value["id"])
        if identifier in identifiers:
            issues.append(
                ContractIssue(
                    str(path),
                    f"duplicate id {identifier}; first declared in {identifiers[identifier]}",
                )
            )
        else:
            identifiers[identifier] = path
        contracts.append(value)

    known = {str(contract["id"]) for contract in contracts}
    for contract in contracts:
        identifier = str(contract["id"])
        for dependency in contract.get("prerequisites", []):
            if dependency not in known:
                issues.append(ContractIssue(identifier, f"unknown prerequisite: {dependency}"))
            if dependency == identifier:
                issues.append(ContractIssue(identifier, "Contract cannot depend on itself"))
        for other in contract.get("orthogonal_with", []):
            if other not in known:
                issues.append(ContractIssue(identifier, f"unknown orthogonal Contract: {other}"))
            if other == identifier:
                issues.append(ContractIssue(identifier, "Contract cannot be orthogonal with itself"))
        normalizers = contract.get("normalization", [])
        if "none" in normalizers and len(normalizers) > 1:
            issues.append(ContractIssue(identifier, "normalization 'none' cannot be combined"))

    if not issues:
        cycle = _cycle_nodes(contracts)
        if cycle:
            issues.append(ContractIssue("capability_graph", "cycle: " + " -> ".join(cycle)))

    return ContractReport(contracts=contracts, issues=issues)


@lru_cache(maxsize=1)
def _validate_default_cached() -> ContractReport:
    return _validate_contracts_uncached(None)


def validate_contracts(root: Path | None = None) -> ContractReport:
    report = _validate_default_cached() if root is None else _validate_contracts_uncached(root)
    return ContractReport(contracts=copy.deepcopy(report.contracts), issues=list(report.issues))
