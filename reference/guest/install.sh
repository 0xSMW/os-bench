#!/bin/sh
set -eu
SOURCE=${1:-/cdrom/osbench}
install -d -m 0755 /usr/local/lib/osbench /usr/local/share/osbench/packages /var/lib/osbench/state
install -m 0755 "$SOURCE/osbench_agent.py" /usr/local/lib/osbench/osbench_agent.py
install -m 0755 "$SOURCE/osbench-inventory.sh" /usr/local/lib/osbench/osbench-inventory.sh
install -m 0644 "$SOURCE/osbench-agent.service" /etc/systemd/system/osbench-agent.service
if [ -d "$SOURCE/packages" ]; then
  cp -a "$SOURCE/packages/." /usr/local/share/osbench/packages/
fi
systemctl enable osbench-agent.service
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/osbench.conf <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF
