from __future__ import annotations

import copy
import re
from typing import Any


_PID_KEYS = {
    "pid",
    "process_id",
    "child_pid",
    "parent_pid",
    "child",
    "parent",
    "creator_pid",
    "target_pid",
}
_PPID_KEYS = {"ppid", "parent_process_id"}
_TID_KEYS = {"tid", "thread_id", "thread"}
_INODE_KEYS = {"inode", "ino", "st_ino", "inode_number"}
_PORT_KEYS = {"port", "local_port", "remote_port", "ephemeral_port"}
_HOST_KEYS = {"hostname", "kernel", "kernel_release", "platform", "machine", "nodename"}


def normalize_observation(
    observation: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    """Normalize only nondeterminism declared by a Contract.

    Probe execution time is transport metadata rather than an OS semantic unless the
    Contract explicitly observes timing or resource use. It is removed consistently,
    including from Contracts that otherwise request ``none`` normalization.
    """

    value = copy.deepcopy(observation)
    observables = set(contract.get("observables", []))
    if "timing" not in observables and "resource_usage" not in observables:
        value.pop("duration_ns", None)

    rules = {rule for rule in contract.get("normalization", []) if rule != "none"}
    if not rules:
        return value

    def walk(item: Any) -> Any:
        if isinstance(item, dict):
            out: dict[str, Any] = {}
            for key, raw in item.items():
                lower = key.lower()
                if "pid" in rules and (lower in _PID_KEYS or lower.endswith("_pid")):
                    out[key] = "<PID>"
                elif "ppid" in rules and lower in _PPID_KEYS:
                    out[key] = "<PPID>"
                elif "tid" in rules and (lower in _TID_KEYS or lower.endswith("_tid")):
                    out[key] = "<TID>"
                elif "inode" in rules and lower in _INODE_KEYS:
                    out[key] = "<INODE>"
                elif "timestamps" in rules and (
                    "timestamp" in lower
                    or lower.endswith("_time")
                    or lower.endswith("_time_ns")
                    or lower in {"atime", "mtime", "ctime", "btime"}
                ):
                    out[key] = "<TIME>"
                elif "ephemeral_port" in rules and lower in _PORT_KEYS:
                    out[key] = "<PORT>"
                elif "addresses" in rules and (
                    "address" in lower or lower in {"addr", "pointer", "ptr"}
                ):
                    out[key] = "<ADDRESS>"
                elif "host_metadata" in rules and lower in _HOST_KEYS:
                    out[key] = "<HOST>"
                else:
                    out[key] = walk(raw)

            if "directory_order" in rules:
                for key, raw in list(out.items()):
                    if key in {"entries", "directory_entries"} and isinstance(raw, list):
                        out[key] = sorted(raw, key=lambda value: repr(value))
            if "scheduler_order" in rules:
                for key, raw in list(out.items()):
                    if key in {"events", "schedule", "thread_order"} and isinstance(raw, list):
                        out[key] = sorted(raw, key=lambda value: repr(value))
            return out

        if isinstance(item, list):
            return [walk(value) for value in item]
        if isinstance(item, str) and "temporary_paths" in rules:
            item = re.sub(r"/tmp/osbench-[A-Za-z0-9_.-]+", "/tmp/<OSBENCH>", item)
            item = re.sub(r"/tmp/tmp[A-Za-z0-9_.-]+", "/tmp/<TMP>", item)
        return item

    return walk(value)
