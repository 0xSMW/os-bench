#!/usr/bin/env bash
set -euo pipefail
osbench reference preflight
osbench payload build
osbench reference build
osbench reference boot
osbench reference inventory
osbench reference export-oci
osbench reference calibrate-unsynced --trials 20
osbench reference lock-realize
osbench reference preflight --verify-hashes --strict
