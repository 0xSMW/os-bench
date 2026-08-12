#!/bin/sh
set -eu
ssh -V 2>&1 | head -n1
