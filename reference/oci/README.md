# OCI representation

`osbench reference export-oci` exports the pinned VM root filesystem and creates
an OCI image layout plus archive. This representation is useful for userspace and
distro inspection. It shares the host/Docker VM kernel and cannot grade kernel
semantics.
