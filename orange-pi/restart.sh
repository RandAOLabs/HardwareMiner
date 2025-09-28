#!/bin/bash
#
# Restart RNG Miner services
#

set -euo pipefail

INSTALL_DIR="/opt/rng-miner"

echo "🔄 Restarting RNG Miner services..."

"$INSTALL_DIR/stop.sh"
sleep 2
"$INSTALL_DIR/start.sh"

echo "✅ RNG Miner services restarted"