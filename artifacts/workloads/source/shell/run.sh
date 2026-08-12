#!/bin/sh
set -eu
result=$(printf 'zeta\nalpha\nbeta\nalpha\n' | sort | uniq -c | grep alpha)
case "$result" in *2*alpha*) ;; *) exit 1;; esac
