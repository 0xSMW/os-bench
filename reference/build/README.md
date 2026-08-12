# Reference builder

The builder verifies the Debian 13.6.0 amd64 DVD-1 source against both Debian's
signed checksum file and the immutable digest in `reference/lock.json`, injects
an unattended preseed plus the serial evaluator agent, creates an 8 GiB QCOW2
image, installs under Q35/OVMF, and exports a normalized rootfs tar for OCI use.

Commands:

```bash
reference/build/download_iso.sh
reference/build/prepare_installer.sh
reference/build/build_image.sh
reference/build/export_rootfs.sh
```
