#!/bin/sh
set -eu
systemctl start osbench-workload.service
[ "$(cat /var/lib/osbench/service-state)" = service-ok ]
printf '{"workload":"service","status":"ok"}\n'
