#!/usr/bin/env bash
# Run ONCE as root on a fresh Ubuntu 24.04 droplet:
#   curl -fsSL https://raw.githubusercontent.com/itskaysyoga-gif/pumpfun/main/deploy/bootstrap_root.sh -o bootstrap_root.sh
#   less bootstrap_root.sh      # read it first
#   bash bootstrap_root.sh
#
# What it does: updates the OS, turns on automatic security updates, firewall,
# fail2ban, a 4 GB swap file, creates the non-root user `pumplab` with your SSH
# key, and lets pumplab's services keep running after logout.
# It does NOT disable root login. You do that yourself after testing (guide step 6).
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y upgrade
apt-get -y install git tmux curl ufw fail2ban unattended-upgrades htop jq

# Automatic security updates
dpkg-reconfigure -f noninteractive unattended-upgrades

# Firewall: SSH only
ufw allow OpenSSH
ufw --force enable

# fail2ban with default sshd jail
systemctl enable --now fail2ban

# 4 GB swap (Claude Code + DuckDB on a 4 GB droplet need headroom)
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=10
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-swappiness.conf
fi

# Non-root user with root's SSH key. No sudo: Claude Code runs as this user.
if ! id pumplab >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" pumplab
fi
install -d -m 700 -o pumplab -g pumplab /home/pumplab/.ssh
install -m 600 -o pumplab -g pumplab /root/.ssh/authorized_keys /home/pumplab/.ssh/authorized_keys

# Let pumplab's systemd --user services run without an open login
loginctl enable-linger pumplab

timedatectl set-timezone UTC

echo
echo "Done. Next: open a NEW terminal on your Mac and test:  ssh pumplab@$(curl -s ifconfig.me)"
echo "Keep this root session open until that works."
