#!/bin/bash
# ============================================================
# ISO 27001 Annex A.8 - System Configuration Collector
# ============================================================
# Run this script on the target Ubuntu server to collect
# system configuration for audit evaluation.
#
# Prerequisites:
#   - Ansible must be installed: sudo apt install ansible
#   - Run with sudo or as root
#
# Usage:
#   chmod +x collect.sh
#   sudo ./collect.sh
#
# Output:
#   system_config.json in the current directory
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo " ISO 27001 A.8 Configuration Collector"
echo "============================================"
echo ""

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "[ERROR] Ansible is not installed."
    echo "Install it with: sudo apt install ansible"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[WARNING] Not running as root. Some checks may fail."
    echo "Consider running with: sudo ./collect.sh"
    echo ""
fi

echo "[*] Running configuration collector playbook..."
echo ""

ansible-playbook \
    -i "localhost," \
    -c local \
    "$SCRIPT_DIR/collector.yml" \
    -e "output_dir=$(pwd)"

echo ""
echo "============================================"
echo " Collection Complete!"
echo "============================================"
echo " Output: $(pwd)/system_config.json"
echo ""
echo " Upload this file to the ISO 27001 Audit App"
echo " for evaluation."
echo "============================================"
