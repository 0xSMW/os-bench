# Capability coverage

The workload matrix maps each executable workflow to its directly declared Contracts and the complete prerequisite closure in the capability DAG. Syscall counts remain zero until the pinned Debian VM has been built and the workload has been traced with `osbench trace workload <name>`.

| Workload | Declared level | Direct Contracts | DAG closure | Observed syscalls |
|---|---:|---:|---:|---:|
| `compiler` | `real_workloads` | 5 | 21 | 0 |
| `compression` | `real_workloads` | 4 | 21 | 0 |
| `coreutils_pipeline` | `posix_userspace` | 5 | 32 | 0 |
| `dns` | `real_workloads` | 3 | 34 | 0 |
| `dynamic_elf` | `real_workloads` | 4 | 18 | 0 |
| `git` | `real_workloads` | 4 | 39 | 0 |
| `http` | `real_workloads` | 4 | 24 | 0 |
| `package` | `package_ecosystem` | 2 | 31 | 0 |
| `package_install` | `package_ecosystem` | 5 | 47 | 0 |
| `pthread` | `real_workloads` | 5 | 26 | 0 |
| `python` | `real_workloads` | 5 | 47 | 0 |
| `reboot_service` | `full_reconstruction` | 4 | 73 | 0 |
| `service` | `real_workloads` | 4 | 65 | 0 |
| `shell` | `posix_userspace` | 6 | 26 | 0 |
| `sqlite` | `real_workloads` | 6 | 27 | 0 |
| `ssh` | `real_workloads` | 5 | 42 | 0 |
| `static_elf` | `real_workloads` | 4 | 13 | 0 |
| `tcp` | `real_workloads` | 4 | 24 | 0 |

The matrix answers blocking questions mechanically: a workload is blocked when any Contract in its closure fails. `osbench graph workload <name>` returns the closure; `osbench graph blocked <contract>` returns affected workloads; `osbench graph frontier <results.json>` returns the lowest unsatisfied implementation frontier.

### `compiler`

Command: `/bin/sh -c d=$(mktemp -d); printf '#include <stdio.h>\nint main(){puts("ok");}' > "$d/a.c"; cc "$d/a.c" -o "$d/a"; "$d/a"; rm -rf "$d"`

Direct Contracts: `elf.dynamic_loader.basic`, `fs.file.write.basic`, `memory.mmap.file`, `process.execve.basic`, `workload.c.compile_link_run`

Capability closure by level: `boot` 3, `kernel_subsystems` 4, `linux_primitives` 6, `linux_process_environment` 2, `machine` 4, `real_workloads` 2

### `compression`

Command: `/bin/sh -c d=$(mktemp -d); dd if=/dev/urandom of="$d/in" bs=4096 count=4 status=none; gzip -c "$d/in" > "$d/in.gz"; gzip -dc "$d/in.gz" > "$d/out"; cmp "$d/in" "$d/out"; echo compression-ok; rm -rf "$d"`

Direct Contracts: `fs.file.write.basic`, `pipe.basic`, `workload.compression.roundtrip`, `workload.dynamic_elf`

Capability closure by level: `boot` 3, `kernel_subsystems` 4, `linux_primitives` 6, `linux_process_environment` 2, `machine` 4, `real_workloads` 2

### `coreutils_pipeline`

Command: `/bin/sh -c d=$(mktemp -d); printf 'zeta
alpha
beta
alpha
' > "$d/in"; cat "$d/in" | sort | uniq -c | grep alpha; rm -rf "$d"`

Direct Contracts: `posix.utility.cat`, `posix.utility.grep`, `posix.utility.sort`, `shell.pipeline.basic`, `workload.coreutils.pipeline`

Capability closure by level: `boot` 3, `kernel_subsystems` 9, `linux_primitives` 9, `linux_process_environment` 1, `machine` 4, `posix_userspace` 5, `real_workloads` 1

### `dns`

Command: `getent ahostsv4 localhost`

Direct Contracts: `distro.dns.configuration`, `network.dns.resolve`, `workload.dns.lookup`

Capability closure by level: `boot` 5, `distro` 4, `kernel_subsystems` 5, `linux_primitives` 9, `linux_process_environment` 2, `linux_system` 3, `machine` 5, `real_workloads` 1

### `dynamic_elf`

Command: `/var/lib/osbench/workloads/dynamic-elf alpha beta`

Direct Contracts: `elf.argv_env`, `elf.auxv`, `elf.dynamic_loader.basic`, `workload.dynamic_elf`

Capability closure by level: `boot` 3, `kernel_subsystems` 3, `linux_primitives` 5, `linux_process_environment` 2, `machine` 4, `real_workloads` 1

### `git`

Command: `/bin/sh -c d=$(mktemp -d); git init -q "$d"; echo x > "$d/f"; git -C "$d" add f; git -C "$d" status --porcelain; rm -rf "$d"`

Direct Contracts: `fs.directory.create_remove`, `fs.file.rename.atomicity`, `fs.file.write.basic`, `workload.git.repository`

Capability closure by level: `boot` 5, `distro` 3, `kernel_subsystems` 9, `linux_primitives` 12, `linux_process_environment` 2, `machine` 4, `posix_userspace` 2, `real_workloads` 2

### `http`

Command: `python3 /var/lib/osbench/workloads/fixtures/http_loopback.py`

Direct Contracts: `poll.socket.readiness`, `socket.tcp.loopback`, `thread.create_join`, `workload.http.server_client`

Capability closure by level: `boot` 3, `kernel_subsystems` 12, `linux_primitives` 3, `machine` 5, `real_workloads` 1

### `package`

Command: `dpkg-query -W base-files`

Direct Contracts: `package.database.query`, `package.dpkg.status`

Capability closure by level: `boot` 5, `distro` 2, `kernel_subsystems` 7, `linux_primitives` 9, `linux_process_environment` 1, `machine` 4, `package_ecosystem` 2, `posix_userspace` 1

### `package_install`

Command: `dpkg-deb --info /var/lib/osbench/packages/osbench-hello_0.1.0_all.deb`

Direct Contracts: `package.deb.install`, `package.deb.remove`, `package.maintainer.postinst`, `package.maintainer.preinst`, `workload.package.install`

Capability closure by level: `boot` 5, `distro` 4, `kernel_subsystems` 12, `linux_primitives` 11, `linux_process_environment` 2, `linux_system` 1, `machine` 4, `package_ecosystem` 6, `posix_userspace` 1, `real_workloads` 1

### `pthread`

Command: `/var/lib/osbench/workloads/pthread`

Direct Contracts: `sync.futex.wait_wake`, `sync.mutex.exclusion`, `thread.create_join`, `thread.tls`, `workload.pthread.program`

Capability closure by level: `boot` 3, `kernel_subsystems` 8, `linux_primitives` 4, `linux_process_environment` 3, `linux_system` 1, `machine` 6, `real_workloads` 1

### `python`

Command: `python3 -c import os,sqlite3,threading; print(os.getpid(), sqlite3.sqlite_version, threading.active_count())`

Direct Contracts: `elf.dynamic_loader.basic`, `memory.mmap.anonymous`, `procfs.self.status`, `thread.create_join`, `workload.python.basic`

Capability closure by level: `boot` 5, `distro` 3, `kernel_subsystems` 14, `linux_primitives` 11, `linux_process_environment` 3, `linux_system` 2, `machine` 6, `posix_userspace` 2, `real_workloads` 1

### `reboot_service`

Command: `/bin/true`

Direct Contracts: `full.install_serve_reboot`, `package.deb.install`, `persistence.service.reboot`, `service.enable.start`

Capability closure by level: `boot` 7, `distro` 11, `full_reconstruction` 1, `kernel_subsystems` 25, `linux_primitives` 11, `linux_process_environment` 2, `linux_system` 1, `machine` 6, `package_ecosystem` 6, `posix_userspace` 1, `real_workloads` 2

### `service`

Command: `systemctl cat osbench-agent.service`

Direct Contracts: `package.service.install`, `service.enable.start`, `service.lifecycle.start_stop`, `workload.service.start`

Capability closure by level: `boot` 5, `distro` 7, `kernel_subsystems` 24, `linux_primitives` 11, `linux_process_environment` 2, `linux_system` 1, `machine` 6, `package_ecosystem` 6, `posix_userspace` 1, `real_workloads` 2

### `shell`

Command: `/bin/sh -c printf 'z\na\n' | sort | head -n 1`

Direct Contracts: `fd.dup2.redirection`, `pipe.basic`, `process.execve.basic`, `process.fork.basic`, `process.wait.basic`, `shell.pipeline.basic`

Capability closure by level: `boot` 3, `kernel_subsystems` 9, `linux_primitives` 7, `linux_process_environment` 1, `machine` 4, `posix_userspace` 2

### `sqlite`

Command: `python3 -c import sqlite3,tempfile,os; p=tempfile.mktemp(); c=sqlite3.connect(p); c.execute('create table t(x)'); c.execute('insert into t values (1)'); c.commit(); print(c.execute('select x from t').fetchone()[0]); c.close(); os.unlink(p)`

Direct Contracts: `fs.file.fsync`, `fs.file.open`, `fs.file.rename.atomicity`, `fs.file.write.basic`, `memory.mmap.file`, `workload.sqlite.transaction`

Capability closure by level: `boot` 3, `kernel_subsystems` 9, `linux_primitives` 7, `linux_system` 1, `machine` 6, `real_workloads` 1

### `ssh`

Command: `/var/lib/osbench/workloads/fixtures/ssh_loopback.sh`

Direct Contracts: `permission.setuid_transition`, `service.lifecycle.start_stop`, `socket.tcp.stream_semantics`, `tty.pty`, `workload.ssh.loopback`

Capability closure by level: `boot` 5, `distro` 3, `kernel_subsystems` 14, `linux_primitives` 9, `linux_process_environment` 2, `linux_system` 2, `machine` 6, `real_workloads` 1

### `static_elf`

Command: `/var/lib/osbench/workloads/static-elf`

Direct Contracts: `elf.static.load`, `fs.file.write.basic`, `process.execution`, `workload.static_elf`

Capability closure by level: `boot` 3, `linux_primitives` 5, `machine` 4, `real_workloads` 1

### `tcp`

Command: `python3 /var/lib/osbench/workloads/fixtures/tcp_loopback.py`

Direct Contracts: `poll.socket.readiness`, `process.fork.basic`, `socket.tcp.stream_semantics`, `workload.tcp.client_server`

Capability closure by level: `boot` 3, `kernel_subsystems` 12, `linux_primitives` 3, `machine` 5, `real_workloads` 1
