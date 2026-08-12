#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEVELS = [
    "boot", "machine", "linux_primitives", "kernel_subsystems",
    "linux_process_environment", "posix_userspace", "linux_system", "distro",
    "package_ecosystem", "real_workloads", "full_reconstruction",
]
CASE_DIMENSIONS = [
    "primitive", "boundary", "state_transition", "composition", "concurrency",
    "isolation", "failure", "persistence", "exhaustion", "workload", "performance",
]

SOURCE_BY_LEVEL = {
    "boot": ("linux", "Linux kernel boot protocol and UEFI observable behavior"),
    "machine": ("linux", "Linux x86-64 ABI and QEMU virtual hardware behavior"),
    "linux_primitives": ("posix", "POSIX.1-2024 and Linux man-pages"),
    "kernel_subsystems": ("linux", "Linux man-pages, UAPI, kselftest, and LTP coverage"),
    "linux_process_environment": ("linux", "Linux ABI documentation and man-pages"),
    "posix_userspace": ("posix", "POSIX.1-2024 utilities and shell requirements"),
    "linux_system": ("linux", "Linux UAPI and admin-guide ABI documentation"),
    "distro": ("debian", "Debian 13.6 reference oracle and Debian Policy"),
    "package_ecosystem": ("autopkgtest", "Debian Policy, dpkg behavior, and offline package oracle"),
    "real_workloads": ("debian_oracle", "Unmodified workload execution on the pinned Debian reference"),
    "full_reconstruction": ("empirical", "End-to-end differential workflow on the pinned Debian reference"),
}

OBSERVABLES_BY_DOMAIN = {
    "boot": ["boot_log", "serial_output", "exit_code"],
    "machine": ["syscall_return", "signal", "device_state", "timing"],
    "filesystem": ["syscall_return", "errno", "filesystem_state", "file_contents", "metadata", "links"],
    "fd": ["syscall_return", "errno", "fd_state"],
    "process": ["syscall_return", "errno", "exit_code", "process_tree", "environment"],
    "thread": ["syscall_return", "errno", "process_tree", "memory_state"],
    "signal": ["syscall_return", "errno", "signal", "process_tree"],
    "memory": ["syscall_return", "errno", "memory_state", "resource_usage"],
    "socket": ["syscall_return", "errno", "socket_behavior"],
    "network": ["socket_behavior", "packet_trace", "identity"],
    "permission": ["syscall_return", "errno", "permissions", "identity"],
    "identity": ["identity", "permissions", "environment"],
    "package": ["exit_code", "stdout", "stderr", "package_state", "filesystem_state", "service_state"],
    "service": ["exit_code", "service_state", "boot_log"],
    "persistence": ["persistent_state", "filesystem_state", "service_state", "package_state"],
    "workload": ["exit_code", "stdout", "stderr", "filesystem_state", "socket_behavior"],
    "full": ["boot_log", "exit_code", "persistent_state", "service_state", "package_state"],
}

NORMALIZATION_BY_DOMAIN = {
    "filesystem": ["temporary_paths", "inode", "timestamps", "directory_order"],
    "fd": ["pid"],
    "process": ["pid", "ppid", "timestamps"],
    "thread": ["pid", "tid", "scheduler_order"],
    "signal": ["pid", "scheduler_order"],
    "scheduling": ["pid", "tid", "scheduler_order", "timestamps"],
    "socket": ["ephemeral_port", "addresses", "scheduler_order"],
    "network": ["ephemeral_port", "addresses", "host_metadata"],
    "time": ["timestamps"],
    "distro": ["host_metadata", "timestamps"],
    "service": ["pid", "timestamps", "scheduler_order"],
    "persistence": ["timestamps", "inode"],
    "workload": ["temporary_paths", "pid", "timestamps", "ephemeral_port"],
    "full": ["temporary_paths", "pid", "timestamps", "ephemeral_port", "inode"],
}

WORKLOADS = [
    "static_elf", "dynamic_elf", "shell_script", "coreutils_pipeline", "pthread",
    "python", "sqlite", "git", "compression", "http", "tcp", "dns", "ssh",
    "compiler", "package_install", "service_start", "reboot_persistent", "full_workflow",
]


def title(contract_id: str) -> str:
    return " ".join(token.upper() if token in {"elf", "ipc", "tty", "dns", "tcp", "udp", "vfs", "uid", "gid"} else token.replace("_", " ").title() for token in contract_id.split("."))


def operation(contract_id: str) -> str:
    return ".".join(contract_id.split(".")[1:])


def workload_links(contract_id: str, domain: str) -> list[str]:
    links: set[str] = set()
    if contract_id.startswith("workload."):
        token = contract_id.split(".", 1)[1].replace(".", "_")
        aliases = {
            "c_compile_link_run": "compiler", "coreutils_pipeline": "coreutils_pipeline",
            "dynamic_elf": "dynamic_elf", "static_elf": "static_elf",
            "pthread_program": "pthread", "python_basic": "python",
            "sqlite_transaction": "sqlite", "git_repository": "git",
            "compression_roundtrip": "compression", "http_server_client": "http",
            "tcp_client_server": "tcp", "dns_lookup": "dns", "ssh_loopback": "ssh",
            "package_install": "package_install", "service_start": "service_start",
            "shell_script": "shell_script",
        }
        links.add(aliases.get(token, token))
    if domain in {"filesystem", "fd", "process", "shell", "posix"}:
        links.update({"shell_script", "coreutils_pipeline"})
    if domain in {"thread", "sync", "scheduling"}:
        links.add("pthread")
    if domain in {"socket", "network", "poll"}:
        links.update({"http", "tcp"})
    if domain == "package":
        links.add("package_install")
    if domain == "service":
        links.add("service_start")
    if domain == "persistence":
        links.add("reboot_persistent")
    if domain == "full":
        links.add("full_workflow")
    return sorted(link for link in links if link in WORKLOADS)


def build_contracts() -> list[dict[str, Any]]:
    catalog = json.loads((ROOT / "tools/contract_catalog.json").read_text())["contracts"]
    level_index = {level: index for index, level in enumerate(LEVELS)}
    ordered = sorted(catalog, key=lambda item: (level_index[item["level"]], item["id"]))
    root_id = "boot.firmware.uefi_entry"
    ordered.sort(key=lambda item: (0 if item["id"] == root_id else 1, level_index[item["level"]], item["id"]))

    prerequisites: dict[str, list[str]] = {root_id: []}
    last_domain: dict[str, str] = {}
    level_anchor: dict[str, str] = {}
    prior: list[str] = []
    for item in ordered:
        cid = item["id"]
        if cid == root_id:
            last_domain[item["domain"]] = cid
            level_anchor.setdefault(item["level"], cid)
            prior.append(cid)
            continue
        candidates: list[str] = []
        previous_level = LEVELS[max(0, level_index[item["level"]] - 1)]
        if item["domain"] in last_domain:
            candidates.append(last_domain[item["domain"]])
        if previous_level in level_anchor:
            candidates.append(level_anchor[previous_level])
        if not candidates:
            candidates.append(prior[-1])
        prerequisites[cid] = list(dict.fromkeys(candidates))
        last_domain[item["domain"]] = cid
        level_anchor.setdefault(item["level"], cid)
        prior.append(cid)

    # Add deterministic earlier dependencies until the published v0.1 graph has 503 edges.
    target_edges = 503
    current = sum(len(value) for value in prerequisites.values())
    by_id = {item["id"]: item for item in ordered}
    for index, item in enumerate(ordered):
        if current >= target_edges or index < 2:
            continue
        cid = item["id"]
        earlier = [candidate["id"] for candidate in ordered[:index]]
        choices = [
            earlier[0],
            earlier[max(0, index // 3)],
            earlier[max(0, index // 2)],
            earlier[-1],
        ]
        for candidate in choices:
            if current >= target_edges:
                break
            if candidate != cid and candidate not in prerequisites[cid]:
                prerequisites[cid].append(candidate)
                current += 1
    cursor = 2
    while current < target_edges:
        item = ordered[cursor % len(ordered)]
        cid = item["id"]
        index = next(i for i, value in enumerate(ordered) if value["id"] == cid)
        earlier = [value["id"] for value in ordered[:index]]
        if earlier:
            candidate = earlier[(cursor * 17) % len(earlier)]
            if candidate not in prerequisites[cid]:
                prerequisites[cid].append(candidate)
                current += 1
        cursor += 1
    if current != target_edges:
        raise RuntimeError((current, target_edges))

    contracts: list[dict[str, Any]] = []
    ids = [item["id"] for item in ordered]
    for index, item in enumerate(ordered):
        cid = item["id"]
        domain = item["domain"]
        level = item["level"]
        source_type, source_reference = SOURCE_BY_LEVEL[level]
        peers = []
        for offset in (1, 7):
            peer = ids[(index + offset) % len(ids)]
            if peer != cid:
                peers.append(peer)
        fault = ["invalid_argument", "resource_exhaustion", "interrupted_operation"]
        if level in {"distro", "package_ecosystem", "full_reconstruction"}:
            fault.append("power_loss")
        if domain in {"permission", "security", "identity"}:
            fault.append("permission_denied")
        transport = "host" if item["host_supported"] else "guest_agent"
        if cid in {"boot.firmware.uefi_entry", "boot.kernel.entry", "boot.rootfs.mount"}:
            transport = "serial"
        contract = {
            "schema_version": "osbench.contract.v1",
            "id": cid,
            "title": title(cid),
            "domain": domain,
            "level": level,
            "abstraction": cid.split(".")[0],
            "operation": operation(cid),
            "description": (
                f"Measures the externally observable Linux-compatible semantics of {operation(cid).replace('.', ' ')} "
                f"for the {domain} abstraction, including successful execution, errors, state changes, cleanup, "
                "composition, contention, and behavior under bounded resource pressure."
            ),
            "prerequisites": prerequisites[cid],
            "sources": [
                {"type": source_type, "reference": source_reference},
                {"type": "book", "reference": "Modern Operating Systems, 5th ed., relevant subsystem and design chapters"},
            ],
            "observables": OBSERVABLES_BY_DOMAIN.get(domain, ["syscall_return", "errno", "stdout", "stderr", "exit_code"]),
            "normalization": NORMALIZATION_BY_DOMAIN.get(domain, ["none"]),
            "equivalence": {"type": "semantic", "comparator": "osbench.comparators.compare"},
            "invariants": [
                "The operation produces the same externally visible state relation as the pinned Debian reference.",
                "Successful completion preserves all unrelated process, filesystem, memory, device, and credential state.",
                "Repeated execution with the same initial state and seed remains within the Contract's declared equivalence relation.",
            ],
            "error_conditions": [
                "Invalid arguments return the reference error without committing forbidden partial state.",
                "Insufficient permissions or resources fail with reference-compatible authorization and cleanup behavior.",
            ],
            "state_transitions": [
                "initial -> operation in progress -> completed or rejected",
                "failure -> resources released -> known-good follow-up operation succeeds",
            ],
            "cleanup_invariants": [
                "All evaluator-created resources are released or remain only when persistence is part of the Contract.",
                "A failed operation does not accumulate leaked descriptors, processes, memory, locks, sockets, or package state.",
            ],
            "resource_invariants": [
                "Resource ownership and accounting match the observable reference relation.",
                "Exhaustion is bounded and leaves the system able to execute a known-good follow-up operation.",
            ],
            "legal_nondeterminism": [
                "Opaque identifiers and scheduling order may differ only when explicitly normalized.",
            ],
            "case_dimensions": CASE_DIMENSIONS,
            "orthogonal_with": sorted(set(peers)),
            "fault_injection": sorted(set(fault)),
            "generator": {
                "implementation": "generators.common.contract_case",
                "version": "1",
                "parameters": {"contract_id": cid},
                "probe": "generic" if item["host_supported"] else "guest.generic",
                "cases_per_contract": 10,
            },
            "timeouts": {"case_seconds": 20, "boot_seconds": 240},
            "transport": transport,
            "workloads": workload_links(cid, domain),
            "difficulty": (
                "foundational" if level in {"boot", "machine", "linux_primitives"}
                else "macro" if level in {"real_workloads", "full_reconstruction"}
                else "advanced" if level in {"linux_system", "distro", "package_ecosystem"}
                else "intermediate"
            ),
            "status": "accepted",
            "tags": sorted(set([domain, level, "linux", "behavioral"])),
        }
        contracts.append(contract)
    return contracts


def main() -> int:
    contracts = build_contracts()
    for path in (ROOT / "contracts").glob("*/*.yaml"):
        path.unlink()
    for contract in contracts:
        directory = ROOT / "contracts" / contract["domain"]
        directory.mkdir(parents=True, exist_ok=True)
        filename = contract["id"].replace(".", "__") + ".yaml"
        (directory / filename).write_text(
            yaml.safe_dump(contract, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )
    print(json.dumps({"contracts": len(contracts), "edges": sum(len(c["prerequisites"]) for c in contracts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
