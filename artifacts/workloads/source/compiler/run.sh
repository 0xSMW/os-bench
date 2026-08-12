#!/bin/sh
set -eu
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/main.c" <<'C'
#include <stdio.h>
int main(void){puts("compiler-ok");return 0;}
C
cc "$d/main.c" -o "$d/main"
[ "$($d/main)" = compiler-ok ]
