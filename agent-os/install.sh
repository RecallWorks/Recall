#!/usr/bin/env bash
# @recall.works/agent-os | install.sh | v0.1 (placeholder)
#
# A bash equivalent of bootstrap.ps1 is on the v0.2 roadmap. Today this
# script verifies dependencies and prints the manual steps.
#
# Usage:  ./install.sh
#
# The PowerShell scripts in bin/ run on PowerShell 7+ (cross-platform), so
# you can use them directly on Linux/macOS today — install pwsh, ollama, az,
# azcopy, then `pwsh ./bootstrap.ps1`. A native bash variant is coming.

set -euo pipefail

echo "=== Recall · Agent OS install (bash placeholder) ==="

need() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "  MISSING: $1 (install via your package manager and re-run)"
        return 1
    fi
    echo "  ok   $1 -> $(command -v "$1")"
}

missing=0
need pwsh   || missing=$((missing+1))
need ollama || missing=$((missing+1))
need az     || missing=$((missing+1))
need azcopy || missing=$((missing+1))

if [ "$missing" -gt 0 ]; then
    echo
    echo "Install the missing items above, then re-run."
    exit 2
fi

echo
echo "All dependencies present. PowerShell 7 will drive the rest:"
echo "  pwsh ./bootstrap.ps1"
echo
echo "(A native bash bootstrap is on the v0.2 roadmap — same logic, no pwsh needed.)"
