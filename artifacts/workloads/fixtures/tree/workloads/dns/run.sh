#!/bin/sh
set -eu
getent ahostsv4 localhost | grep -q '127.0.0.1'
