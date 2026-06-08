#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo -v
python3 -m macmon.main "$@"
