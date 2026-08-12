from __future__ import annotations

from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path
from typing import Any

from .contracts import contracts_by_id, validate_contracts
from .paths import repo_root
from .util import read_json, read_yaml, sha256_file, write_json, write_yaml


def build_graph() -> dict[str, Any]:
    report = validate_contracts()
    if not report.valid:
        raise ValueError(f"invalid Contract corpus: {report.issues[:3]}")
    nodes = {
        contract["id"]: {
            "level": contract["level"],
            "domain": contract["domain"],
            "title": contract["title"],
            "transport": contract["transport"],
            "workloads": contract.get("workloads", []),
        }
        for contract in report.contracts
    }
    edges = [
        {"from": dependency, "to": contract["id"], "type": "prerequisite"}
        for contract in report.contracts
        for dependency in contract.get("prerequisites", [])
    ]
    return {
        "schema_version": "osbench.capability_graph.v1",
        "nodes": nodes,
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"])),
    }


@lru_cache(maxsize=2)
def _adjacency(reverse: bool = False) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    contracts = contracts_by_id()
    adjacency: dict[str, list[str]] = defaultdict(list)
    for identifier, contract in contracts.items():
        for dependency in contract.get("prerequisites", []):
            source, target = (identifier, dependency) if reverse else (dependency, identifier)
            adjacency[source].append(target)
    for key in adjacency:
        adjacency[key].sort()
    return contracts, adjacency


def _closure(start: list[str], adjacency: dict[str, list[str]]) -> list[str]:
    output: set[str] = set()
    queue = deque(start)
    while queue:
        value = queue.popleft()
        if value in output:
            continue
        output.add(value)
        queue.extend(adjacency.get(value, []))
    return sorted(output)


def prerequisites(contract_id: str, transitive: bool = True) -> list[str]:
    contracts, adjacency = _adjacency(reverse=True)
    if contract_id not in contracts:
        raise KeyError(contract_id)
    direct = adjacency.get(contract_id, [])
    return _closure(direct, adjacency) if transitive else list(direct)


def unlocked_by(contract_id: str, transitive: bool = False) -> list[str]:
    contracts, adjacency = _adjacency(reverse=False)
    if contract_id not in contracts:
        raise KeyError(contract_id)
    direct = adjacency.get(contract_id, [])
    return _closure(direct, adjacency) if transitive else list(direct)


def _workload_document() -> dict[str, Any]:
    path = repo_root() / "capability_graph/workloads.yaml"
    value = read_yaml(path) if path.exists() else {}
    return value if isinstance(value, dict) else {}


def contracts_for_workload(workload: str) -> list[str]:
    workloads = _workload_document()
    item = workloads.get(workload)
    if not isinstance(item, dict):
        raise KeyError(workload)
    direct = [str(value) for value in item.get("contracts", [])]
    closure = set(direct)
    for identifier in direct:
        closure.update(prerequisites(identifier))
    return sorted(closure)


def workloads_for(contract_id: str) -> list[str]:
    if contract_id not in contracts_by_id():
        raise KeyError(contract_id)
    return sorted(
        workload
        for workload in _workload_document()
        if contract_id in contracts_for_workload(workload)
    )


def frontier(results_path: Path) -> list[str]:
    result = read_json(results_path)
    contract_results = result.get("contracts", {})
    passed = {
        identifier
        for identifier, value in contract_results.items()
        if isinstance(value, dict) and value.get("passed") is True
    }
    contracts = contracts_by_id()
    return sorted(
        identifier
        for identifier, contract in contracts.items()
        if identifier not in passed
        and all(dependency in passed for dependency in contract.get("prerequisites", []))
    )


def _topology(graph: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    indegree = {identifier: 0 for identifier in graph["nodes"]}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in graph["edges"]:
        indegree[edge["to"]] += 1
        adjacency[edge["from"]].append(edge["to"])
    roots = sorted(identifier for identifier, value in indegree.items() if value == 0)
    queue = deque(roots)
    order: list[str] = []
    while queue:
        identifier = queue.popleft()
        order.append(identifier)
        for child in sorted(adjacency.get(identifier, [])):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return len(order) == len(indegree), roots, order


def _workload_matrix() -> dict[str, Any]:
    workloads = _workload_document()
    contracts, reverse_adjacency = _adjacency(reverse=True)
    rendered: dict[str, Any] = {}
    for name, value in sorted(workloads.items()):
        direct = [str(item) for item in value.get("contracts", [])]
        closure = set(direct)
        for identifier in direct:
            if identifier not in contracts:
                raise KeyError(f"workload {name} references unknown Contract {identifier}")
            closure.update(_closure(reverse_adjacency.get(identifier, []), reverse_adjacency))
        rendered[name] = {**value, "contract_closure": sorted(closure)}
    return {"schema_version": "osbench.workload_matrix.v1", "workloads": rendered}


def write_graph_outputs() -> dict[str, Any]:
    root = repo_root()
    output_dir = root / "capability_graph"
    output_dir.mkdir(parents=True, exist_ok=True)
    graph = build_graph()
    acyclic, roots, order = _topology(graph)
    if not acyclic:
        raise ValueError("capability graph contains a cycle")

    yaml_path = output_dir / "graph.yaml"
    json_path = output_dir / "graph.json"
    dot_path = output_dir / "graph.dot"
    matrix_path = output_dir / "workload_matrix.json"
    write_yaml(yaml_path, graph)
    write_json(json_path, graph)
    write_json(matrix_path, _workload_matrix())

    lines = ["digraph osbench {", "  rankdir=LR;", "  node [shape=box,fontname=Helvetica];"]
    for identifier, metadata in sorted(graph["nodes"].items()):
        label = f"{identifier}\\n{metadata['level']}"
        lines.append(f'  "{identifier}" [label="{label}"];')
    for edge in graph["edges"]:
        lines.append(f'  "{edge["from"]}" -> "{edge["to"]}";')
    lines.append("}")
    dot_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "acyclic": acyclic,
        "roots": roots,
        "topological_order_count": len(order),
        "graph": str(yaml_path.relative_to(root)),
        "json": str(json_path.relative_to(root)),
        "dot": str(dot_path.relative_to(root)),
        "workload_matrix": str(matrix_path.relative_to(root)),
        "graph_sha256": sha256_file(yaml_path),
    }
